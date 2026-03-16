"""
Risk Heatmap — colored metric grid for watchlist items by risk score.
"""

import streamlit as st

st.set_page_config(page_title="Risk Heatmap — Shekel-Watch", page_icon="🌡️", layout="wide")

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from components.term_tooltip import render_term
from services.supabase_client import get_watchlist
from services.formatters import risk_label, risk_label_he

if not require_auth():
    st.stop()

with st.sidebar:
    st.markdown("## 📊 Shekel-Watch")
    st.divider()
    render_mode_toggle()
    st.divider()
    render_sidebar_user()

# ─────────────────────────────────────────────────────────────────────────────
st.title("🌡️ Risk Heatmap")
st.caption("Risk scores for your watchlist tickers. Updated daily.")

render_term("risk score", "Risk Score")
st.divider()

token = st.session_state["access_token"]
user_id = st.session_state["user_id"]
watchlist = get_watchlist(token, user_id)

if not watchlist:
    st.info("Your watchlist is empty. Add tickers in the **Watchlist** page to see risk scores.")
    st.stop()

# ── Legend ────────────────────────────────────────────────────────────────────
with st.expander("📖 Risk Score Legend"):
    leg1, leg2, leg3 = st.columns(3)
    with leg1:
        st.success("**0–3: Low Risk / נמוך**\nStable, low volatility assets")
    with leg2:
        st.warning("**4–6: Medium Risk / בינוני**\nModerate volatility")
    with leg3:
        st.error("**7–10: High Risk / גבוה**\nHigh volatility or uncertainty")

st.divider()

# ── Grid ──────────────────────────────────────────────────────────────────────
COLS_PER_ROW = 4
items = watchlist

for row_start in range(0, len(items), COLS_PER_ROW):
    row_items = items[row_start: row_start + COLS_PER_ROW]
    cols = st.columns(COLS_PER_ROW)

    for col, item in zip(cols, row_items):
        ticker = item.get("ticker", "")
        market = item.get("market", "")
        risk = item.get("risk_score") or 0
        en_label = risk_label(risk)
        he_label = risk_label_he(risk)

        with col:
            card_content = (
                f"**{ticker}**\n\n"
                f"Risk Score: **{risk}/10**\n\n"
                f"{en_label} / {he_label}\n\n"
                f"*{market}*"
            )
            if risk <= 3:
                st.success(card_content)
            elif risk <= 6:
                st.warning(card_content)
            else:
                st.error(card_content)

# ── Summary ───────────────────────────────────────────────────────────────────
st.divider()
low_count = sum(1 for i in watchlist if (i.get("risk_score") or 0) <= 3)
med_count = sum(1 for i in watchlist if 3 < (i.get("risk_score") or 0) <= 6)
high_count = sum(1 for i in watchlist if (i.get("risk_score") or 0) > 6)

c1, c2, c3 = st.columns(3)
c1.metric("Low Risk 🟢", low_count, help="Risk score 0–3")
c2.metric("Medium Risk 🟡", med_count, help="Risk score 4–6")
c3.metric("High Risk 🔴", high_count, help="Risk score 7–10")
