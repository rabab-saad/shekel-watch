"""
3-step onboarding wizard.
Called from app.py when profiles.trading_mode is NULL.
"""

import streamlit as st
from services.supabase_client import update_profile, upsert_virtual_balance, add_to_watchlist
from utils.i18n import t, inject_dir


def render_onboarding():
    """
    Runs the onboarding wizard inline.
    Uses st.session_state['onboarding_step'] to track progress.
    """
    inject_dir()

    if "onboarding_step" not in st.session_state:
        st.session_state["onboarding_step"] = 1

    step = st.session_state["onboarding_step"]

    st.markdown(
        f"<h2 style='text-align:center;'>{t('onboarding_welcome')}</h2>"
        f"<p style='text-align:center;color:#94a3b8;'>{t('onboarding_subtitle')}</p>",
        unsafe_allow_html=True,
    )
    st.progress(step / 3, text=t("step_progress").format(step=step))
    st.divider()

    if step == 1:
        _step1()
    elif step == 2:
        _step2()
    elif step == 3:
        _step3()


def _step1():
    """Step 1: Choose trading mode."""
    st.markdown(t("step1_title"))
    st.markdown(t("step1_subtitle"))
    st.markdown("")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown(t("beginner_card_title"))
            st.markdown(t("beginner_card_desc"))
            if st.button(t("choose_beginner"), use_container_width=True, key="choose_beginner"):
                st.session_state["selected_mode"] = "beginner"
                st.session_state["onboarding_step"] = 2
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown(t("pro_card_title"))
            st.markdown(t("pro_card_desc"))
            if st.button(t("choose_pro"), use_container_width=True, key="choose_pro"):
                st.session_state["selected_mode"] = "pro"
                st.session_state["onboarding_step"] = 2
                st.rerun()


def _step2():
    """Step 2A (Beginner) or 2B (Pro)."""
    mode = st.session_state.get("selected_mode", "beginner")
    token = st.session_state["access_token"]
    user_id = st.session_state["user_id"]

    if mode == "beginner":
        st.markdown(t("step2_beginner_title"))
        st.info(t("step2_beginner_desc"))
        col1, col2 = st.columns([2, 1])
        with col1:
            st.metric(t("starting_balance"), "₪100,000", help="You can practice trades risk-free")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t("setup_account_btn"), use_container_width=True):
                with st.spinner(t("setting_up_balance")):
                    upsert_virtual_balance(token, user_id, 100000)
                st.session_state["onboarding_step"] = 3
                st.rerun()

    else:  # pro
        st.markdown(t("step2_pro_title"))
        st.markdown(t("step2_pro_desc"))
        tickers_input = st.text_area(
            t("tickers_label"),
            placeholder=t("tickers_placeholder"),
            height=80,
        )
        col1, col2 = st.columns([1, 2])
        with col2:
            if st.button(t("save_watchlist_btn"), use_container_width=True):
                tickers = [tk.strip().upper() for tk in tickers_input.split(",") if tk.strip()]
                if not tickers:
                    st.warning(t("please_enter_one_ticker"))
                else:
                    with st.spinner(t("adding_tickers").format(n=len(tickers))):
                        for ticker in tickers:
                            market = "TASE" if ticker.endswith(".TA") else "NYSE"
                            add_to_watchlist(token, user_id, ticker, market)
                    st.session_state["onboarding_step"] = 3
                    st.rerun()
        with col1:
            if st.button(t("skip_for_now"), use_container_width=True):
                st.session_state["onboarding_step"] = 3
                st.rerun()


def _step3():
    """Step 3: Phone / WhatsApp opt-in."""
    st.markdown(t("step3_title"))
    st.markdown(t("step3_desc"))

    mode = st.session_state.get("selected_mode", "beginner")
    token = st.session_state["access_token"]
    user_id = st.session_state["user_id"]

    phone = st.text_input(
        t("phone_optional"),
        placeholder=t("phone_placeholder"),
        help=t("phone_help"),
    )
    whatsapp_enabled = st.toggle(t("enable_whatsapp_onboarding"), value=True)
    lang_options = {
        t("lang_en"): "en",
        t("lang_he"): "he",
        t("lang_ar"): "ar",
    }
    lang_label = st.radio(
        t("preferred_language_onboarding"),
        list(lang_options.keys()),
        horizontal=True,
    )
    lang_code = lang_options[lang_label]

    col1, col2 = st.columns([1, 2])
    with col2:
        if st.button(t("finish_setup"), use_container_width=True):
            updates = {
                "trading_mode": mode,
                "language": lang_code,
                "whatsapp_enabled": whatsapp_enabled,
                "morning_summary_enabled": whatsapp_enabled,
            }
            if phone.strip():
                updates["phone_number"] = phone.strip()

            with st.spinner(t("saving_prefs")):
                update_profile(token, user_id, updates)

            st.session_state["trading_mode"] = mode
            st.session_state["language"] = lang_code
            st.session_state.pop("onboarding_step", None)
            st.session_state.pop("selected_mode", None)
            st.success(t("all_set"))
            st.switch_page("pages/1_Dashboard.py")

    with col1:
        if st.button(t("skip"), use_container_width=True):
            updates = {"trading_mode": mode}
            update_profile(token, user_id, updates)
            st.session_state["trading_mode"] = mode
            st.session_state.pop("onboarding_step", None)
            st.session_state.pop("selected_mode", None)
            st.switch_page("pages/1_Dashboard.py")
