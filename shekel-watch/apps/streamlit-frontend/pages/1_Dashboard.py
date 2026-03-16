"""
Dashboard — USD/ILS ticker, AI summary, TASE phase, risk heatmap, charts.
"""

import streamlit as st

st.set_page_config(page_title="Dashboard — Shekel-Watch", page_icon="📈", layout="wide")

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from components.tase_phase_timer import render_phase_timer
from components.term_tooltip import render_term
from components.charts import render_area_chart, render_candlestick_chart
from services.api_client import APIClient, APIError
from services.supabase_client import get_watchlist
from services.formatters import fmt_ils, fmt_pct, risk_label, risk_label_he

if not require_auth():
    st.stop()

with st.sidebar:
    st.markdown("## 📊 Shekel-Watch")
    st.divider()
    render_mode_toggle()
    st.divider()
    render_sidebar_user()

# ─────────────────────────────────────────────────────────────────────────────
st.title("📈 Dashboard")
render_phase_timer()
st.divider()

client = APIClient()
mode = st.session_state.get("trading_mode", "beginner")
lang = st.session_state.get("language", "en")

# ── Row 1: USD/ILS + AI Summary ───────────────────────────────────────────────
col_rate, col_summary = st.columns([1, 2])

with col_rate:
    st.subheader("💵 USD / ILS Rate")
    try:
        rate_data = client.get_usd_ils()
        rate = rate_data.get("rate", 0)
        source = rate_data.get("source", "")
        change = rate_data.get("change", None)

        st.metric(
            label="Current Rate",
            value=fmt_ils(rate, decimals=4),
            delta=f"{change:+.4f}" if change is not None else None,
            help=f"Source: {source}",
        )
        render_term("exchange rate", "Exchange Rate")
    except APIError as e:
        st.error(f"Rate unavailable: {e.message}")

with col_summary:
    st.subheader("🤖 AI Market Summary")
    if st.button("Refresh Summary ↻", key="refresh_summary"):
        st.cache_data.clear()

    @st.cache_data(ttl=300, show_spinner="Generating AI summary…")
    def fetch_summary(language: str) -> str:
        return client.get_summary(lang=language).get("summary", "Summary unavailable.")

    try:
        summary_text = fetch_summary(lang)
        st.markdown(summary_text)
    except APIError as e:
        st.warning(f"Summary unavailable: {e.message}")

st.divider()

# ── Row 2: Key TASE Stocks ────────────────────────────────────────────────────
st.subheader("📊 TASE Movers")

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
    st.warning(f"Stock data unavailable: {e.message}")

st.divider()

# ── Row 3: Risk Heatmap (compact) ────────────────────────────────────────────
st.subheader("🌡️ Watchlist Risk Heatmap")
token = st.session_state["access_token"]
user_id = st.session_state["user_id"]
watchlist = get_watchlist(token, user_id)

if not watchlist:
    st.info("No watchlist items yet. Add tickers in the Watchlist page.")
else:
    risk_cols = st.columns(min(len(watchlist), 6))
    for i, item in enumerate(watchlist[:6]):
        ticker = item.get("ticker", "")
        risk = item.get("risk_score", 0) or 0
        with risk_cols[i % 6]:
            label = f"{ticker}\n{risk_label(risk)} / {risk_label_he(risk)}"
            if risk <= 3:
                st.success(f"**{ticker}**\nRisk: {risk}/10\n{risk_label(risk)}")
            elif risk <= 6:
                st.warning(f"**{ticker}**\nRisk: {risk}/10\n{risk_label(risk)}")
            else:
                st.error(f"**{ticker}**\nRisk: {risk}/10\n{risk_label(risk)}")

st.divider()

# ── Row 4: Price Chart ────────────────────────────────────────────────────────
st.subheader("📉 Price Chart")

chart_ticker = st.selectbox("Select Ticker", TASE_TICKERS, key="chart_ticker")
period_opts = {"1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo", "1 Year": "1y"}
period_label = st.select_slider("Period", options=list(period_opts.keys()), value="3 Months")
period = period_opts[period_label]

try:
    history = client.get_stock_history(chart_ticker, period)
    if mode == "pro":
        render_candlestick_chart(history, chart_ticker)
    else:
        render_area_chart(history, chart_ticker)
except APIError as e:
    st.warning(f"Chart data unavailable: {e.message}")

st.divider()

# ── Term Glossary (compact) ───────────────────────────────────────────────────
with st.expander("📖 Financial Glossary"):
    col_a, col_b = st.columns(2)
    with col_a:
        render_term("arbitrage", "Arbitrage")
        render_term("risk score", "Risk Score")
    with col_b:
        render_term("market cap", "Market Cap")
        render_term("P/E ratio", "P/E Ratio")
