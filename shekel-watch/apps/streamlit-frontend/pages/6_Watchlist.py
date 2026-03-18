"""
Watchlist — search for instruments, add/remove tickers, enriched with live prices.
"""

import time
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Watchlist — Shekel-Watch", page_icon="👁️", layout="wide")

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from components.lang_selector import render_lang_selector
from services.api_client import APIClient, APIError
from services.supabase_client import get_watchlist, add_to_watchlist, remove_from_watchlist
from services.formatters import fmt_ils, fmt_pct
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

token   = st.session_state["access_token"]
user_id = st.session_state["user_id"]
client  = APIClient()


# ── Live-price cache (30-second TTL slot) ─────────────────────────────────────
def _fetch_watchlist_prices(tickers: tuple) -> tuple[dict, str, str | None]:
    """
    Fetch live prices for watchlist tickers.

    Uses a 30-second session-state TTL cache instead of @st.cache_data.
    @st.cache_data is avoided because the APIClient constructor accesses
    st.session_state, which raises inside a cached function in newer
    Streamlit versions — silently returning an empty dict every time.

    Returns (price_map, updated_at, error_message_or_None).
    """
    cache = st.session_state.get("_wl_price_cache", {})
    if cache.get("tickers") == tickers and time.time() - cache.get("ts", 0) < 30:
        return cache["pm"], cache["updated_at"], cache.get("error")

    error_msg: str | None = None
    try:
        quotes = client.get_stocks(list(tickers))
        pm = {q["ticker"]: q for q in quotes}
        if not pm and tickers:
            error_msg = "Backend returned no price data — check server logs"
    except APIError as e:
        pm     = {}
        error_msg = e.message
    except Exception as e:
        pm     = {}
        error_msg = str(e)

    updated_at = datetime.now().strftime("%H:%M:%S")
    st.session_state["_wl_price_cache"] = {
        "tickers":    tickers,
        "ts":         time.time(),
        "pm":         pm,
        "updated_at": updated_at,
        "error":      error_msg,
    }
    return pm, updated_at, error_msg


# ── Search & Add ──────────────────────────────────────────────────────────────
st.subheader(t("search_instruments"))
st.caption(t("search_caption"))

# Fetch watchlist once per page load — used both for duplicate detection and the table
watchlist = get_watchlist(token, user_id)
wl_ticker_set = {item["ticker"] for item in watchlist}

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

if "wl_hits" not in st.session_state:
    st.session_state["wl_hits"] = []

if do_search and query.strip():
    with st.spinner(t("searching")):
        try:
            result = client.search_stocks(query.strip())
            hits   = result.get("quotes", [])
            # Enrich with live prices
            if hits:
                syms = [h["symbol"] for h in hits]
                try:
                    price_list = client.get_stocks(syms)
                    plookup    = {q["ticker"]: q for q in price_list}
                    for h in hits:
                        pq = plookup.get(h["symbol"], {})
                        h["price"]         = pq.get("price")
                        h["changePercent"] = pq.get("changePercent")
                except APIError:
                    pass  # prices are optional in search results
            st.session_state["wl_hits"] = hits
        except APIError as e:
            st.session_state["wl_hits"] = []
            st.error(t("search_failed_msg").format(error=e.message))

if st.session_state["wl_hits"]:
    hits = st.session_state["wl_hits"]
    st.markdown(t("results_found").format(n=len(hits)))

    # Column headers
    hc = st.columns([1.5, 3.5, 1.2, 1.5, 1.5, 1.6])
    for col, lbl in zip(hc, [t("col_symbol"), t("wl_name"), t("wl_type"),
                               t("price"), t("change"), ""]):
        col.caption(f"**{lbl}**")

    for i, h in enumerate(hits):
        sym = h.get("symbol", "")
        ca, cb, cc, cd, ce, cf = st.columns([1.5, 3.5, 1.2, 1.5, 1.5, 1.6])
        ca.markdown(f"**{sym}**")
        cb.write(h.get("name", "")[:40])
        cc.write(h.get("typeDisp", ""))

        p  = h.get("price")
        ch = h.get("changePercent")
        cd.write(fmt_ils(p) if p is not None else "—")
        if ch is not None:
            color = "green" if ch >= 0 else "red"
            ce.markdown(
                f"<span style='color:{color}'>{fmt_pct(ch)}</span>",
                unsafe_allow_html=True,
            )
        else:
            ce.write("—")

        already = sym in wl_ticker_set
        if already:
            cf.button(t("wl_already_added"), key=f"wl_already_{sym}_{i}", disabled=True)
        else:
            if cf.button(t("wl_add_btn"), key=f"wl_add_{sym}_{i}"):
                market = "TASE" if sym.endswith(".TA") else "NYSE"
                res = add_to_watchlist(
                    token, user_id, sym, market,
                    name=h.get("name", ""),
                    asset_type=h.get("typeDisp", ""),
                )
                if res["success"]:
                    st.success(t("added_ticker").format(ticker=sym, market=market))
                    st.session_state["wl_hits"] = []
                    st.rerun()
                else:
                    err = res.get("error", "")
                    if "duplicate" in err.lower() or "unique" in err.lower():
                        st.warning(t("already_in_watchlist").format(ticker=sym))
                    else:
                        st.error(t("failed_to_add").format(error=err))

st.divider()

# ── Watchlist table ───────────────────────────────────────────────────────────
if not watchlist:
    st.info(t("watchlist_empty"))
    st.stop()

tickers = [item["ticker"] for item in watchlist]

# Live prices (session-state TTL cache, 30 s)
price_map, updated_at, price_error = _fetch_watchlist_prices(tuple(tickers))

# Subheader row with timestamp + manual refresh button
sub_col, ref_col = st.columns([5, 1])
sub_col.subheader(t("your_watchlist").format(n=len(watchlist)))
sub_col.caption(f"{t('last_updated')}: {updated_at}")
if ref_col.button(t("refresh"), key="wl_refresh"):
    st.session_state.pop("_wl_price_cache", None)
    st.rerun()

if price_error:
    st.warning(f"⚠ {t('could_not_load_prices').format(error=price_error)}")

# Table column headers
COL_WIDTHS = [1.5, 2.8, 1.2, 1.6, 1.6, 1.3, 1.3, 1.0]
h1, h2, h3, h4, h5, h6, h7, h8 = st.columns(COL_WIDTHS)
for col, lbl in zip(
    [h1, h2, h3, h4, h5, h6, h7, h8],
    [t("col_symbol"), t("wl_name"), t("wl_type"),
     t("price"), t("change"), t("wl_day_high"), t("wl_day_low"), ""],
):
    col.markdown(f"**{lbl}**")

st.markdown("---")

# Rows
for item in watchlist:
    ticker     = item.get("ticker", "")
    name       = item.get("name") or ticker
    asset_type = item.get("asset_type") or "—"
    quote      = price_map.get(ticker, {})
    price      = quote.get("price")
    change_pct = quote.get("changePercent")
    day_high   = quote.get("dayHigh")
    day_low    = quote.get("dayLow")
    stale      = not bool(quote)  # no quote data at all → stale

    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(COL_WIDTHS)

    c1.markdown(f"**{ticker}**")
    c2.write(name[:40] if name else ticker)
    c3.write(asset_type[:14])

    if price is not None:
        c4.write(fmt_ils(price) + (" ⚠" if stale else ""))
    else:
        c4.caption(t("price_na"))

    if change_pct is not None:
        color = "green" if change_pct >= 0 else "red"
        c5.markdown(
            f"<span style='color:{color}'>{fmt_pct(change_pct)}</span>",
            unsafe_allow_html=True,
        )
    else:
        c5.write("—")

    c6.write(fmt_ils(day_high) if day_high else "—")
    c7.write(fmt_ils(day_low)  if day_low  else "—")

    with c8:
        if st.button(t("remove_watchlist_btn"), key=f"remove_{ticker}"):
            result = remove_from_watchlist(token, user_id, ticker)
            if result["success"]:
                st.success(t("removed_ticker").format(ticker=ticker))
                st.rerun()
            else:
                st.error(t("failed_to_remove").format(error=result.get("error", "")))
