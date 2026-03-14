"""
Arbitrage detection service.

1. Currency arbitrage  – compares direct X/ILS rates from Twelve Data
   against the implied rate computed via USD (X/USD × USD/ILS).
   A gap > 0.05 % is flagged as an opportunity.

2. Watchlist arbitrage – for dual-listed Israeli companies, compares
   the TASE price (ILS) with the NYSE/NASDAQ price converted to ILS.
"""

import requests
import pandas as pd
import yfinance as yf
from services.config import get

TWELVE_DATA_KEY = get("TWELVE_DATA_API_KEY")

# Known dual-listed Israeli stocks:  NASDAQ/NYSE ticker → TASE ticker
DUAL_LISTED = {
    "NICE":  "NICE.TA",
    "CHKP":  "CHKP.TA",
    "MNDY":  "MNDY.TA",
    "CYBR":  "CYBR.TA",
    "GLBE":  "GLBE.TA",
    "WIX":   "WIX.TA",
    "ICL":   "ICL.TA",
    "TEVA":  "TEVA.TA",
    "ESLT":  "ESLT.TA",
    "VRNS":  "VRNS.TA",
}
DUAL_LISTED_REV = {v: k for k, v in DUAL_LISTED.items()}

CURRENCIES = ["EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY"]


# ── 1. Currency arbitrage ─────────────────────────────────────────────────────

def get_currency_arbitrage(vs_usd: dict, usd_ils: float) -> pd.DataFrame:
    """
    vs_usd : dict  { "EUR": 1.085, "GBP": 1.263, ... }  (how many USD per 1 unit)
    usd_ils: float  how many ILS per 1 USD

    Strategy: query Twelve Data for direct X/ILS rates, then compare to
    the implied rate = (X/USD) × (USD/ILS).  Any gap indicates an
    arbitrage opportunity between routing trades directly vs via USD.
    """
    direct_pairs = ",".join(f"{c}/ILS" for c in CURRENCIES)

    try:
        resp = requests.get(
            f"https://api.twelvedata.com/price?symbol={direct_pairs}&apikey={TWELVE_DATA_KEY}",
            timeout=8,
        )
        direct_data = resp.json()
    except Exception:
        return pd.DataFrame()

    rows = []
    for code in CURRENCIES:
        pair = f"{code}/ILS"
        try:
            direct_rate = float(direct_data[pair]["price"])
            implied_rate = vs_usd.get(code, 0) * usd_ils     # X→USD→ILS
            if implied_rate == 0:
                continue
            gap_pct = (direct_rate - implied_rate) / implied_rate * 100

            rows.append({
                "Pair":             pair,
                "Direct (X→ILS)":   round(direct_rate, 4),
                "Via USD (X→$→₪)":  round(implied_rate, 4),
                "Gap %":            round(gap_pct, 4),
                "Signal":           _arb_signal(gap_pct),
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Gap %", key=abs, ascending=False).reset_index(drop=True)
    return df


def _arb_signal(gap: float) -> str:
    if gap > 0.05:
        return "⚡ Buy via USD"      # cheaper to convert X→USD→ILS
    if gap < -0.05:
        return "⚡ Buy direct"       # cheaper to convert X→ILS directly
    return "— Neutral"


# ── 2. Watchlist arbitrage ────────────────────────────────────────────────────

def get_watchlist_arbitrage(tickers: list, usd_ils: float) -> pd.DataFrame:
    """
    For each ticker in the watchlist, checks if a dual-listed counterpart
    exists.  Compares the TASE price (ILS) with the foreign price × USD/ILS.
    """
    rows = []
    seen = set()

    for ticker in tickers:
        # Resolve the pair
        if ticker.endswith(".TA"):
            tase    = ticker
            foreign = DUAL_LISTED_REV.get(ticker)
        else:
            foreign = ticker
            tase    = DUAL_LISTED.get(ticker)

        if not tase or not foreign:
            continue

        pair_key = (foreign, tase)
        if pair_key in seen:
            continue
        seen.add(pair_key)

        try:
            tase_hist    = yf.Ticker(tase).history(period="1d")
            foreign_hist = yf.Ticker(foreign).history(period="1d")

            if tase_hist.empty or foreign_hist.empty:
                continue

            tase_price_ils    = tase_hist["Close"].iloc[-1]
            foreign_price_usd = foreign_hist["Close"].iloc[-1]
            foreign_in_ils    = foreign_price_usd * usd_ils

            gap_pct = (tase_price_ils - foreign_in_ils) / foreign_in_ils * 100

            if gap_pct > 0.5:
                trade = "⚡ Sell TASE / Buy NYSE"
            elif gap_pct < -0.5:
                trade = "⚡ Buy TASE / Sell NYSE"
            else:
                trade = "— Neutral"

            rows.append({
                "Stock":               f"{foreign} / {tase}",
                "TASE (₪)":            round(tase_price_ils, 2),
                "NYSE in ₪":           round(foreign_in_ils, 2),
                "NYSE (USD)":          round(foreign_price_usd, 2),
                "Gap %":               round(gap_pct, 2),
                "Signal":              trade,
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Gap %", key=abs, ascending=False).reset_index(drop=True)
    return df
