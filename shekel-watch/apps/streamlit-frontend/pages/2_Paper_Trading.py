"""
Paper Trading — virtual 100k ILS sandbox.
Balance and portfolio read directly from Supabase; trades go via Express backend.
Auto-refreshes every 30 seconds.
"""

import time
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Paper Trading — Shekel-Watch", page_icon="💹", layout="wide")

from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from services.api_client import APIClient, APIError
from services.supabase_client import get_virtual_balance, get_virtual_portfolio
from services.formatters import fmt_ils, fmt_pct

if not require_auth():
    st.stop()

with st.sidebar:
    st.markdown("## 📊 Shekel-Watch")
    st.divider()
    render_mode_toggle()
    st.divider()
    render_sidebar_user()

# ─────────────────────────────────────────────────────────────────────────────
st.title("💹 Paper Trading")
st.caption("Practice trading with a virtual ₪100,000 — no real money involved.")

token = st.session_state["access_token"]
user_id = st.session_state["user_id"]
client = APIClient()

# ── Auto-refresh counter ──────────────────────────────────────────────────────
if "pt_last_refresh" not in st.session_state:
    st.session_state["pt_last_refresh"] = time.time()

elapsed = time.time() - st.session_state["pt_last_refresh"]
col_head, col_refresh = st.columns([4, 1])
with col_head:
    st.caption(f"Last updated {int(elapsed)}s ago. Auto-refreshes every 30s.")
with col_refresh:
    if st.button("↻ Refresh Now") or elapsed >= 30:
        st.session_state["pt_last_refresh"] = time.time()
        st.rerun()

st.divider()

# ── Virtual Balance ───────────────────────────────────────────────────────────
balance_row = get_virtual_balance(token, user_id)
balance_ils = balance_row["balance_ils"] if balance_row else 100000.0

st.metric("💰 Virtual Balance", fmt_ils(balance_ils), help="Your available ILS for paper trades")

st.divider()

# ── Buy / Sell Form ───────────────────────────────────────────────────────────
st.subheader("📝 Place a Trade")
col_form, col_price = st.columns([2, 1])

with col_form:
    with st.form("trade_form"):
        symbol = st.text_input("Ticker Symbol", placeholder="e.g. TEVA.TA").upper().strip()
        quantity = st.number_input("Quantity (shares)", min_value=1, step=1, value=1)
        action = st.radio("Action", ["buy", "sell"], horizontal=True)
        submitted = st.form_submit_button("Execute Trade", use_container_width=True)

with col_price:
    st.markdown("**Live Price Preview**")
    price_placeholder = st.empty()

    if symbol:
        try:
            quote = client.get_stock(symbol)
            current_price = quote.get("price", 0)
            change_pct = quote.get("changePercent", 0)
            price_placeholder.metric(
                label=symbol,
                value=fmt_ils(current_price),
                delta=fmt_pct(change_pct),
                delta_color="normal" if change_pct >= 0 else "inverse",
            )
        except APIError:
            price_placeholder.warning("Ticker not found")
            current_price = 0
    else:
        price_placeholder.info("Enter a ticker above")
        current_price = 0

if submitted:
    if not symbol:
        st.error("Please enter a ticker symbol.")
    elif current_price <= 0:
        st.error(f"Cannot fetch price for {symbol}. Check the ticker.")
    else:
        cost = quantity * current_price
        if action == "buy":
            if cost > balance_ils:
                st.error(f"Insufficient balance. Trade costs {fmt_ils(cost)}, available {fmt_ils(balance_ils)}.")
            else:
                with st.spinner("Executing trade…"):
                    try:
                        result = client.post_paper_trade(symbol, action, quantity, current_price)
                        new_bal = result.get("newBalance", balance_ils)
                        st.success(
                            f"✅ Bought {quantity} × {symbol} @ {fmt_ils(current_price)} "
                            f"= {fmt_ils(cost)}. New balance: {fmt_ils(new_bal)}"
                        )
                        st.session_state["pt_last_refresh"] = time.time()
                        st.rerun()
                    except APIError as e:
                        st.error(f"Trade failed: {e.message}")
        else:
            with st.spinner("Executing trade…"):
                try:
                    result = client.post_paper_trade(symbol, action, quantity, current_price)
                    proceeds = quantity * current_price
                    new_bal = result.get("newBalance", balance_ils)
                    st.success(
                        f"✅ Sold {quantity} × {symbol} @ {fmt_ils(current_price)} "
                        f"= {fmt_ils(proceeds)}. New balance: {fmt_ils(new_bal)}"
                    )
                    st.session_state["pt_last_refresh"] = time.time()
                    st.rerun()
                except APIError as e:
                    st.error(f"Trade failed: {e.message}")

st.divider()

# ── Portfolio ─────────────────────────────────────────────────────────────────
st.subheader("📋 My Virtual Portfolio")
portfolio = get_virtual_portfolio(token, user_id)

if not portfolio:
    st.info("No positions yet. Place a trade above to get started.")
else:
    # Fetch live prices for all holdings
    symbols = [row["symbol"] for row in portfolio]
    price_map: dict[str, float] = {}
    try:
        quotes = client.get_stocks(symbols)
        for q in quotes:
            price_map[q["ticker"]] = q.get("price", 0)
    except APIError:
        pass

    rows = []
    total_cost = 0.0
    total_value = 0.0

    for row in portfolio:
        sym = row["symbol"]
        qty = row["quantity"]
        avg_price = row.get("avg_buy_price", 0)
        curr_price = price_map.get(sym, avg_price)
        cost_basis = qty * avg_price
        curr_value = qty * curr_price
        pnl = curr_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis else 0

        total_cost += cost_basis
        total_value += curr_value

        rows.append({
            "Symbol": sym,
            "Qty": qty,
            "Avg Buy (₪)": round(avg_price, 4),
            "Current (₪)": round(curr_price, 4),
            "Cost Basis (₪)": round(cost_basis, 2),
            "Market Value (₪)": round(curr_value, 2),
            "P&L (₪)": round(pnl, 2),
            "P&L %": round(pnl_pct, 2),
        })

    df = pd.DataFrame(rows)

    # Style P&L columns
    def color_pnl(val):
        if isinstance(val, (int, float)):
            color = "#22c55e" if val >= 0 else "#ef4444"
            return f"color: {color}; font-weight: bold"
        return ""

    styled = (
        df.style
        .applymap(color_pnl, subset=["P&L (₪)", "P&L %"])
        .format({
            "Avg Buy (₪)": "₪{:.4f}",
            "Current (₪)": "₪{:.4f}",
            "Cost Basis (₪)": "₪{:,.2f}",
            "Market Value (₪)": "₪{:,.2f}",
            "P&L (₪)": "₪{:,.2f}",
            "P&L %": "{:+.2f}%",
        })
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Portfolio totals
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0
    t1, t2, t3 = st.columns(3)
    t1.metric("Total Cost Basis", fmt_ils(total_cost))
    t2.metric("Total Market Value", fmt_ils(total_value))
    t3.metric(
        "Total P&L",
        fmt_ils(total_pnl),
        delta=fmt_pct(total_pnl_pct),
        delta_color="normal" if total_pnl >= 0 else "inverse",
    )
