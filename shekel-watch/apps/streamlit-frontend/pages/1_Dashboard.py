"""
Dashboard — USD/ILS ticker, AI summary, TASE phase, risk heatmap, charts.
"""

import streamlit as st

st.set_page_config(page_title="Dashboard — Shekel-Watch", page_icon="📈", layout="wide")

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from components.lang_selector import render_lang_selector
from components.tase_phase_timer import render_phase_timer
from components.term_tooltip import render_term
from components.charts import render_area_chart, render_candlestick_chart
from components.exchange_banner import render_exchange_banner
from services.api_client import APIClient, APIError
from services.supabase_client import get_watchlist
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
st.title(t("dashboard_title"))
render_exchange_banner()
render_phase_timer()
st.divider()

client = APIClient()
mode = st.session_state.get("trading_mode", "beginner")
lang = st.session_state.get("language", "en")

# ── Row 1: USD/ILS + AI Summary ───────────────────────────────────────────────
col_rate, col_summary = st.columns([1, 2])

with col_rate:
    st.subheader(t("usd_ils_rate"))
    try:
        rate_data = client.get_usd_ils()
        rate = rate_data.get("rate", 0)
        source = rate_data.get("source", "")
        change = rate_data.get("change", None)

        st.metric(
            label=t("current_rate"),
            value=fmt_ils(rate, decimals=4),
            delta=f"{change:+.4f}" if change is not None else None,
            help=f"Source: {source}",
        )
        render_term("exchange rate", "Exchange Rate")
    except APIError as e:
        st.error(t("rate_unavailable").format(error=e.message))

with col_summary:
    st.subheader(t("ai_market_summary"))
    if st.button(t("refresh_summary"), key="refresh_summary"):
        st.cache_data.clear()

    @st.cache_data(ttl=300, show_spinner=True)
    def fetch_summary(language: str) -> str:
        return client.get_summary(lang=language).get("summary", "Summary unavailable.")

    try:
        summary_text = fetch_summary(lang)
        st.markdown(summary_text)
    except APIError as e:
        st.warning(t("summary_unavailable").format(error=e.message))

st.divider()

# ── Row 2: Key TASE Stocks ────────────────────────────────────────────────────
st.subheader(t("tase_movers"))

TASE_TICKERS = ["LUMI.TA", "TEVA.TA", "ESLT.TA", "CHKP.TA", "NICE.TA", "HARL.TA"]

try:
    stocks = client.get_stocks(TASE_TICKERS)
    if stocks:
        cols = st.columns(len(stocks))
        for col, stock in zip(cols, stocks):
            ticker = stock.get("ticker", "")
            name = stock.get("name", ticker)
            price = stock.get("price", 0)
            change_pct = stock.get("changePercent", 0)
            with col:
                st.metric(
                    label=ticker,
                    value=fmt_ils(price),
                    delta=fmt_pct(change_pct),
                    delta_color="normal" if change_pct >= 0 else "inverse",
                    help=name,
                )
except APIError as e:
    st.warning(t("stock_data_unavailable").format(error=e.message))

st.divider()

# ── Row 3: Risk Heatmap (compact) ────────────────────────────────────────────
st.subheader(t("watchlist_risk_heatmap"))
token = st.session_state["access_token"]
user_id = st.session_state["user_id"]
watchlist = get_watchlist(token, user_id)

if not watchlist:
    st.info(t("no_watchlist_items"))
else:
    risk_cols = st.columns(min(len(watchlist), 6))
    for i, item in enumerate(watchlist[:6]):
        ticker = item.get("ticker", "")
        risk = item.get("risk_score", 0) or 0
        with risk_cols[i % 6]:
            rl = risk_label(risk)
            if risk <= 3:
                st.success(f"**{ticker}**\nRisk: {risk}/10\n{rl}")
            elif risk <= 6:
                st.warning(f"**{ticker}**\nRisk: {risk}/10\n{rl}")
            else:
                st.error(f"**{ticker}**\nRisk: {risk}/10\n{rl}")

st.divider()

# ── Row 4: Price Chart ────────────────────────────────────────────────────────
st.subheader(t("price_chart"))

chart_ticker = st.selectbox(t("select_ticker"), TASE_TICKERS, key="chart_ticker")
period_opts = {
    t("period_1m"): "1mo",
    t("period_3m"): "3mo",
    t("period_6m"): "6mo",
    t("period_1y"): "1y",
}
period_label = st.select_slider(t("period"), options=list(period_opts.keys()), value=list(period_opts.keys())[1])
period = period_opts[period_label]

try:
    history = client.get_stock_history(chart_ticker, period)
    if mode == "pro":
        render_candlestick_chart(history, chart_ticker)
    else:
        render_area_chart(history, chart_ticker)
except APIError as e:
    st.warning(t("chart_data_unavailable").format(error=e.message))

st.divider()

# ── Term Glossary (compact) ───────────────────────────────────────────────────
with st.expander(t("financial_glossary")):
    col_a, col_b = st.columns(2)
    with col_a:
        render_term("arbitrage", "Arbitrage")
        render_term("risk score", "Risk Score")
    with col_b:
        render_term("market cap", "Market Cap")
        render_term("P/E ratio", "P/E Ratio")
