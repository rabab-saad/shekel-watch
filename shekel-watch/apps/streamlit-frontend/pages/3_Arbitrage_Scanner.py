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
from components.term_tooltip import render_term
from services.api_client import APIClient, APIError
from services.formatters import arb_direction_label, arb_direction_label_he

if not require_auth():
    st.stop()

with st.sidebar:
    st.markdown("## 📊 Shekel-Watch")
    st.divider()
    render_mode_toggle()
    st.divider()
    render_sidebar_user()

# ─────────────────────────────────────────────────────────────────────────────
st.title("🔍 Arbitrage Scanner")
st.caption("Real-time pricing gaps between TASE and NYSE for dual-listed companies.")

render_term("arbitrage", "What is Arbitrage?")

client = APIClient()
mode = st.session_state.get("trading_mode", "beginner")

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if "arb_last_refresh" not in st.session_state:
    st.session_state["arb_last_refresh"] = time.time()

elapsed = time.time() - st.session_state["arb_last_refresh"]
col_ts, col_btn = st.columns([4, 1])
with col_ts:
    st.caption(f"Last updated {int(elapsed)}s ago. Auto-refreshes every 60s.")
with col_btn:
    if st.button("↻ Refresh", key="arb_refresh") or elapsed >= 60:
        st.session_state["arb_last_refresh"] = time.time()
        st.rerun()

st.divider()

# ── Fetch data ────────────────────────────────────────────────────────────────
try:
    gaps = client.get_arbitrage()
except APIError as e:
    st.error(f"Failed to load arbitrage data: {e.message}")
    st.stop()

if not gaps:
    st.info("No arbitrage gaps detected right now. Check back during market hours.")
    st.stop()

# ── Beginner mode: top 3 plain-language cards ─────────────────────────────────
if mode == "beginner":
    st.subheader("Top Opportunities")
    st.markdown("Here are the biggest pricing differences between the Tel Aviv and New York stock exchanges:")

    for gap_item in gaps[:3]:
        name = gap_item.get("name", "")
        gap_pct = gap_item.get("gapPercent", 0)
        direction = gap_item.get("direction", "")
        tase_ticker = gap_item.get("taseTicker", "")
        nyse_ticker = gap_item.get("nyseTicker", "")
        tase_price = gap_item.get("tasePrice", 0)
        nyse_price_ils = gap_item.get("nysePriceIls", gap_item.get("nysePrice", 0))

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
                    st.markdown(
                        f"**{name}** is **{abs(gap_pct):.2f}% more expensive on TASE** "
                        f"than on NYSE right now. Buying on NYSE and selling on TASE "
                        f"could theoretically lock in this difference."
                    )
                elif direction == "FOREIGN_PREMIUM":
                    st.markdown(
                        f"**{name}** is **{abs(gap_pct):.2f}% cheaper on TASE** "
                        f"than on NYSE. It may be worth buying locally."
                    )
                else:
                    st.markdown(f"**{name}** prices are roughly equal on both exchanges ({gap_pct:.2f}% gap).")
                st.caption(f"TASE: {tase_ticker} | NYSE: {nyse_ticker}")
            with col2:
                st.metric(
                    "Gap",
                    f"{sign}{gap_pct:.2f}%",
                    delta=arb_direction_label(direction),
                    delta_color="off",
                )

# ── Pro mode: full styled table ───────────────────────────────────────────────
else:
    st.subheader(f"All Dual-Listed Pairs ({len(gaps)} companies)")

    rows = []
    for g in gaps:
        rows.append({
            "Company": g.get("name", ""),
            "TASE": g.get("taseTicker", ""),
            "NYSE": g.get("nyseTicker", ""),
            "TASE Price (₪)": round(g.get("tasePrice", 0), 4),
            "NYSE (₪ equiv)": round(g.get("nysePriceIls", g.get("nysePrice", 0)), 4),
            "Gap %": round(g.get("gapPercent", 0), 4),
            "Direction": arb_direction_label(g.get("direction", "")),
        })

    df = pd.DataFrame(rows)

    def highlight_gap(row):
        gap = row["Gap %"]
        if gap > 0.5:
            return ["background-color: #14532d"] * len(row)
        elif gap < -0.5:
            return ["background-color: #7f1d1d"] * len(row)
        return [""] * len(row)

    styled = (
        df.style
        .apply(highlight_gap, axis=1)
        .format({
            "TASE Price (₪)": "₪{:.4f}",
            "NYSE (₪ equiv)": "₪{:.4f}",
            "Gap %": "{:+.4f}%",
        })
    )

    st.dataframe(styled, use_container_width=True, hide_index=True, height=500)

    # Summary stats
    positive_gaps = [g["gapPercent"] for g in gaps if g.get("gapPercent", 0) > 0.5]
    negative_gaps = [g["gapPercent"] for g in gaps if g.get("gapPercent", 0) < -0.5]

    c1, c2, c3 = st.columns(3)
    c1.metric("TASE Premium Opportunities", len(positive_gaps))
    c2.metric("Foreign Premium Opportunities", len(negative_gaps))
    c3.metric("Near Parity", len(gaps) - len(positive_gaps) - len(negative_gaps))
