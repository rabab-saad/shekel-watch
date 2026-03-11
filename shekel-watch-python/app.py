import streamlit as st
from services.supabase_service import sign_in, sign_up

st.set_page_config(
    page_title="Shekel-Watch ₪",
    page_icon="₪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Already logged in → jump to dashboard
if st.session_state.get("user"):
    st.switch_page("pages/1_Dashboard.py")

st.title("₪ Shekel-Watch")
st.caption("Israeli Market Intelligence Dashboard")
st.divider()

tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

with tab_login:
    with st.form("login_form"):
        email    = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
    if submitted:
        if not email or not password:
            st.error("Please enter email and password.")
        else:
            with st.spinner("Signing in…"):
                result = sign_in(email, password)
            if result["success"]:
                st.session_state["user"]         = result["user"]
                st.session_state["access_token"] = result["access_token"]
                st.rerun()
            else:
                st.error(result["error"])

with tab_signup:
    with st.form("signup_form"):
        s_name     = st.text_input("Display Name")
        s_email    = st.text_input("Email", key="s_email")
        s_password = st.text_input("Password", type="password", key="s_pw")
        s_submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
    if s_submitted:
        if not s_email or not s_password:
            st.error("Email and password are required.")
        else:
            with st.spinner("Creating account…"):
                result = sign_up(s_email, s_password, s_name)
            if result["success"]:
                st.success("Account created! Check your email to confirm, then sign in.")
            else:
                st.error(result["error"])
