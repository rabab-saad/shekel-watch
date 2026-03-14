import yfinance as yf
import pandas as pd

INDICES = {
    "TA-35":     "^TA35",
    "S&P 500":   "^GSPC",
    "NASDAQ":    "^IXIC",
    "Dow Jones": "^DJI",
}


def get_indices_df() -> pd.DataFrame:
    rows = []
    for name, symbol in INDICES.items():
        try:
            hist = yf.Ticker(symbol).history(period="2d")
            if len(hist) >= 2:
                current = hist["Close"].iloc[-1]
                prev    = hist["Close"].iloc[-2]
            elif len(hist) == 1:
                current = hist["Close"].iloc[-1]
                prev    = current
            else:
                continue
            change     = current - prev
            change_pct = (change / prev) * 100 if prev else 0
            rows.append({
                "Index":    name,
                "Price":    round(current, 2),
                "Change":   round(change, 2),
                "Change %": round(change_pct, 2),
            })
        except Exception:
            continue
    return pd.DataFrame(rows)


def get_stock_quote(symbol: str) -> dict:
    try:
        t    = yf.Ticker(symbol)
        hist = t.history(period="2d")
        info = t.info
        current    = hist["Close"].iloc[-1] if len(hist) >= 1 else 0
        prev       = hist["Close"].iloc[-2] if len(hist) >= 2 else current
        change_pct = ((current - prev) / prev * 100) if prev else 0
        return {
            "Ticker":   symbol,
            "Name":     info.get("longName") or info.get("shortName") or symbol,
            "Price":    round(current, 2),
            "Change %": round(change_pct, 2),
            "Currency": info.get("currency", "USD"),
            "Market":   info.get("marketState", "CLOSED"),
        }
    except Exception:
        return {"Ticker": symbol, "Name": symbol, "Price": 0, "Change %": 0, "Currency": "USD", "Market": "CLOSED"}


def get_stock_history(symbol: str, period: str = "1mo") -> pd.DataFrame:
    hist = yf.Ticker(symbol).history(period=period)
    return hist[["Open", "High", "Low", "Close", "Volume"]].round(2)


def get_watchlist_df(tickers: list) -> pd.DataFrame:
    return pd.DataFrame([get_stock_quote(t) for t in tickers])
