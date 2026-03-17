"""
Auth component — login form, session management, auth gate.
Supports email/password, magic link, and Google OAuth (PKCE flow).
"""

import os
import streamlit as st
from services.supabase_client import (
    sign_in, sign_up, sign_in_magic_link, get_profile,
    get_google_oauth_url, exchange_oauth_code,
)
from utils.i18n import t, inject_dir

# The public URL of this Streamlit app — used as the OAuth redirect target.
# Set APP_URL in environment (same as your Railway Streamlit domain).
# Falls back to localhost for local development.
_APP_URL = os.environ.get("APP_URL", "http://localhost:8501")


def require_auth() -> bool:
    """
    Call at the top of every page.
    1. Checks for a ?code= query param (Google OAuth return) and exchanges it.
    2. Returns True if already authenticated.
    3. Otherwise renders the login form and returns False.
    """
    # ── Handle Google OAuth return ────────────────────────────────────────────
    code = st.query_params.get("code")
    if code and not st.session_state.get("access_token"):
        with st.spinner("Completing Google sign-in…"):
            result = exchange_oauth_code(code)
        # Clear the code from the URL immediately
        st.query_params.clear()
        if result["success"]:
            _save_session(result)
            st.rerun()
        else:
            st.error(t("google_signin_failed").format(error=result.get("error", "")))
            return False

    if st.session_state.get("access_token"):
        return True

    render_login()
    return False


def render_login():
    """Full-page login / signup form with Google OAuth button."""
    inject_dir()
    st.markdown(
        f"<h1 style='text-align:center;'>📊 {t('app_name')}</h1>"
        f"<p style='text-align:center;color:#94a3b8;'>{t('app_tagline')}</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Google Sign-In button ─────────────────────────────────────────────────
    col_l, col_mid, col_r = st.columns([1, 2, 1])
    with col_mid:
        if st.button(t("sign_in_google"), use_container_width=True):
            result = get_google_oauth_url(_APP_URL)
            if result["success"]:
                st.markdown(
                    f'<meta http-equiv="refresh" content="0; url={result["url"]}">',
                    unsafe_allow_html=True,
                )
                st.info(t("redirecting_google").format(url=result["url"]))
                st.stop()
            else:
                st.error(t("google_login_failed").format(error=result.get("error")))

    st.markdown(
        f"<p style='text-align:center;color:#64748b;'>{t('or_use_email')}</p>",
        unsafe_allow_html=True,
    )

    tab_login, tab_signup, tab_magic = st.tabs([t("sign_in"), t("sign_up"), t("magic_link")])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input(t("email"), placeholder=t("email_placeholder"))
            password = st.text_input(t("password"), type="password")
            submitted = st.form_submit_button(t("sign_in"), use_container_width=True)

        if submitted:
            if not email or not password:
                st.error(t("enter_email_password"))
            else:
                with st.spinner(t("signing_in")):
                    result = sign_in(email, password)
                if result["success"]:
                    _save_session(result)
                    st.rerun()
                else:
                    st.error(t("login_failed").format(error=result.get("error", "")))

    with tab_signup:
        with st.form("signup_form"):
            su_name  = st.text_input(t("display_name"), placeholder=t("display_name_placeholder"))
            su_email = st.text_input(t("email"), placeholder=t("email_placeholder"), key="su_email")
            su_pass  = st.text_input(t("password"), type="password", key="su_pass")
            su_pass2 = st.text_input(t("confirm_password"), type="password", key="su_pass2")
            su_submitted = st.form_submit_button(t("create_account"), use_container_width=True)

        if su_submitted:
            if su_pass != su_pass2:
                st.error(t("passwords_no_match"))
            elif len(su_pass) < 8:
                st.error(t("password_too_short"))
            else:
                with st.spinner(t("creating_account")):
                    result = sign_up(su_email, su_pass, su_name)
                if result["success"]:
                    st.success(t("check_email_confirm"))
                else:
                    st.error(t("signup_failed").format(error=result.get("error", "")))

    with tab_magic:
        with st.form("magic_form"):
            ml_email = st.text_input(t("email"), placeholder=t("email_placeholder"), key="ml_email")
            ml_submitted = st.form_submit_button(t("send_magic_link"), use_container_width=True)

        if ml_submitted:
            result = sign_in_magic_link(ml_email)
            if result["success"]:
                st.success(t("magic_link_sent"))
            else:
                st.error(result.get("error", ""))


def _save_session(result: dict):
    """Persist auth result to session_state."""
    st.session_state["access_token"] = result["access_token"]
    st.session_state["refresh_token"] = result.get("refresh_token", "")
    st.session_state["user_id"] = result["user_id"]
    st.session_state["user_email"] = result.get("email", "")

    # Fetch trading mode from profile
    profile = get_profile(result["access_token"], result["user_id"])
    st.session_state["profile"] = profile
    st.session_state["trading_mode"] = profile.get("trading_mode")
    st.session_state["language"] = profile.get("language", "en")
    st.session_state["term_cache"] = {}


def logout():
    """Clear all session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def render_sidebar_user():
    """Render user email + logout button in sidebar."""
    email = st.session_state.get("user_email", "")
    mode  = st.session_state.get("trading_mode", "")
    mode_icon = "🌱" if mode == "beginner" else "⚡" if mode == "pro" else ""

    st.sidebar.markdown(f"**{email}** {mode_icon}")
    if st.sidebar.button(t("logout"), use_container_width=True):
        logout()
