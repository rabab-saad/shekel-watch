"""
Arbitrage Scanner — dual-listed stock gaps between TASE and NYSE.
Pro mode: full table. Beginner mode: top 3 with plain language.
Auto-refreshes every 60 seconds.
"""

import time
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Arbitrage Scanner — Shekel-Watch", page_icon="🔍", layout="wide")

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from components.lang_selector import render_lang_selector
from components.term_tooltip import render_term
from services.api_client import APIClient, APIError
from services.formatters import arb_direction_label
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
st.title(t("arbitrage_title"))
st.caption(t("arbitrage_caption"))

render_term("arbitrage", t("what_is_arbitrage"))

client = APIClient()
mode = st.session_state.get("trading_mode", "beginner")

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if "arb_last_refresh" not in st.session_state:
    st.session_state["arb_last_refresh"] = time.time()

elapsed = time.time() - st.session_state["arb_last_refresh"]
col_ts, col_btn = st.columns([4, 1])
with col_ts:
    st.caption(t("last_updated_auto").format(seconds=int(elapsed)))
with col_btn:
    if st.button(t("refresh"), key="arb_refresh") or elapsed >= 60:
        st.session_state["arb_last_refresh"] = time.time()
        st.rerun()

st.divider()

# ── Fetch data ────────────────────────────────────────────────────────────────
try:
    gaps = client.get_arbitrage()
except APIError as e:
    st.error(t("arb_fetch_failed").format(error=e.message))
    st.stop()

if not gaps:
    st.info(t("no_arb_gaps"))
    st.stop()

# ── Beginner mode: top 3 plain-language cards ─────────────────────────────────
if mode == "beginner":
    st.subheader(t("top_opportunities"))
    st.markdown(t("top_opportunities_desc"))

    for gap_item in gaps[:3]:
        name = gap_item.get("name", "")
        gap_pct = gap_item.get("gapPercent", 0)
        direction = gap_item.get("direction", "")
        tase_ticker = gap_item.get("taseTicker", "")
        nyse_ticker = gap_item.get("nyseTicker", "")

        sign = "+" if gap_pct >= 0 else ""
        if abs(gap_pct) >= 0.5:
            border_color = "#22c55e" if gap_pct > 0 else "#ef4444"
        else:
            border_color = "#94a3b8"

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {name}")
                if direction == "TASE_PREMIUM":
                    st.markdown(t("tase_premium_desc").format(name=name, pct=abs(gap_pct)))
                elif direction == "FOREIGN_PREMIUM":
                    st.markdown(t("foreign_premium_desc").format(name=name, pct=abs(gap_pct)))
                else:
                    st.markdown(t("parity_desc").format(name=name, pct=gap_pct))
                st.caption(f"TASE: {tase_ticker} | NYSE: {nyse_ticker}")
            with col2:
                st.metric(
                    t("gap"),
                    f"{sign}{gap_pct:.2f}%",
                    delta=arb_direction_label(direction),
                    delta_color="off",
                )

# ── Pro mode: full styled table ───────────────────────────────────────────────
else:
    st.subheader(t("all_pairs").format(n=len(gaps)))

    rows = []
    for g in gaps:
        rows.append({
            t("col_company"):    g.get("name", ""),
            t("col_tase"):       g.get("taseTicker", ""),
            t("col_nyse"):       g.get("nyseTicker", ""),
            t("col_tase_price"): round(g.get("tasePrice", 0), 4),
            t("col_nyse_ils"):   round(g.get("nysePriceIls", g.get("nysePrice", 0)), 4),
            t("col_gap_pct"):    round(g.get("gapPercent", 0), 4),
            t("col_direction"):  arb_direction_label(g.get("direction", "")),
        })

    df = pd.DataFrame(rows)

    col_gap = t("col_gap_pct")
    col_tase_price = t("col_tase_price")
    col_nyse_ils = t("col_nyse_ils")

    def highlight_gap(row):
        gap = row[col_gap]
        if gap > 0.5:
            return ["background-color: #14532d"] * len(row)
        elif gap < -0.5:
            return ["background-color: #7f1d1d"] * len(row)
        return [""] * len(row)

    styled = (
        df.style
        .apply(highlight_gap, axis=1)
        .format({
            col_tase_price: "₪{:.4f}",
            col_nyse_ils:   "₪{:.4f}",
            col_gap:        "{:+.4f}%",
        })
    )

    st.dataframe(styled, use_container_width=True, hide_index=True, height=500)

    # Summary stats
    positive_gaps = [g["gapPercent"] for g in gaps if g.get("gapPercent", 0) > 0.5]
    negative_gaps = [g["gapPercent"] for g in gaps if g.get("gapPercent", 0) < -0.5]

    c1, c2, c3 = st.columns(3)
    c1.metric(t("tase_premium_opps"),   len(positive_gaps))
    c2.metric(t("foreign_premium_opps"), len(negative_gaps))
    c3.metric(t("near_parity"), len(gaps) - len(positive_gaps) - len(negative_gaps))
