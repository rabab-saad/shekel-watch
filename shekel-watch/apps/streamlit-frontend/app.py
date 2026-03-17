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
from components.lang_selector import render_lang_selector
from onboarding import render_onboarding
from utils.i18n import t, inject_dir


def main():
    # ── Auth gate ─────────────────────────────────────────────────────────────
    if not require_auth():
        st.stop()

    inject_dir()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(t("sidebar_title"))
        st.divider()
        render_lang_selector()
        render_mode_toggle()
        st.divider()
        render_sidebar_user()

    # ── Onboarding gate ───────────────────────────────────────────────────────
    trading_mode = st.session_state.get("trading_mode")
    if not trading_mode:
        render_onboarding()
        st.stop()

    # ── Home screen (redirect hint) ───────────────────────────────────────────
    st.title(t("home_title"))
    st.markdown(t("home_desc"))
    st.info(t("home_hint"))

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(t("btn_dashboard"), use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")
    with col2:
        if st.button(t("btn_paper_trading"), use_container_width=True):
            st.switch_page("pages/2_Paper_Trading.py")
    with col3:
        if st.button(t("btn_arbitrage"), use_container_width=True):
            st.switch_page("pages/3_Arbitrage_Scanner.py")


if __name__ == "__main__":
    main()
