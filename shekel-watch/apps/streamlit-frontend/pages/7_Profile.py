"""
Profile — edit display name, language, phone, toggles, mode, and password.
"""

import streamlit as st

st.set_page_config(page_title="Profile — Shekel-Watch", page_icon="👤", layout="wide")

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from components.lang_selector import render_lang_selector
from services.supabase_client import get_profile, update_profile, reset_password, update_password
from services.formatters import mode_label
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
st.title(t("profile_title"))

token = st.session_state["access_token"]
user_id = st.session_state["user_id"]
email = st.session_state.get("user_email", "")

# Refresh profile from DB
profile = get_profile(token, user_id)
if not profile:
    st.error(t("could_not_load_profile"))
    st.stop()

st.caption(t("account").format(email=email))
st.divider()

# ── Profile form ──────────────────────────────────────────────────────────────
st.subheader(t("personal_details"))

with st.form("profile_form"):
    display_name = st.text_input(
        t("display_name"),
        value=profile.get("display_name", ""),
        placeholder=t("display_name_placeholder"),
    )

    lang_options = {
        "en": t("lang_en"),
        "he": t("lang_he"),
        "ar": t("lang_ar"),
    }
    current_lang = profile.get("language", "en")
    language = st.radio(
        t("preferred_language"),
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(current_lang) if current_lang in lang_options else 0,
        horizontal=True,
    )

    phone = st.text_input(
        t("phone_number"),
        value=profile.get("phone_number", ""),
        placeholder=t("phone_placeholder"),
    )

    st.markdown("---")
    st.markdown(t("notifications"))

    whatsapp_enabled = st.toggle(
        t("whatsapp_alerts"),
        value=bool(profile.get("whatsapp_enabled", False)),
        help=t("whatsapp_help"),
    )
    morning_enabled = st.toggle(
        t("morning_summary_toggle"),
        value=bool(profile.get("morning_summary_enabled", False)),
        help=t("morning_help"),
    )

    st.markdown("---")
    st.markdown(t("trading_mode_label"))
    mode_options = {
        "beginner": t("mode_beginner"),
        "pro":      t("mode_pro"),
    }
    current_mode = profile.get("trading_mode", "beginner") or "beginner"
    trading_mode = st.radio(
        t("mode_label"),
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        index=list(mode_options.keys()).index(current_mode) if current_mode in mode_options else 0,
        horizontal=True,
    )

    save_btn = st.form_submit_button(t("save_changes"), use_container_width=True)

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
        st.success(t("profile_saved"))
        st.rerun()
    else:
        st.error(t("failed_to_save_profile").format(error=result.get("error", "Unknown error")))

st.divider()

# ── Change password ───────────────────────────────────────────────────────────
st.subheader(t("change_password"))

tab_reset, tab_change = st.tabs([t("send_reset_email_tab"), t("change_now_tab")])

with tab_reset:
    st.markdown(t("reset_email_desc").format(email=email))
    if st.button(t("send_reset_btn"), use_container_width=True):
        result = reset_password(email)
        if result["success"]:
            st.success(t("reset_sent"))
        else:
            st.error(t("reset_failed").format(error=result.get("error", "Unknown error")))

with tab_change:
    with st.form("change_password_form"):
        new_pass = st.text_input(t("new_password"), type="password")
        confirm_pass = st.text_input(t("confirm_new_password"), type="password")
        change_btn = st.form_submit_button(t("update_password_btn"), use_container_width=True)

    if change_btn:
        if new_pass != confirm_pass:
            st.error(t("passwords_no_match"))
        elif len(new_pass) < 8:
            st.error(t("password_too_short"))
        else:
            result = update_password(token, new_pass)
            if result["success"]:
                st.success(t("password_updated"))
            else:
                st.error(t("reset_failed").format(error=result.get("error", "Unknown error")))

st.divider()

# ── Danger zone ───────────────────────────────────────────────────────────────
with st.expander(t("danger_zone"), expanded=False):
    st.warning(t("danger_warning"))
    if st.button(t("logout_all_devices"), use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
