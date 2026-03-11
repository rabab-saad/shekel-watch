import streamlit as st
import plotly.express as px
from services.market_service import get_indices_df
from services.currency_service import get_rates_df
from services.crew_service import get_market_summary

st.set_page_config(page_title="Dashboard | Shekel-Watch", page_icon="₪", layout="wide")

# ── Auth guard ────────────────────────────────────────────────────────────────
if not st.session_state.get("user"):
    st.warning("Please sign in first.")
    st.page_link("app.py", label="← Go to Login")
    st.stop()

user  = st.session_state["user"]
token = st.session_state.get("access_token", "")

st.title("₪ לוח בקרה  |  Dashboard")

# ── Currency rates ────────────────────────────────────────────────────────────
st.subheader("💱 שערי מטבע  |  Currency Rates")

with st.spinner("Loading rates…"):
    try:
        rates_df, usd_ils = get_rates_df()
        rate_ok = True
    except Exception as e:
        st.error(f"Could not load rates: {e}")
        rate_ok = False

if rate_ok:
    st.metric("🇺🇸 USD  /  🇮🇱 ILS", f"₪ {usd_ils:.4f}")
    col_usd, col_ils = st.columns(2)
    with col_usd:
        st.caption("vs USD")
        st.dataframe(
            rates_df[["Currency", "vs USD"]].set_index("Currency"),
            use_container_width=True,
        )
    with col_ils:
        st.caption("vs ILS")
        st.dataframe(
            rates_df[["Currency", "vs ILS"]].set_index("Currency"),
            use_container_width=True,
        )

st.divider()

# ── Indices + AI Summary ──────────────────────────────────────────────────────
col_indices, col_ai = st.columns([3, 2])

with col_indices:
    st.subheader("📈 מניות בורסה  |  Market Indices")
    with st.spinner("Fetching indices…"):
        indices_df = get_indices_df()

    if indices_df.empty:
        st.info("No index data available right now.")
    else:
        # Colour-code Change %
        def _colour(val):
            if val > 0:  return "color: #22c55e"
            if val < 0:  return "color: #ef4444"
            return "color: #94a3b8"

        styled = (
            indices_df.style
            .applymap(_colour, subset=["Change", "Change %"])
            .format({"Price": "{:,.2f}", "Change": "{:+.2f}", "Change %": "{:+.2f}%"})
        )
        st.dataframe(styled, use_container_width=True, hide_index=True)

        fig = px.bar(
            indices_df,
            x="Index", y="Change %",
            color="Change %",
            color_continuous_scale=["#ef4444", "#94a3b8", "#22c55e"],
            title="Daily Change %",
        )
        fig.update_layout(showlegend=False, height=280, margin=dict(t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

with col_ai:
    st.subheader("🤖 סיכום שוק  |  AI Summary")
    if st.button("✨ Generate AI Summary", type="primary", use_container_width=True):
        with st.spinner("Two AI agents are analysing the market…"):
            mkt_str = indices_df.to_string() if not indices_df.empty else "No data"
            cur_str = rates_df[["Code", "vs USD", "vs ILS"]].to_string() if rate_ok else "No data"
            st.session_state["ai_summary"] = get_market_summary(mkt_str, cur_str)

    if "ai_summary" in st.session_state:
        st.info(st.session_state["ai_summary"])
    else:
        st.caption("Click the button above to run the AI agents and get a market summary.")
