"""
Watchlist — search for instruments, add/remove tickers, enriched with live prices.
"""

import streamlit as st

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

# ── Search & Add ──────────────────────────────────────────────────────────────
st.subheader(t("search_instruments"))
st.caption(t("search_caption"))

col_q, col_btn = st.columns([4, 1])
with col_q:
    query = st.text_input(
        "Search",
        placeholder=t("search_placeholder"),
        label_visibility="collapsed",
        key="wl_search_query",
    )
with col_btn:
    do_search = st.button(t("search_btn"), use_container_width=True, key="wl_search_btn")

if do_search and query:
    with st.spinner(t("searching")):
        try:
            result = client.search_stocks(query)
            hits = result.get("quotes", [])
        except APIError as e:
            hits = []
            st.error(t("search_failed_msg").format(error=e.message))

    if not hits:
        st.info(t("no_results"))
    else:
        st.markdown(t("results_found").format(n=len(hits)))
        for i, h in enumerate(hits):
            ca, cb, cc, cd, ce = st.columns([1.5, 3.5, 1.2, 1.2, 1])
            ca.markdown(f"**{h.get('symbol', '')}**")
            cb.write(h.get("name", ""))
            cc.write(h.get("typeDisp", ""))
            cd.write(h.get("exchange", ""))
            if ce.button(t("add"), key=f"wl_add_{h['symbol']}_{i}"):
                sym = h["symbol"]
                market = "TASE" if sym.endswith(".TA") else "NYSE"
                res = add_to_watchlist(token, user_id, sym, market)
                if res["success"]:
                    st.success(t("added_ticker").format(ticker=sym, market=market))
                    st.rerun()
                else:
                    err = res.get("error", "")
                    if "duplicate" in err.lower() or "unique" in err.lower():
                        st.warning(t("already_in_watchlist").format(ticker=sym))
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
