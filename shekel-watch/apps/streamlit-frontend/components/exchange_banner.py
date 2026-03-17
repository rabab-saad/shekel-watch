"""
Live exchange rate banner — horizontal card row, auto-refreshes every 60 s.
Shows EUR, GBP, USD, JPY, CHF, CAD, AUD vs ILS and USD.
Falls back to last known values with a stale indicator on API errors.
"""

import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

_BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:3001").rstrip("/")
_CURRENCIES = ["EUR", "GBP", "USD", "JPY", "CHF", "CAD", "AUD"]

# Currency display metadata
_META = {
    "EUR": {"flag": "🇪🇺", "name": "Euro"},
    "GBP": {"flag": "🇬🇧", "name": "Pound"},
    "USD": {"flag": "🇺🇸", "name": "Dollar"},
    "JPY": {"flag": "🇯🇵", "name": "Yen"},
    "CHF": {"flag": "🇨🇭", "name": "Franc"},
    "CAD": {"flag": "🇨🇦", "name": "CAD"},
    "AUD": {"flag": "🇦🇺", "name": "AUD"},
}


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_rates(backend_url: str) -> dict:
    resp = requests.get(f"{backend_url}/api/rates/all", timeout=15)
    resp.raise_for_status()
    return resp.json()


def render_exchange_banner():
    """Render the live exchange rate banner. Call once at the top of the Dashboard."""
    from streamlit_autorefresh import st_autorefresh  # imported here to avoid errors on other pages

    # Trigger a full page re-run every 60 s (60 000 ms)
    st_autorefresh(interval=60_000, key="exchange_banner_refresh")

    # ── Fetch data ────────────────────────────────────────────────────────────
    is_stale = False
    data = None
    try:
        data = _fetch_rates(_BACKEND_URL)
        st.session_state["_rates_last_good"] = data
    except Exception:
        data = st.session_state.get("_rates_last_good")
        is_stale = True

    from utils.i18n import t

    if not data:
        st.warning(t("live_exchange_rates") + " — will retry in 60 s.")
        return

    # ── Build lookup ──────────────────────────────────────────────────────────
    rates_map = {r["code"]: r for r in data.get("rates", [])}
    usd_ils = data.get("usdIls", 0.0)
    # USD is not in the rates list (it's the base for vsUsd), so inject it manually
    rates_map["USD"] = {"code": "USD", "vsUsd": 1.0, "vsIls": usd_ils}

    # ── Header ────────────────────────────────────────────────────────────────
    stale_html = (
        f" &nbsp;<span style='color:#f59e0b;font-size:0.75rem;'>⚠ {t('stale')}</span>"
        if is_stale
        else ""
    )
    fetched_at = data.get("fetchedAt", "")
    time_str = fetched_at[11:19] if len(fetched_at) >= 19 else ""
    time_html = (
        f"<span style='color:#64748b;font-size:0.7rem;margin-left:8px;'>{t('updated_at').format(time=time_str)}</span>"
        if time_str and not is_stale
        else ""
    )

    st.markdown(
        f"<p style='margin:0 0 6px 0;font-size:0.8rem;color:#94a3b8;'>"
        f"<b>{t('live_exchange_rates')}</b>{stale_html}{time_html}</p>",
        unsafe_allow_html=True,
    )

    # ── Cards ─────────────────────────────────────────────────────────────────
    cols = st.columns(len(_CURRENCIES))
    for col, code in zip(cols, _CURRENCIES):
        r = rates_map.get(code)
        if not r:
            continue
        meta = _META.get(code, {"flag": "", "name": code})
        vs_ils = r.get("vsIls", 0.0)
        vs_usd = r.get("vsUsd", 0.0)

        # Format: JPY and similar low-value currencies need fewer decimals vs ILS
        ils_fmt = f"{vs_ils:.2f}" if vs_ils >= 10 else f"{vs_ils:.4f}"
        usd_fmt = f"{vs_usd:.4f}" if vs_usd < 10 else f"{vs_usd:.2f}"

        card_html = f"""
        <div style="
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 10px 8px;
            text-align: center;
            line-height: 1.5;
        ">
            <div style="font-size:1.2rem;">{meta['flag']}</div>
            <div style="font-weight:700;font-size:0.95rem;color:#f1f5f9;">{code}</div>
            <div style="font-size:0.75rem;color:#94a3b8;">₪ {ils_fmt}</div>
            <div style="font-size:0.75rem;color:#64748b;">$ {usd_fmt}</div>
        </div>
        """
        col.markdown(card_html, unsafe_allow_html=True)

    st.divider()
