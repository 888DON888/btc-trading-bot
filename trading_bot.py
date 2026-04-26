import os, requests, time, logging, hashlib, hmac, math, json
from datetime import datetime, timezone

C = {
    "PAPER": os.getenv("PAPER_TRADING","true").lower()=="true",
    "KEY":   os.getenv("BYBIT_API_KEY",""),
    "SEC":   os.getenv("BYBIT_API_SECRET",""),
    "SYM":   os.getenv("SYMBOL","BTCUSDT"),
    "AMT":   float(os.getenv("TRADE_USDT","50")),
    "TP":    float(os.getenv("TAKE_PROFIT_PCT","2.5")),
    "SL":    float(os.getenv("STOP_LOSS_PCT","1.5")),
    "TRS":   float(os.getenv("TRAILING_START","1.5")),
    "TRD":   float(os.getenv("TRAILING_STEP","0.3")),
    "HRS":   list(range(1,9)),
    "RSI_OV":float(os.getenv("RSI_OVERSOLD","42")),
    "RSI_P": 14, "BB_P":20, "BB_S":2.0, "EMA_S":200,
    "VMUL":  float(os.getenv("VOLUME_MULT","1.3")),
    "DL":    float(os.getenv("MAX_DAILY_LOSS_PCT","5.0")),
    "CD":    int(os.getenv("COOLDOWN_MINUTES","30")),
    "TGT":   os.getenv("TG_TOKEN",""),
    "TGC":   os.getenv("TG_CHAT_ID",""),
    "INT":   int(os.getenv("CHECK_INTERVAL","60")),
}
BASE = "https://api.bybit.com"
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("BOT")

def tg(txt):
    if not C["TGT"] or not C["TGC"]: return
    try: requests.post(f"https://api.telegram.org/bot{C['TGT']}/sendMessage",json={"chat_id":C["TGC"],"text":txt},timeout=5)
    except Exception as e: log.warning(f"TG:{e}")

def get_price():
    r=requests.get(f"{BASE}/v5/market/tickers",params={"category":"spot","symbol":C["SYM"]},timeout=10)
    r.raise_for_status()
    return float(r.json()["result"]["list"][0]["lastPrice"])

def get_klines():
    r=requests.get(f"{BASE}/v5/market/kline",params={"category":"spot","symbol":C["SYM"],"interval":"60","limit":220},timeout=10)
    r.raise_for_status()
    raw=list(reversed(r.json()["result"]["list"]))
    return [float(k[4]) for k in raw],[float(k[5]) for k in raw]

def ema(p,n):
    k=2/(n+1); res=[None]*len(p)
    if len(p)<n: return res
    res[n-1]=sum(p[:n])/n
    for i in range(n,len(p)): res[i]=p[i]*k+res[i-1]*(1-k)
    return res

def rsi(c,n=14):
    res=[None]*len(c)
    if len(c)<n+1: return res
    g=[max(c[i]-c[i-1],0) for i in range(1,n+1)]
    l=[max(c[i-1]-c[i],0) for i in range(1,n+1)]
    ag,al=sum(g)/n,sum(l)/n
    for i in range(n,len(c)):
        if i>n:
            d=c[i]-c[i-1]; ag=(ag*(n-1)+max(d,0))/n; al=(al*(n-1)+max(-d,0))/n
        res[i]=100-100/(1+ag/al) if al else 100
    return res

def bbands(c,n=20,s=2.0):
    lo=[None]*len(c)
    for i in range(n-1,len(c)):
        w=c[i-n+1:i+1]; m=sum(w)/n; std=(sum((x-m)**2 for x in w)/n)**.5
        lo[i]=m-s*std
    return lo

class Paper:
    def __init__(self): self.bal=1000.0; self.tr=[]
    def buy(self,p,q):
        c=p*q
        if c>self.bal: q=self.bal/p*.999; c=p*q
        self.bal-=c; return q
    def sell(self,p,q,ep,reason):
        pnl=(p-ep)/ep*100; self.bal+=p*q
        self.tr.append({"pnl":round(pnl,3),"r":reason}); return pnl
    def stats(self):
        if not self.tr: return "No trades"
        w=[t for t in self.tr if t["pnl"]>0]; wr=len(w)/len(self.tr)*100
        return f"Trades:{len(self.tr)} Win:{wr:.0f}% Bal:{self.bal:.2f}$"

class Bot:
    def __init__(self):
        self.paper=Paper() if C["PAPER"] else None
        self.pos=None; self.dpnl=0.0; self.lstop=None; self.stopped=False
        self._day=datetime.now(timezone.utc).day
        mode="PAPER" if C["PAPER"] else "LIVE"
        log.info(f"BOT STARTED | {mode} | {C['SYM']} | Bybit | TP:{C['TP']}% SL:{C['SL']}%")
        tg(f"Bot started | {mode} | {C['SYM']} | Bybit")

    def signals(self,closes,vols):
        rv=rsi(closes,C["RSI_P"]); es=ema(closes,C["EMA_S"]); bl=bbands(closes,C["BB_P"],C["BB_S"])
        av=sum(vols[-21:-1])/20 if len(vols)>=21 else 0
        p=closes[-1]; score=0; h=datetime.now(timezone.utc).hour
        if h in C["HRS"]: score+=1
        if es[-1] and p>es[-1]: score+=1
        if rv[-1] and rv[-1]<C["RSI_OV"]: score+=1
        if bl[-1] and p<=bl[-1]*1.005: score+=1
        if av and vols[-1]>av*C["VMUL"]: score+=1
        return score>=4,score,rv[-1],es[-1]

    def open(self,price,score,rsi_v):
        qty=math.floor((C["AMT"]/price)*100000)/100000
        if qty<=0: return
        sl=price*(1-C["SL"]/100); tp=price*(1+C["TP"]/100)
        if C["PAPER"]: qty=self.paper.buy(price,qty)
        self.pos={"qty":qty,"ep":price,"high":price,"sl":sl,"tp":tp,"trail":None,"t":datetime.now(timezone.utc)}
        msg=f"BUY {C['SYM']} @ {price:.2f}\nTP:{tp:.2f} SL:{sl:.2f}\nRSI:{rsi_v:.1f} Signals:{score}/5"
        log.info(msg.replace(chr(10)," | ")); tg(msg)

    def close(self,price,reason):
        if not self.pos: return
        qty=self.pos["qty"]
        pnl=self.paper.sell(price,qty,self.pos["ep"],reason) if C["PAPER"] else (price-self.pos["ep"])/self.pos["ep"]*100
        self.dpnl+=pnl
        if pnl<0: self.lstop=datetime.now(timezone.utc)
        ok="PROFIT" if pnl>0 else "LOSS"
        msg=f"{ok} {reason} @ {price:.2f} PnL:{pnl:+.2f}% Daily:{self.dpnl:+.2f}%"
        if C["PAPER"]: msg+=f"\n{self.paper.stats()}"
        log.info(msg.replace(chr(10)," | ")); tg(msg); self.pos=None

    def manage(self,price):
        p=self.pos
        if not p: return
        if price>p["high"]: p["high"]=price
        pnl=(price-p["ep"])/p["ep"]*100
        if price>=p["tp"]: self.close(price,"TAKE_PROFIT"); return
        if price<=p["sl"]: self.close(price,"STOP_LOSS"); return
        if pnl>=C["TRS"]:
            t=p["high"]*(1-C["TRD"]/100)
            if not p["trail"] or t>p["trail"]: p["trail"]=t; p["sl"]=t
            if price<=p["trail"]: self.close(price,"TRAILING"); return
        if (datetime.now(timezone.utc)-p["t"]).total_seconds()/3600>=22 and pnl>0.3:
            self.close(price,"TIME_EXIT")

    def risk_ok(self):
        if self.dpnl<=-C["DL"]:
            if not self.stopped: self.stopped=True; tg(f"Daily limit {self.dpnl:.2f}%")
            return False
        if self.lstop and (datetime.now(timezone.utc)-self.lstop).total_seconds()/60<C["CD"]: return False
        return True

    def run(self):
        log.info("Running. Ctrl+C to stop."); n=0
        while True:
            try:
                today=datetime.now(timezone.utc).day
                if today!=self._day: self.dpnl=0.0; self.stopped=False; self._day=today
                n+=1
                try: price=get_price()
                except Exception as e: log.error(f"Price:{e}"); time.sleep(30); continue
                if self.pos: self.manage(price)
                if not self.pos and self.risk_ok():
                    try:
                        closes,vols=get_klines()
                        enter,score,rv,es=self.signals(closes,vols)
                        if n%10==0:
                            log.info(f"Price:{price:.2f} RSI:{rv:.1f if rv else 'N/A'} EMA200:{es:.0f if es else 'N/A'} Sig:{score}/5 H:{datetime.now(timezone.utc).hour:02d}UTC")
                            if C["PAPER"]: log.info(self.paper.stats())
                        if enter: log.info(f"SIGNAL {score}/5"); self.open(price,score,rv or 0)
                    except Exception as e: log.error(f"Indicators:{e}")
                time.sleep(C["INT"])
            except KeyboardInterrupt:
                if C["PAPER"]: log.info(self.paper.stats())
                break
            except Exception as e: log.error(f"Error:{e}"); time.sleep(60)

if __name__=="__main__":
    Bot().run()
