import os
import requests
import time
import logging
import hashlib
import hmac
import math
from datetime import datetime, timezone
from urllib.parse import urlencode

CONFIG = {
    "PAPER_TRADING":      os.getenv("PAPER_TRADING", "true").lower() == "true",
    "API_KEY":            os.getenv("BINANCE_API_KEY", ""),
    "API_SECRET":         os.getenv("BINANCE_API_SECRET", ""),
    "SYMBOL":             os.getenv("SYMBOL", "BTCUSDT"),
    "TRADE_USDT":         float(os.getenv("TRADE_USDT", "50")),
    "TAKE_PROFIT_PCT":    float(os.getenv("TAKE_PROFIT_PCT", "2.5")),
    "STOP_LOSS_PCT":      float(os.getenv("STOP_LOSS_PCT", "1.5")),
    "TRAILING_START":     float(os.getenv("TRAILING_START", "1.5")),
    "TRAILING_STEP":      float(os.getenv("TRAILING_STEP", "0.3")),
    "ENTRY_HOURS_UTC":    list(range(1, 9)),
    "RSI_OVERSOLD":       float(os.getenv("RSI_OVERSOLD", "42")),
    "RSI_PERIOD":         14,
    "BB_PERIOD":          20,
    "BB_STD":             2.0,
    "EMA_FAST":           50,
    "EMA_SLOW":           200,
    "VOLUME_MULT":        float(os.getenv("VOLUME_MULT", "1.3")),
    "MAX_DAILY_LOSS_PCT": float(os.getenv("MAX_DAILY_LOSS_PCT", "5.0")),
    "COOLDOWN_MINUTES":   int(os.getenv("COOLDOWN_MINUTES", "30")),
    "TG_TOKEN":           os.getenv("TG_TOKEN", ""),
    "TG_CHAT_ID":         os.getenv("TG_CHAT_ID", ""),
    "CHECK_INTERVAL":     int(os.getenv("CHECK_INTERVAL", "60")),
    "KLINE_INTERVAL":     "1h",
    "KLINE_LIMIT":        250,
}

BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("BOT")

class BinanceAPI:
    def __init__(self, k="", s=""):
        self.key=k; self.secret=s
        self.session=requests.Session()
        self.session.headers.update({"X-MBX-APIKEY":self.key})
    def _sign(self,p):
        p["timestamp"]=int(time.time()*1000)
        q=urlencode(p)
        p["signature"]=hmac.new(self.secret.encode(),q.encode(),hashlib.sha256).hexdigest()
        return p
    def get(self,path,params=None,signed=False):
        if params is None: params={}
        if signed: params=self._sign(params)
        r=self.session.get(BASE_URL+path,params=params,timeout=10); r.raise_for_status(); return r.json()
    def post(self,path,params=None):
        if params is None: params={}
        params=self._sign(params)
        r=self.session.post(BASE_URL+path,params=params,timeout=10); r.raise_for_status(); return r.json()
    def klines(self,symbol,interval,limit=250):
        return self.get("/api/v3/klines",{"symbol":symbol,"interval":interval,"limit":limit})
    def ticker_price(self,symbol):
        return float(self.get("/api/v3/ticker/price",{"symbol":symbol})["price"])
    def place_order(self,symbol,side,qty):
        return self.post("/api/v3/order",{"symbol":symbol,"side":side,"type":"MARKET","quantity":qty})

def ema(prices,period):
    k=2/(period+1); result=[None]*len(prices)
    if len(prices)<period: return result
    result[period-1]=sum(prices[:period])/period
    for i in range(period,len(prices)): result[i]=prices[i]*k+result[i-1]*(1-k)
    return result

def rsi(closes,period=14):
    result=[None]*len(closes)
    if len(closes)<period+1: return result
import os
import requests
import time
import logging
import hashlib
import hmac
import math
from datetime import datetime, timezone
from urllib.parse import urlencode

CONFIG = {
    "PAPER_TRADING":      os.getenv("PAPER_TRADING", "true").lower() == "true",
    "API_KEY":            os.getenv("BINANCE_API_KEY", ""),
    "API_SECRET":         os.getenv("BINANCE_API_SECRET", ""),
    "SYMBOL":             os.getenv("SYMBOL", "BTCUSDT"),
    "TRADE_USDT":         float(os.getenv("TRADE_USDT", "50")),
    "TAKE_PROFIT_PCT":    float(os.getenv("TAKE_PROFIT_PCT", "2.5")),
    "STOP_LOSS_PCT":      float(os.getenv("STOP_LOSS_PCT", "1.5")),
    "TRAILING_START":     float(os.getenv("TRAILING_START", "1.5")),
    "TRAILING_STEP":      float(os.getenv("TRAILING_STEP", "0.3")),
    "ENTRY_HOURS_UTC":    list(range(1, 9)),
    "RSI_OVERSOLD":       float(os.getenv("RSI_OVERSOLD", "42")),
    "RSI_PERIOD":         14,
    "BB_PERIOD":          20,
    "BB_STD":             2.0,
    "EMA_FAST":           50,
    "EMA_SLOW":           200,
    "VOLUME_MULT":        float(os.getenv("VOLUME_MULT", "1.3")),
    "MAX_DAILY_LOSS_PCT": float(os.getenv("MAX_DAILY_LOSS_PCT", "5.0")),
    "COOLDOWN_MINUTES":   int(os.getenv("COOLDOWN_MINUTES", "30")),
    "TG_TOKEN":           os.getenv("TG_TOKEN", ""),
    "TG_CHAT_ID":         os.getenv("TG_CHAT_ID", ""),
    "CHECK_INTERVAL":     int(os.getenv("CHECK_INTERVAL", "60")),
    "KLINE_INTERVAL":     "1h",
    "KLINE_LIMIT":        250,
}

BASE_URL = "https://api.binance.com"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("BOT")

class BinanceAPI:
    def __init__(self, k="", s=""):
        self.key=k; self.secret=s
        self.session=requests.Session()
        self.session.headers.update({"X-MBX-APIKEY":self.key})
    def _sign(self,p):
        p["timestamp"]=int(time.time()*1000)
        q=urlencode(p)
        p["signature"]=hmac.new(self.secret.encode(),q.encode(),hashlib.sha256).hexdigest()
        return p
    def get(self,path,params=None,signed=False):
        if params is None: params={}
        if signed: params=self._sign(params)
        r=self.session.get(BASE_URL+path,params=params,timeout=10); r.raise_for_status(); return r.json()
    def post(self,path,params=None):
        if params is None: params={}
        params=self._sign(params)
        r=self.session.post(BASE_URL+path,params=params,timeout=10); r.raise_for_status(); return r.json()
    def klines(self,symbol,interval,limit=250):
        return self.get("/api/v3/klines",{"symbol":symbol,"interval":interval,"limit":limit})
    def ticker_price(self,symbol):
        return float(self.get("/api/v3/ticker/price",{"symbol":symbol})["price"])
    def place_order(self,symbol,side,qty):
        return self.post("/api/v3/order",{"symbol":symbol,"side":side,"type":"MARKET","quantity":qty})

def ema(prices,period):
    k=2/(period+1); result=[None]*len(prices)
    if len(prices)<period: return result
    result[period-1]=sum(prices[:period])/period
    for i in range(period,len(prices)): result[i]=prices[i]*k+result[i-1]*(1-k)
    return result

def rsi(closes,period=14):
    result=[None]*len(closes)
    if len(closes)<period+1: return result
    gains,losses=[],[]
    for i in range(1,period+1):
        d=closes[i]-closes[i-1]; gains.append(max(d,0)); losses.append(max(-d,0))
    ag=sum(gains)/period; al=sum(losses)/period
    for i in range(period,len(closes)):
        if i>period:
            d=closes[i]-closes[i-1]; ag=(ag*(period-1)+max(d,0))/period; al=(al*(period-1)+max(-d,0))/period
        rs=ag/al if al!=0 else float("inf"); result[i]=100-100/(1+rs)
    return result

def bollinger(closes,period=20,std_mult=2.0):
    upper,middle,lower=[None]*len(closes),[None]*len(closes),[None]*len(closes)
    for i in range(period-1,len(closes)):
        w=closes[i-period+1:i+1]; sma=sum(w)/period
        std=(sum((x-sma)**2 for x in w)/period)**0.5
        middle[i]=sma; upper[i]=sma+std_mult*std; lower[i]=sma-std_mult*std
    return upper,middle,lower

def send_tg(text):
    t=CONFIG["TG_TOKEN"]; c=CONFIG["TG_CHAT_ID"]
    if not t or not c: return
    try: requests.post(f"https://api.telegram.org/bot{t}/sendMessage",json={"chat_id":c,"text":text,"parse_mode":"HTML"},timeout=5)
    except Exception as e: log.warning(f"TG error:{e}")

class PaperAccount:
    def __init__(self,usdt=1000.0): self.usdt=usdt; self.trades=[]
    def buy(self,price,qty):
        cost=price*qty
        if cost>self.usdt: qty=self.usdt/price*0.999; cost=price*qty
        self.usdt-=cost; return {"qty":qty,"price":price}
    def sell(self,price,qty,entry,reason):
        pnl=(price-entry)/entry*100; self.usdt+=price*qty
        self.trades.append({"pnl":round(pnl,3),"reason":reason}); return pnl
    def stats(self): 
        if not self.trades: return "No trades"
        wins=[t for t in self.trades if t["pnl"]>0]; wr=len(wins)/len(self.trades)*100
        return f"Trades:{len(self.trades)} Win:{wr:.0f}% Balance:{self.usdt:.2f}$"

class TradingBot:
    def __init__(self):
        self.cfg=CONFIG; self.api=BinanceAPI(self.cfg["API_KEY"],self.cfg["API_SECRET"])
        self.paper=PaperAccount(1000.0) if self.cfg["PAPER_TRADING"] else None
        self.position=None; self.daily_pnl=0.0; self.last_stop=None; self.stopped=False
        self._day=datetime.now(timezone.utc).day
        mode="PAPER" if self.cfg["PAPER_TRADING"] else "LIVE"
        log.info(f"BOT STARTED | {mode} | {self.cfg['SYMBOL']} | TP:{self.cfg['TAKE_PROFIT_PCT']}% SL:{self.cfg['STOP_LOSS_PCT']}%")
        send_tg(f"Bot started | {mode} | {self.cfg['SYMBOL']}")
    def indicators(self):
        try: raw=self.api.klines(self.cfg["SYMBOL"],self.cfg["KLINE_INTERVAL"],self.cfg["KLINE_LIMIT"])
        except Exception as e: log.error(e); return None
        c=[float(k[4]) for k in raw]; v=[float(k[5]) for k in raw]
        rv=rsi(c,self.cfg["RSI_PERIOD"]); ef=ema(c,self.cfg["EMA_FAST"]); es=ema(c,self.cfg["EMA_SLOW"])
        bu,_,bl=bollinger(c,self.cfg["BB_PERIOD"],self.cfg["BB_STD"])
        av=sum(v[-21:-1])/20 if len(v)>=21 else 0
        return {"price":c[-1],"rsi":rv[-1],"ema_fast":ef[-1],"ema_slow":es[-1],"bb_upper":bu[-1],"bb_lower":bl[-1],"volume":v[-1],"avg_vol":av}
    def signals(self,ind):
        s=0; h=datetime.now(timezone.utc).hour
        if h in self.cfg["ENTRY_HOURS_UTC"]: s+=1
        if ind["ema_slow"] and ind["price"]>ind["ema_slow"]: s+=1
        if ind["rsi"] and ind["rsi"]<self.cfg["RSI_OVERSOLD"]: s+=1
        if ind["bb_lower"] and ind["price"]<=ind["bb_lower"]*1.005: s+=1
        if ind["avg_vol"] and ind["volume"]>ind["avg_vol"]*self.cfg["VOLUME_MULT"]: s+=1
        return s>=4,s
    def open_pos(self,price,ind):
        qty=math.floor((self.cfg["TRADE_USDT"]/price)*100000)/100000
        if qty<=0: return
        sl=price*(1-self.cfg["STOP_LOSS_PCT"]/100); tp=price*(1+self.cfg["TAKE_PROFIT_PCT"]/100)
        if self.cfg["PAPER_TRADING"]: r=self.paper.buy(price,qty); qty=r["qty"]
        else:
            try: self.api.place_order(self.cfg["SYMBOL"],"BUY",qty)
            except Exception as e: log.error(e); return
        self.position={"qty":qty,"entry":price,"high":price,"sl":sl,"tp":tp,"trail":None,"time":datetime.now(timezone.utc)}
        msg=f"BUY {self.cfg['SYMBOL']} @ {price:.2f} | TP:{tp:.2f} SL:{sl:.2f} | RSI:{ind['rsi']:.1f}"
        log.info(msg); send_tg(msg)
    def close_pos(self,price,reason):
        if not self.position: return
        qty=self.position["qty"]
        if self.cfg["PAPER_TRADING"]: pnl=self.paper.sell(price,qty,self.position["entry"],reason)
        else:
            try: self.api.place_order(self.cfg["SYMBOL"],"SELL",qty)
            except Exception as e: log.error(e); return
            pnl=(price-self.position["entry"])/self.position["entry"]*100
        self.daily_pnl+=pnl
        if pnl<0: self.last_stop=datetime.now(timezone.utc)
        msg=f"{'PROFIT' if pnl>0 else 'LOSS'} {reason} @ {price:.2f} PnL:{pnl:+.2f}% Daily:{self.daily_pnl:+.2f}%"
        log.info(msg); send_tg(msg)
        if self.cfg["PAPER_TRADING"]: send_tg(self.paper.stats())
        self.position=None
    def manage(self,price):
        p=self.position
        if not p: return
        if price>p["high"]: p["high"]=price
        pnl=(price-p["entry"])/p["entry"]*100
        if price>=p["tp"]: self.close_pos(price,"TAKE_PROFIT"); return
        if price<=p["sl"]: self.close_pos(price,"STOP_LOSS"); return
        if pnl>=self.cfg["TRAILING_START"]:
            t=p["high"]*(1-self.cfg["TRAILING_STEP"]/100)
            if p["trail"] is None or t>p["trail"]: p["trail"]=t; p["sl"]=t
            if price<=p["trail"]: self.close_pos(price,"TRAILING"); return
        elapsed=(datetime.now(timezone.utc)-p["time"]).total_seconds()/3600
        if elapsed>=22 and pnl>0.3: self.close_pos(price,"TIME_EXIT")
    def risk_ok(self):
        if self.daily_pnl<=-self.cfg["MAX_DAILY_LOSS_PCT"]:
            if not self.stopped: self.stopped=True; send_tg(f"DAILY LIMIT {self.daily_pnl:.2f}%")
            return False
        if self.last_stop:
            if (datetime.now(timezone.utc)-self.last_stop).total_seconds()/60<self.cfg["COOLDOWN_MINUTES"]: return False
        return True
    def run(self):
        log.info("Running. Ctrl+C to stop."); n=0
        while True:
            try:
                today=datetime.now(timezone.utc).day
                if today!=self._day: self.daily_pnl=0.0; self.stopped=False; self._day=today
                n+=1
                try: price=self.api.ticker_price(self.cfg["SYMBOL"])
                except Exception as e: log.error(e); time.sleep(30); continue
                if self.position: self.manage(price)
                if not self.position and self.risk_ok():
                    ind=self.indicators()
                    if ind:
                        enter,score=self.signals(ind)
                        if n%10==0:
                            log.info(f"Price:{price:.2f} RSI:{ind['rsi']:.1f if ind['rsi'] else 'N/A'} Signals:{score}/5 Hour:{datetime.now(timezone.utc).hour:02d}UTC")
                            if self.cfg["PAPER_TRADING"]: log.info(self.paper.stats())
                        if enter: log.info(f"SIGNAL {score}/5"); self.open_pos(price,ind)
                time.sleep(self.cfg["CHECK_INTERVAL"])
            except KeyboardInterrupt:
                if self.cfg["PAPER_TRADING"]: log.info(self.paper.stats())
                break
            except Exception as e: log.error(e); time.sleep(60)

if __name__=="__main__":
    TradingBot().run()
