"""
Profile — edit display name, language, phone, toggles, mode, and password.
"""

import streamlit as st

st.set_page_config(page_title="Profile — Shekel-Watch", page_icon="👤", layout="wide")

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from services.supabase_client import get_profile, update_profile, reset_password, update_password
from services.formatters import mode_label

if not require_auth():
    st.stop()

with st.sidebar:
    st.markdown("## 📊 Shekel-Watch")
    st.divider()
    render_mode_toggle()
    st.divider()
    render_sidebar_user()

# ─────────────────────────────────────────────────────────────────────────────
st.title("👤 Profile & Settings")

token = st.session_state["access_token"]
user_id = st.session_state["user_id"]
email = st.session_state.get("user_email", "")

# Refresh profile from DB
profile = get_profile(token, user_id)
if not profile:
    st.error("Could not load profile. Please try refreshing.")
    st.stop()

st.caption(f"Account: **{email}**")
st.divider()

# ── Profile form ──────────────────────────────────────────────────────────────
st.subheader("Personal Details")

with st.form("profile_form"):
    display_name = st.text_input(
        "Display Name",
        value=profile.get("display_name", ""),
        placeholder="Your name",
    )

    lang_options = {"en": "English", "he": "עברית (Hebrew)"}
    current_lang = profile.get("language", "en")
    language = st.radio(
        "Preferred Language",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(current_lang) if current_lang in lang_options else 0,
        horizontal=True,
    )

    phone = st.text_input(
        "Phone Number (for WhatsApp alerts)",
        value=profile.get("phone_number", ""),
        placeholder="+972501234567",
    )

    st.markdown("---")
    st.markdown("**Notifications**")

    whatsapp_enabled = st.toggle(
        "📱 Enable WhatsApp Alerts",
        value=bool(profile.get("whatsapp_enabled", False)),
        help="Receive arbitrage and volatility alerts via WhatsApp",
    )
    morning_enabled = st.toggle(
        "🌅 Morning Market Summary (06:00 UTC, Mon–Fri)",
        value=bool(profile.get("morning_summary_enabled", False)),
        help="Daily AI-powered market summary sent to your WhatsApp",
    )

    st.markdown("---")
    st.markdown("**Trading Mode**")
    mode_options = {"beginner": "🌱 Beginner / פשוט", "pro": "⚡ Pro / מקצועי"}
    current_mode = profile.get("trading_mode", "beginner") or "beginner"
    trading_mode = st.radio(
        "Mode",
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        index=list(mode_options.keys()).index(current_mode) if current_mode in mode_options else 0,
        horizontal=True,
    )

    save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)

if save_btn:
    updates = {
        "display_name": display_name.strip(),
        "language": language,
        "phone_number": phone.strip(),
        "whatsapp_enabled": whatsapp_enabled,
        "morning_summary_enabled": morning_enabled,
        "trading_mode": trading_mode,
    }
    result = update_profile(token, user_id, updates)
    if result["success"]:
        st.session_state["trading_mode"] = trading_mode
        st.session_state["language"] = language
        st.success("✅ Profile saved successfully.")
        st.rerun()
    else:
        st.error(f"Failed to save: {result.get('error', 'Unknown error')}")

st.divider()

# ── Change password ───────────────────────────────────────────────────────────
st.subheader("🔑 Change Password")

tab_reset, tab_change = st.tabs(["Send Reset Email", "Change Now"])

with tab_reset:
    st.markdown(f"We'll send a password reset link to **{email}**.")
    if st.button("Send Password Reset Email", use_container_width=True):
        result = reset_password(email)
        if result["success"]:
            st.success("Reset email sent! Check your inbox.")
        else:
            st.error(f"Failed: {result.get('error', 'Unknown error')}")

with tab_change:
    with st.form("change_password_form"):
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")
        change_btn = st.form_submit_button("Update Password", use_container_width=True)

    if change_btn:
        if new_pass != confirm_pass:
            st.error("Passwords do not match.")
        elif len(new_pass) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            result = update_password(token, new_pass)
            if result["success"]:
                st.success("✅ Password updated successfully.")
            else:
                st.error(f"Failed: {result.get('error', 'Unknown error')}")

st.divider()

# ── Danger zone ───────────────────────────────────────────────────────────────
with st.expander("⚠️ Danger Zone", expanded=False):
    st.warning("The following actions cannot be undone.")
    if st.button("🚪 Logout from all devices", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
