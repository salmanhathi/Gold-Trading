import json, re, datetime as dt, os
import requests, yfinance as yf
from bs4 import BeautifulSoup

TICKERS = {"gold": "GC=F", "dxy": "DX-Y.NYB", "tnx": "^TNX", "vix": "^VIX", "silver": "SI=F", "spx": "^GSPC"}
old = {}
if os.path.exists("data.json"):
    try: old = json.load(open("data.json"))
    except Exception: pass

out = {"updated": dt.datetime.utcnow().isoformat() + "Z", "series": {}, "retail": old.get("retail"), "retail_hist": old.get("retail_hist", [])}

for key, sym in TICKERS.items():
    try:
        h = yf.Ticker(sym).history(period="5y", interval="1d")["Close"].dropna()
        out["series"][key] = [[d.strftime("%Y-%m-%d"), round(float(v), 2)] for d, v in h.items()]
    except Exception as e:
        print("failed", sym, e)
        out["series"][key] = old.get("series", {}).get(key, [])

# Dubai Jewellery Group suggested retail rates (AED/g)
try:
    html = requests.get("https://dubaicityofgold.com", headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
    text = BeautifulSoup(html, "html.parser").get_text(" ")
    rates = {f"{k}K": float(v.replace(",", "")) for k, v in re.findall(r"(\d\d)K Gold\s*AED\s*([\d.,]+)", text)}
    if rates.get("24K"):
        out["retail"] = rates
        today = dt.date.today().isoformat()
        out["retail_hist"] = [r for r in out["retail_hist"] if r["d"] != today] + [{"d": today, **rates}]
except Exception as e:
    print("retail scrape failed", e)

json.dump(out, open("data.json", "w"))
print("ok", {k: len(v) for k, v in out["series"].items()}, out["retail"])
