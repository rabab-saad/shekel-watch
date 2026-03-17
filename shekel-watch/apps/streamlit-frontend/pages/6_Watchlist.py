"""
Watchlist — add/remove tickers, enriched with live prices from the backend.
"""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Watchlist — Shekel-Watch", page_icon="👁️", layout="wide")

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from components.lang_selector import render_lang_selector
from services.api_client import APIClient, APIError
from services.supabase_client import get_watchlist, add_to_watchlist, remove_from_watchlist
from services.formatters import fmt_ils, fmt_pct, risk_label
from utils.i18n import t, inject_dir

if not require_auth():
    st.stop()

inject_dir()

with st.sidebar:
    st.markdown(t("sidebar_title"))
    st.divider()
    render_lang_selector()
    render_mode_toggle()
    st.divider()
    render_sidebar_user()

# ─────────────────────────────────────────────────────────────────────────────
st.title(t("watchlist_title"))
st.caption(t("watchlist_caption"))

token = st.session_state["access_token"]
user_id = st.session_state["user_id"]
client = APIClient()

# ── Add ticker ────────────────────────────────────────────────────────────────
with st.form("add_ticker_form"):
    col_input, col_market, col_btn = st.columns([3, 1, 1])
    with col_input:
        new_ticker = st.text_input(
            "Ticker Symbol",
            placeholder=t("ticker_placeholder"),
            label_visibility="collapsed",
        )
    with col_market:
        market_options = [t("auto_detect"), "TASE", "NYSE", "NASDAQ"]
        market_select = st.selectbox(t("market"), market_options, label_visibility="collapsed")
    with col_btn:
        add_submitted = st.form_submit_button(t("add"), use_container_width=True)

if add_submitted:
    ticker_clean = new_ticker.strip().upper()
    if not ticker_clean:
        st.error(t("please_enter_ticker"))
    else:
        # Auto-detect market
        if market_select == t("auto_detect"):
            market = "TASE" if ticker_clean.endswith(".TA") else "NYSE"
        else:
            market = market_select

        result = add_to_watchlist(token, user_id, ticker_clean, market)
        if result["success"]:
            st.success(t("added_ticker").format(ticker=ticker_clean, market=market))
            st.rerun()
        else:
            err = result.get("error", "")
            if "duplicate" in err.lower() or "unique" in err.lower():
                st.warning(t("already_in_watchlist").format(ticker=ticker_clean))
            else:
                st.error(t("failed_to_add").format(error=err))

st.divider()

# ── Fetch watchlist + live prices ─────────────────────────────────────────────
watchlist = get_watchlist(token, user_id)

if not watchlist:
    st.info(t("watchlist_empty"))
    st.stop()

tickers = [item["ticker"] for item in watchlist]
price_map: dict[str, dict] = {}

try:
    quotes = client.get_stocks(tickers)
    for q in quotes:
        price_map[q["ticker"]] = q
except APIError as e:
    st.warning(t("could_not_load_prices").format(error=e.message))

# ── Watchlist table ───────────────────────────────────────────────────────────
st.subheader(t("your_watchlist").format(n=len(watchlist)))

for item in watchlist:
    ticker = item.get("ticker", "")
    market = item.get("market", "")
    risk = item.get("risk_score") or 0
    quote = price_map.get(ticker, {})
    price = quote.get("price", None)
    change_pct = quote.get("changePercent", None)
    name = quote.get("name", ticker)

    with st.container(border=True):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])

        with col1:
            st.markdown(f"**{ticker}**")
            st.caption(name[:40] if name else "")

        with col2:
            st.caption(f"{t('market')}: {market}")

        with col3:
            if price is not None:
                st.metric(
                    t("price"),
                    fmt_ils(price),
                    delta=fmt_pct(change_pct) if change_pct is not None else None,
                    delta_color="normal" if (change_pct or 0) >= 0 else "inverse",
                )
            else:
                st.caption(t("price_na"))

        with col4:
            risk_lbl = risk_label(risk)
            if risk <= 3:
                st.success(f"{t('risk')}: {risk}/10\n{risk_lbl}")
            elif risk <= 6:
                st.warning(f"{t('risk')}: {risk}/10\n{risk_lbl}")
            else:
                st.error(f"{t('risk')}: {risk}/10\n{risk_lbl}")

        with col5:
            if st.button(t("remove_watchlist_btn"), key=f"remove_{ticker}"):
                result = remove_from_watchlist(token, user_id, ticker)
                if result["success"]:
                    st.success(t("removed_ticker").format(ticker=ticker))
                    st.rerun()
                else:
                    st.error(t("failed_to_remove").format(error=result.get("error", "")))
