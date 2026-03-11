import streamlit as st
from services.supabase_service import get_profile, get_watchlist

st.set_page_config(page_title="Profile | Shekel-Watch", page_icon="⚙️", layout="wide")

# ── Auth guard ────────────────────────────────────────────────────────────────
if not st.session_state.get("user"):
    st.warning("Please sign in first.")
    st.page_link("app.py", label="← Go to Login")
    st.stop()

user  = st.session_state["user"]
token = st.session_state.get("access_token", "")

st.title("⚙️ פרופיל  |  Profile")

profile   = get_profile(token, user.id)
watchlist = get_watchlist(token, user.id)

col_info, col_stats = st.columns(2)

with col_info:
    st.subheader("Account Info")
    st.write(f"**Email:** {user.email}")
    st.write(f"**Display name:** {profile.get('display_name') or '—'}")
    st.write(f"**Language:** {profile.get('language', 'en').upper()}")
    st.write(f"**Phone:** {profile.get('phone_number') or '—'}")

with col_stats:
    st.subheader("Stats")
    st.metric("Stocks in watchlist", len(watchlist))

st.divider()

if st.button("🚪 Sign Out", type="secondary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
