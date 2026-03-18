"""
Dashboard — USD/ILS ticker, AI summary, TASE phase, daily market news, charts.
"""

import streamlit as st

st.set_page_config(page_title="Dashboard — Shekel-Watch", page_icon="📈", layout="wide")

import time

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from components.lang_selector import render_lang_selector
from components.tase_phase_timer import render_phase_timer
from components.term_tooltip import render_term
from components.charts import render_area_chart, render_candlestick_chart
from components.exchange_banner import render_exchange_banner
from services.api_client import APIClient, APIError
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

# ── Row 3: Daily Market News Analysis ────────────────────────────────────────
st.subheader(t("daily_market_analysis"))

# 30-minute cache key — changes every 30 min so st.cache_data re-fetches
_news_cache_slot = int(time.time() // 1800)

if st.button(t("refresh_market_news"), key="refresh_market_news"):
    st.cache_data.clear()
    _news_cache_slot = int(time.time() // 1800) + 1  # bust the slot

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_market_news(language: str, _slot: int) -> dict:
    return client.get_market_news(lang=language)

try:
    with st.spinner(t("generating_market_analysis")):
        news_data = fetch_market_news(lang, _news_cache_slot)

    us_text     = news_data.get("usAnalysis", "")
    israel_text = news_data.get("israelAnalysis", "")
    indices     = news_data.get("indices", [])
    generated   = news_data.get("generatedAt", "")

    # AI paragraphs
    col_us, col_il = st.columns(2)
    with col_us:
        st.markdown(f"**🇺🇸 {t('us_market_analysis')}**")
        st.markdown(us_text or "—")
    with col_il:
        st.markdown(f"**🇮🇱 {t('israel_market_analysis')}**")
        st.markdown(israel_text or "—")

    # Index snapshot row
    if indices:
        st.markdown("")
        idx_cols = st.columns(len(indices))
        for col, idx in zip(idx_cols, indices):
            chg   = idx.get("changePercent", 0) or 0
            price = idx.get("price", 0) or 0
            with col:
                st.metric(
                    label=idx.get("name", idx.get("ticker", "")),
                    value=f"{price:,.2f}",
                    delta=fmt_pct(chg),
                    delta_color="normal" if chg >= 0 else "inverse",
                )

    # Timestamp
    if generated:
        try:
            from datetime import datetime, timezone
            dt  = datetime.fromisoformat(generated.replace("Z", "+00:00"))
            hm  = dt.astimezone(timezone.utc).strftime("%H:%M UTC")
            st.caption(f"{t('last_updated')}: {hm}")
        except Exception:
            pass

except APIError as e:
    st.warning(t("market_news_unavailable").format(error=e.message))

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
