"""
Trading mode toggle — Beginner / Pro.
Renders in the sidebar. Persists to session_state and updates profiles via Supabase.
"""

import streamlit as st
from services.supabase_client import update_profile


def render_mode_toggle() -> str:
    """
    Renders the mode radio in the sidebar.
    Returns the current mode string: 'beginner' or 'pro'.
    """
    from utils.i18n import t

    options_map   = {"beginner": t("mode_beginner"), "pro": t("mode_pro")}
    display_opts  = list(options_map.values())
    reverse_map   = {v: k for k, v in options_map.items()}

    current_mode  = st.session_state.get("trading_mode", "beginner")
    current_label = options_map.get(current_mode, display_opts[0])

    selected = st.sidebar.radio(
        t("trading_mode"),
        options=display_opts,
        index=display_opts.index(current_label) if current_label in display_opts else 0,
        key="mode_radio",
    )

    new_mode = reverse_map.get(selected, "beginner")

    if new_mode != current_mode:
        st.session_state["trading_mode"] = new_mode
        token   = st.session_state.get("access_token")
        user_id = st.session_state.get("user_id")
        if token and user_id:
            update_profile(token, user_id, {"trading_mode": new_mode})
        st.rerun()

    return new_mode
