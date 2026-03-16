"""
Trading mode toggle — Beginner / Pro.
Renders in the sidebar. Persists to session_state and updates profiles via Supabase.
"""

import streamlit as st
from services.supabase_client import update_profile

_OPTIONS = ["🌱 Simple / פשוט", "⚡ Pro / מקצועי"]
_MODE_MAP = {"🌱 Simple / פשוט": "beginner", "⚡ Pro / מקצועי": "pro"}
_REVERSE_MAP = {"beginner": "🌱 Simple / פשוט", "pro": "⚡ Pro / מקצועי"}


def render_mode_toggle() -> str:
    """
    Renders the mode radio in the sidebar.
    Returns the current mode string: 'beginner' or 'pro'.
    """
    current_mode = st.session_state.get("trading_mode", "beginner")
    current_label = _REVERSE_MAP.get(current_mode, _OPTIONS[0])

    selected = st.sidebar.radio(
        "Trading Mode",
        options=_OPTIONS,
        index=_OPTIONS.index(current_label),
        key="mode_radio",
    )

    new_mode = _MODE_MAP[selected]

    if new_mode != current_mode:
        st.session_state["trading_mode"] = new_mode
        token = st.session_state.get("access_token")
        user_id = st.session_state.get("user_id")
        if token and user_id:
            update_profile(token, user_id, {"trading_mode": new_mode})
        st.rerun()

    return new_mode
