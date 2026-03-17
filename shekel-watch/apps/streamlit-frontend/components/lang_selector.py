"""
Language selector widget — renders in the sidebar.
Shows a compact selectbox: EN | עב | عر
Saves the selection to session state and the user's DB profile.
"""

import streamlit as st
from services.supabase_client import update_profile

_LANG_OPTIONS = {"en": "🌐 EN", "he": "🇮🇱 עב", "ar": "🇸🇦 عر"}
_LANG_KEYS = list(_LANG_OPTIONS.keys())


def render_lang_selector() -> None:
    """Render the language selector in the sidebar."""
    current = st.session_state.get("language", "en")
    if current not in _LANG_KEYS:
        current = "en"

    selected = st.sidebar.selectbox(
        "🌐",
        options=_LANG_KEYS,
        index=_LANG_KEYS.index(current),
        format_func=lambda x: _LANG_OPTIONS[x],
        key="lang_selector",
        label_visibility="collapsed",
    )

    if selected != current:
        st.session_state["language"] = selected
        token  = st.session_state.get("access_token")
        uid    = st.session_state.get("user_id")
        if token and uid:
            update_profile(token, uid, {"language": selected})
        st.rerun()
