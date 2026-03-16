"""
TASE market phase timer component.
Shows current phase (Hebrew + English) and static "as-of" time.
"""

import streamlit as st
from datetime import datetime, date, time
import pytz

IST = pytz.timezone("Asia/Jerusalem")

# Hardcoded TASE holidays 2025 (YYYY-MM-DD)
TASE_HOLIDAYS_2025 = {
    date(2025, 1, 1),   # New Year (observed)
    date(2025, 3, 13),  # Purim
    date(2025, 4, 13),  # Passover Eve
    date(2025, 4, 14),  # Passover I
    date(2025, 4, 20),  # Passover VII
    date(2025, 4, 30),  # Independence Day (Israel)
    date(2025, 6, 1),   # Shavuot Eve
    date(2025, 6, 2),   # Shavuot
    date(2025, 9, 22),  # Rosh Hashana I
    date(2025, 9, 23),  # Rosh Hashana II
    date(2025, 10, 1),  # Yom Kippur Eve
    date(2025, 10, 2),  # Yom Kippur
    date(2025, 10, 6),  # Sukkot Eve
    date(2025, 10, 7),  # Sukkot I
    date(2025, 10, 13), # Sukkot VII (Hoshana Raba)
    date(2025, 10, 14), # Shemini Atzeret / Simchat Torah
}

# Phase schedule (IST, 24h)
PHASES = [
    ("Pre-Open / טרום פתיחה",    time(8, 45),  time(9, 59),  "info"),
    ("Continuous / מסחר רציף",   time(10, 0),  time(17, 14), "success"),
    ("Pre-Close / טרום סגירה",   time(17, 15), time(17, 24), "warning"),
    ("Closing Auction / מכרז סגירה", time(17, 25), time(17, 30), "error"),
]

CLOSED_LABEL = "Closed / סגור"


def _is_friday_short_day(today: date) -> bool:
    return today.weekday() == 4  # Friday (0=Mon)


def _is_trading_day(today: date) -> bool:
    # TASE trades Sun–Thu (weekday 6=Sun, 0=Mon, ..., 3=Thu)
    if today in TASE_HOLIDAYS_2025:
        return False
    dow = today.weekday()
    # Python: Mon=0 Sun=6. TASE: Sun–Thu = weekday 6,0,1,2,3
    return dow in (0, 1, 2, 3, 6)  # Mon–Thu + Sun


def get_current_phase() -> tuple[str, str]:
    """
    Returns (phase_label, alert_type) for the current IST time.
    alert_type is one of: 'info', 'success', 'warning', 'error', 'closed'
    """
    now_ist = datetime.now(IST)
    today = now_ist.date()
    now_time = now_ist.time()

    if not _is_trading_day(today):
        return (CLOSED_LABEL, "closed")

    # Friday early close at 13:30
    if _is_friday_short_day(today):
        if now_time >= time(13, 30):
            return (CLOSED_LABEL, "closed")
        # Only Pre-Open and Continuous phases exist on Friday
        if time(8, 45) <= now_time < time(9, 59):
            return ("Pre-Open / טרום פתיחה", "info")
        if time(10, 0) <= now_time < time(13, 30):
            return ("Continuous / מסחר רציף", "success")
        return (CLOSED_LABEL, "closed")

    for label, start, end, alert_type in PHASES:
        if start <= now_time <= end:
            return (label, alert_type)

    return (CLOSED_LABEL, "closed")


def render_phase_timer():
    """Render the market phase badge with a manual refresh button."""
    now_ist = datetime.now(IST)
    phase_label, alert_type = get_current_phase()

    time_str = now_ist.strftime("%H:%M:%S IST")

    col1, col2 = st.columns([4, 1])
    with col1:
        if alert_type == "success":
            st.success(f"🟢 **{phase_label}** — as of {time_str}")
        elif alert_type == "info":
            st.info(f"🔵 **{phase_label}** — as of {time_str}")
        elif alert_type == "warning":
            st.warning(f"🟡 **{phase_label}** — as of {time_str}")
        elif alert_type == "error":
            st.error(f"🔴 **{phase_label}** — as of {time_str}")
        else:
            st.info(f"⚫ **{phase_label}** — as of {time_str}")
    with col2:
        if st.button("↻ Refresh", key="phase_refresh"):
            st.rerun()
