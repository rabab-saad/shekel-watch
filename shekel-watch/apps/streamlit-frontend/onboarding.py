"""
3-step onboarding wizard.
Called from app.py when profiles.trading_mode is NULL.
"""

import streamlit as st
from services.supabase_client import update_profile, upsert_virtual_balance, add_to_watchlist


def render_onboarding():
    """
    Runs the onboarding wizard inline.
    Uses st.session_state['onboarding_step'] to track progress.
    """
    if "onboarding_step" not in st.session_state:
        st.session_state["onboarding_step"] = 1

    step = st.session_state["onboarding_step"]

    st.markdown(
        "<h2 style='text-align:center;'>👋 Welcome to Shekel-Watch</h2>"
        "<p style='text-align:center;color:#94a3b8;'>Let's set up your account in 3 quick steps.</p>",
        unsafe_allow_html=True,
    )
    st.progress(step / 3, text=f"Step {step} of 3")
    st.divider()

    if step == 1:
        _step1()
    elif step == 2:
        _step2()
    elif step == 3:
        _step3()


def _step1():
    """Step 1: Choose trading mode."""
    st.markdown("### Step 1 — Choose your trading style")
    st.markdown("This personalises your dashboard experience.")
    st.markdown("")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("### 🌱 משקיע מתחיל\n**Beginner Investor**")
            st.markdown(
                "- Simple metrics and plain language\n"
                "- Virtual trading with ₪100,000 sandbox\n"
                "- Daily market summary delivered to WhatsApp"
            )
            if st.button("Choose Beginner", use_container_width=True, key="choose_beginner"):
                st.session_state["selected_mode"] = "beginner"
                st.session_state["onboarding_step"] = 2
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("### ⚡ סוחר פעיל\n**Active Trader**")
            st.markdown(
                "- Full candlestick charts with RSI & MACD\n"
                "- Complete arbitrage scanner\n"
                "- Custom watchlist & real-time risk heatmap"
            )
            if st.button("Choose Pro", use_container_width=True, key="choose_pro"):
                st.session_state["selected_mode"] = "pro"
                st.session_state["onboarding_step"] = 2
                st.rerun()


def _step2():
    """Step 2A (Beginner) or 2B (Pro)."""
    mode = st.session_state.get("selected_mode", "beginner")
    token = st.session_state["access_token"]
    user_id = st.session_state["user_id"]

    if mode == "beginner":
        st.markdown("### Step 2 — Your Virtual Portfolio 🌱")
        st.info(
            "We'll create a virtual trading account with **₪100,000** for you to practice "
            "buying and selling Israeli stocks — no real money involved."
        )
        col1, col2 = st.columns([2, 1])
        with col1:
            st.metric("Starting Virtual Balance", "₪100,000", help="You can practice trades risk-free")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Set Up My Account →", use_container_width=True):
                with st.spinner("Setting up virtual balance…"):
                    upsert_virtual_balance(token, user_id, 100000)
                st.session_state["onboarding_step"] = 3
                st.rerun()

    else:  # pro
        st.markdown("### Step 2 — Build Your Watchlist ⚡")
        st.markdown(
            "Enter comma-separated tickers to track (e.g. `TEVA.TA, LUMI.TA, CHKP.TA`). "
            "You can always add or remove tickers later."
        )
        tickers_input = st.text_area(
            "Tickers (comma-separated)",
            placeholder="TEVA.TA, LUMI.TA, CHKP.TA, ESLT.TA",
            height=80,
        )
        col1, col2 = st.columns([1, 2])
        with col2:
            if st.button("Save Watchlist →", use_container_width=True):
                tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
                if not tickers:
                    st.warning("Please enter at least one ticker.")
                else:
                    with st.spinner(f"Adding {len(tickers)} tickers…"):
                        for ticker in tickers:
                            market = "TASE" if ticker.endswith(".TA") else "NYSE"
                            add_to_watchlist(token, user_id, ticker, market)
                    st.session_state["onboarding_step"] = 3
                    st.rerun()
        with col1:
            if st.button("Skip for now", use_container_width=True):
                st.session_state["onboarding_step"] = 3
                st.rerun()


def _step3():
    """Step 3: Phone / WhatsApp opt-in."""
    st.markdown("### Step 3 — WhatsApp Alerts 📱")
    st.markdown(
        "Receive a personalised morning market summary every weekday at 08:45 IST. "
        "You can always change this in your Profile settings."
    )

    mode = st.session_state.get("selected_mode", "beginner")
    token = st.session_state["access_token"]
    user_id = st.session_state["user_id"]

    phone = st.text_input(
        "Phone Number (optional)",
        placeholder="+972501234567",
        help="Israeli format: +972-50-xxx-xxxx",
    )
    whatsapp_enabled = st.toggle("Enable WhatsApp morning summary", value=True)
    lang = st.radio("Preferred language", ["English", "Hebrew"], horizontal=True)

    col1, col2 = st.columns([1, 2])
    with col2:
        if st.button("Finish Setup 🎉", use_container_width=True):
            updates = {
                "trading_mode": mode,
                "language": "he" if lang == "Hebrew" else "en",
                "whatsapp_enabled": whatsapp_enabled,
                "morning_summary_enabled": whatsapp_enabled,
            }
            if phone.strip():
                updates["phone_number"] = phone.strip()

            with st.spinner("Saving your preferences…"):
                update_profile(token, user_id, updates)

            st.session_state["trading_mode"] = mode
            st.session_state["language"] = updates["language"]
            st.session_state.pop("onboarding_step", None)
            st.session_state.pop("selected_mode", None)
            st.success("All set! Redirecting to your dashboard…")
            st.switch_page("pages/1_Dashboard.py")

    with col1:
        if st.button("Skip", use_container_width=True):
            updates = {"trading_mode": mode}
            update_profile(token, user_id, updates)
            st.session_state["trading_mode"] = mode
            st.session_state.pop("onboarding_step", None)
            st.session_state.pop("selected_mode", None)
            st.switch_page("pages/1_Dashboard.py")
