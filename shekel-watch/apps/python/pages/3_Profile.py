import streamlit as st
from services.supabase_service import get_profile, get_watchlist, update_profile
from services.whatsapp_service import send_whatsapp

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
    current_phone = profile.get("phone_number") or ""
    st.write(f"**WhatsApp:** {current_phone if current_phone else '—'}")

with col_stats:
    st.subheader("Stats")
    st.metric("Stocks in watchlist", len(watchlist))

st.divider()

# ── WhatsApp Settings ─────────────────────────────────────────────────────────
st.subheader("📱 WhatsApp Alerts")
st.caption(
    "Enter your WhatsApp number to receive alerts when arbitrage opportunities are detected. "
    "Israeli numbers: e.g. 0501234567 or +972501234567"
)

with st.form("phone_form"):
    new_phone = st.text_input(
        "WhatsApp number",
        value=current_phone,
        placeholder="+972501234567",
    )
    whatsapp_enabled = st.checkbox(
        "Enable WhatsApp alerts",
        value=bool(profile.get("whatsapp_enabled", False)),
    )
    save = st.form_submit_button("Save", type="primary")

if save:
    res = update_profile(token, user.id, {
        "phone_number":     new_phone.strip() or None,
        "whatsapp_enabled": whatsapp_enabled,
    })
    if res["success"]:
        st.success("Profile updated!")
        st.rerun()
    else:
        st.error(res.get("error", "Could not update profile"))

# ── Send test message ─────────────────────────────────────────────────────────
if current_phone and profile.get("whatsapp_enabled"):
    st.divider()
    st.subheader("🧪 Test Alert")
    if st.button("Send test WhatsApp message", use_container_width=True):
        with st.spinner("Sending…"):
            res = send_whatsapp(
                current_phone,
                "✅ Shekel-Watch connected!\nYou will now receive arbitrage alerts on this number.",
            )
        if res["success"]:
            st.success("Test message sent! Check your WhatsApp.")
        else:
            st.error(f"Failed: {res.get('error')}")
else:
    st.info("Save your WhatsApp number and enable alerts to activate notifications.")

st.divider()

if st.button("🚪 Sign Out", type="secondary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
