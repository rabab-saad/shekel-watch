import requests
import pandas as pd
from services.config import get

TWELVE_DATA_KEY   = get("TWELVE_DATA_API_KEY")
EXCHANGE_RATE_KEY = get("EXCHANGE_RATE_API_KEY")

CURRENCY_INFO = {
    "EUR": ("Euro",              "🇪🇺"),
    "GBP": ("British Pound",     "🇬🇧"),
    "JPY": ("Japanese Yen",      "🇯🇵"),
    "CHF": ("Swiss Franc",       "🇨🇭"),
    "CAD": ("Canadian Dollar",   "🇨🇦"),
    "AUD": ("Australian Dollar", "🇦🇺"),
    "CNY": ("Chinese Yuan",      "🇨🇳"),
}

FX_PAIRS = ",".join([f"{c}/USD" for c in CURRENCY_INFO]) + ",USD/ILS"


def get_rates_df() -> tuple:
    """Returns (pd.DataFrame, usd_ils_rate)"""

    # Primary: Twelve Data
    try:
        resp = requests.get(
            f"https://api.twelvedata.com/price?symbol={FX_PAIRS}&apikey={TWELVE_DATA_KEY}",
            timeout=8,
        )
        data = resp.json()
        usd_ils = float(data["USD/ILS"]["price"])
        rows = []
        for code, (name, flag) in CURRENCY_INFO.items():
            vs_usd = float(data[f"{code}/USD"]["price"])
            rows.append({
                "Currency": f"{flag} {name}",
                "Code":     code,
                "vs USD":   round(vs_usd, 4),
                "vs ILS":   round(vs_usd * usd_ils, 4),
            })
        return pd.DataFrame(rows), usd_ils
    except Exception:
        pass

    # Fallback: ExchangeRate-API
    resp = requests.get(
        f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_KEY}/latest/USD",
        timeout=6,
    )
    data = resp.json()
    usd_ils = data["conversion_rates"]["ILS"]
    rows = []
    for code, (name, flag) in CURRENCY_INFO.items():
        rate   = data["conversion_rates"].get(code, 1)
        vs_usd = 1 / rate if rate else 0
        rows.append({
            "Currency": f"{flag} {name}",
            "Code":     code,
            "vs USD":   round(vs_usd, 4),
            "vs ILS":   round(vs_usd * usd_ils, 4),
        })
    return pd.DataFrame(rows), usd_ils
