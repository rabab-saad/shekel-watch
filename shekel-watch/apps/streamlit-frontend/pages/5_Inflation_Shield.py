"""
Inflation Shield — shows real purchasing power erosion since Jan 2020.
"""

import streamlit as st

st.set_page_config(page_title="Inflation Shield — Shekel-Watch", page_icon="🛡️", layout="wide")

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from components.term_tooltip import render_term
from services.api_client import APIClient, APIError
from services.formatters import fmt_ils, fmt_usd, fmt_pct

if not require_auth():
    st.stop()

with st.sidebar:
    st.markdown("## 📊 Shekel-Watch")
    st.divider()
    render_mode_toggle()
    st.divider()
    render_sidebar_user()

# ─────────────────────────────────────────────────────────────────────────────
st.title("🛡️ Inflation Shield")
st.caption("See how Israeli inflation has eroded purchasing power since January 2020.")

render_term("inflation", "What is Inflation? / מה זה אינפלציה?")
st.divider()

client = APIClient()

# ── Fetch inflation data ──────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner="Loading Bank of Israel CPI data…")
def fetch_inflation():
    return client.get_inflation()

try:
    inf = fetch_inflation()
except APIError as e:
    st.error(f"Failed to load inflation data: {e.message}")
    st.stop()

cpi_current = inf.get("cpiCurrent", 0)
cpi_baseline = inf.get("cpiBaseline2020", 0)
usd_ils_now = inf.get("usdIls", 3.6)
usd_ils_2020 = inf.get("usdIlsBaseline2020", 3.456)

if not cpi_baseline or not cpi_current:
    st.error("CPI data unavailable. Please try again later.")
    st.stop()

inflation_rate = ((cpi_current - cpi_baseline) / cpi_baseline) * 100

# ── Input ─────────────────────────────────────────────────────────────────────
st.subheader("הכנס את החסכונות שלך / Enter Your Savings")
savings = st.number_input(
    "Savings amount (₪)",
    min_value=0.0,
    max_value=100_000_000.0,
    value=100_000.0,
    step=1000.0,
    format="%.0f",
    help="Enter the amount in Israeli Shekels you want to analyse",
)

if savings <= 0:
    st.info("Enter a savings amount above to see the inflation analysis.")
    st.stop()

st.divider()

# ── Calculations ──────────────────────────────────────────────────────────────
# Real value after CPI inflation
real_value = savings / (cpi_current / cpi_baseline)
real_delta = real_value - savings

# USD equivalent: what was the USD value in 2020 vs now
usd_value_2020 = savings / usd_ils_2020  # how many USD you could buy with this ILS in 2020
usd_value_now = savings / usd_ils_now    # how many USD you can buy today
usd_delta_ils = (usd_value_now - usd_value_2020) * usd_ils_now  # expressed in ILS terms

# ── Display ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📉 Real Purchasing Power")
    st.metric(
        label="Real value of your savings (Jan 2020 → today)",
        value=fmt_ils(real_value),
        delta=f"{fmt_ils(real_delta)} ({fmt_pct(real_delta / savings * 100)})",
        delta_color="inverse",  # loss = red
        help=f"Adjusted using Bank of Israel CPI. Total inflation since Jan 2020: {inflation_rate:.1f}%",
    )
    st.caption(
        f"CPI Jan 2020: {cpi_baseline:.1f} → today: {cpi_current:.1f} "
        f"(+{inflation_rate:.1f}% total)"
    )

with col2:
    st.subheader("💵 USD Purchasing Power")
    st.metric(
        label="USD you could buy: 2020 vs today",
        value=f"${usd_value_now:,.2f} now",
        delta=f"${usd_value_now - usd_value_2020:+,.2f} vs 2020",
        delta_color="normal" if usd_value_now >= usd_value_2020 else "inverse",
        help=f"USD/ILS was ₪{usd_ils_2020} in Jan 2020, now ₪{usd_ils_now:.4f}",
    )
    st.caption(f"USD/ILS Jan 2020: ₪{usd_ils_2020:.4f} → today: ₪{usd_ils_now:.4f}")

st.divider()

# ── Inflation summary ─────────────────────────────────────────────────────────
st.subheader("📊 Inflation Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Total CPI Inflation (since Jan 2020)", fmt_pct(inflation_rate))
c2.metric("ILS / USD Change", fmt_pct((usd_ils_now - usd_ils_2020) / usd_ils_2020 * 100))
c3.metric("Your Savings Erosion", fmt_ils(abs(real_delta)), delta=fmt_pct(real_delta / savings * 100, sign=False), delta_color="inverse")

st.divider()

# ── Hedge suggestions ─────────────────────────────────────────────────────────
st.subheader("💡 Inflation Hedge Ideas / רעיונות לגידור")
st.markdown(
    "Inflation erodes cash savings. Here are common inflation hedges relevant to Israeli investors:"
)

h1, h2, h3 = st.columns(3)
with h1:
    with st.container(border=True):
        st.markdown("### 🇺🇸 USD Exposure")
        st.markdown(
            "Hold savings in USD or USD-linked assets (US ETFs, dollar deposits). "
            "ILS tends to weaken vs USD during inflation spikes."
        )
        render_term("currency hedge", "Currency Hedge")
with h2:
    with st.container(border=True):
        st.markdown("### 🏦 Linked Bonds (צמוד)")
        st.markdown(
            "Israeli CPI-linked (מדד) bonds and savings plans protect the real value "
            "of your principal against inflation."
        )
        render_term("CPI linked bond", "CPI-Linked Bond")
with h3:
    with st.container(border=True):
        st.markdown("### 📈 Real Assets")
        st.markdown(
            "Real estate, commodities (gold, oil), and inflation-resilient stocks "
            "(energy, materials) have historically outperformed cash during inflationary periods."
        )
        render_term("real assets", "Real Assets")
