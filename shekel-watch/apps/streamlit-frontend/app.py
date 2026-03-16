"""
Shekel-Watch — Streamlit entry point.
Handles auth gate and onboarding redirect.
"""

import streamlit as st

st.set_page_config(
    page_title="Shekel-Watch",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from onboarding import render_onboarding


def main():
    # ── Auth gate ─────────────────────────────────────────────────────────────
    if not require_auth():
        st.stop()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 📊 Shekel-Watch")
        st.divider()
        render_mode_toggle()
        st.divider()
        render_sidebar_user()

    # ── Onboarding gate ───────────────────────────────────────────────────────
    trading_mode = st.session_state.get("trading_mode")
    if not trading_mode:
        render_onboarding()
        st.stop()

    # ── Home screen (redirect hint) ───────────────────────────────────────────
    st.title("📊 Shekel-Watch")
    st.markdown(
        "Israeli market intelligence platform — USD/ILS rates, TASE stocks, "
        "arbitrage detection, and AI-powered summaries."
    )
    st.info("👈 Use the sidebar to navigate to Dashboard, Paper Trading, Arbitrage Scanner, and more.")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📈 Dashboard", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")
    with col2:
        if st.button("💹 Paper Trading", use_container_width=True):
            st.switch_page("pages/2_Paper_Trading.py")
    with col3:
        if st.button("🔍 Arbitrage Scanner", use_container_width=True):
            st.switch_page("pages/3_Arbitrage_Scanner.py")


if __name__ == "__main__":
    main()
