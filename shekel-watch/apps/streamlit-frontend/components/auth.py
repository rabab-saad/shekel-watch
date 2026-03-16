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
            st.error(f"Google sign-in failed: {result.get('error', 'Unknown error')}")
            return False

    if st.session_state.get("access_token"):
        return True

    render_login()
    return False


def render_login():
    """Full-page login / signup form with Google OAuth button."""
    st.markdown(
        "<h1 style='text-align:center;'>📊 Shekel-Watch</h1>"
        "<p style='text-align:center;color:#94a3b8;'>Israeli Market Intelligence Platform</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Google Sign-In button ─────────────────────────────────────────────────
    col_l, col_mid, col_r = st.columns([1, 2, 1])
    with col_mid:
        if st.button("🔵  Sign in with Google", use_container_width=True):
            result = get_google_oauth_url(_APP_URL)
            if result["success"]:
                # Redirect the browser to Google's consent screen
                st.markdown(
                    f'<meta http-equiv="refresh" content="0; url={result["url"]}">',
                    unsafe_allow_html=True,
                )
                st.info("Redirecting to Google… if nothing happens, [click here](%s)." % result["url"])
                st.stop()
            else:
                st.error(f"Could not start Google login: {result.get('error')}")

    st.markdown("<p style='text-align:center;color:#64748b;'>— or use email —</p>", unsafe_allow_html=True)

    tab_login, tab_signup, tab_magic = st.tabs(["Sign In", "Sign Up", "Magic Link"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please enter email and password.")
            else:
                with st.spinner("Signing in…"):
                    result = sign_in(email, password)
                if result["success"]:
                    _save_session(result)
                    st.rerun()
                else:
                    st.error(f"Login failed: {result.get('error', 'Unknown error')}")

    with tab_signup:
        with st.form("signup_form"):
            su_name = st.text_input("Display Name", placeholder="Your name")
            su_email = st.text_input("Email", placeholder="you@example.com", key="su_email")
            su_pass = st.text_input("Password", type="password", key="su_pass")
            su_pass2 = st.text_input("Confirm Password", type="password", key="su_pass2")
            su_submitted = st.form_submit_button("Create Account", use_container_width=True)

        if su_submitted:
            if su_pass != su_pass2:
                st.error("Passwords do not match.")
            elif len(su_pass) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                with st.spinner("Creating account…"):
                    result = sign_up(su_email, su_pass, su_name)
                if result["success"]:
                    st.success("Account created! Please check your email to confirm, then sign in.")
                else:
                    st.error(f"Sign-up failed: {result.get('error', 'Unknown error')}")

    with tab_magic:
        with st.form("magic_form"):
            ml_email = st.text_input("Email", placeholder="you@example.com", key="ml_email")
            ml_submitted = st.form_submit_button("Send Magic Link", use_container_width=True)

        if ml_submitted:
            result = sign_in_magic_link(ml_email)
            if result["success"]:
                st.success("Magic link sent! Check your email.")
            else:
                st.error(f"Failed: {result.get('error', 'Unknown error')}")


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
    mode = st.session_state.get("trading_mode", "")
    mode_icon = "🌱" if mode == "beginner" else "⚡" if mode == "pro" else ""

    st.sidebar.markdown(f"**{email}** {mode_icon}")
    if st.sidebar.button("Logout", use_container_width=True):
        logout()
