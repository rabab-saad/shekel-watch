import streamlit as st
import plotly.graph_objects as go
from services.supabase_service import get_watchlist, add_to_watchlist, remove_from_watchlist
from services.market_service import get_watchlist_df, get_stock_history
from services.currency_service import get_rates_df
from services.arbitrage_service import get_watchlist_arbitrage

st.set_page_config(page_title="Watchlist | Shekel-Watch", page_icon="⭐", layout="wide")

# ── Auth guard ────────────────────────────────────────────────────────────────
if not st.session_state.get("user"):
    st.warning("Please sign in first.")
    st.page_link("app.py", label="← Go to Login")
    st.stop()

user  = st.session_state["user"]
token = st.session_state.get("access_token", "")

st.title("⭐ רשימת המעקב שלי  |  My Watchlist")

# ── Add stock ─────────────────────────────────────────────────────────────────
with st.expander("➕ Add a stock"):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        new_ticker = st.text_input("Ticker symbol  (e.g. AAPL, TSLA, NICE.TA)").upper().strip()
    with c2:
        market = st.selectbox("Market", ["NYSE", "NASDAQ", "TASE"])
    with c3:
        st.write("")
        st.write("")
        if st.button("Add", type="primary"):
            if new_ticker:
                res = add_to_watchlist(token, user.id, new_ticker, market)
                if res["success"]:
                    st.success(f"Added {new_ticker}")
                    st.rerun()
                else:
                    st.error(res.get("error", "Could not add ticker"))
            else:
                st.warning("Enter a ticker symbol first.")

# ── Load watchlist ────────────────────────────────────────────────────────────
watchlist = get_watchlist(token, user.id)

if not watchlist:
    st.info("Your watchlist is empty. Add stocks using the panel above.")
    st.stop()

tickers = [w["ticker"] for w in watchlist]

with st.spinner("Fetching live quotes…"):
    df = get_watchlist_df(tickers)

# Colour Change %
def _colour(val):
    if val > 0:  return "color: #22c55e"
    if val < 0:  return "color: #ef4444"
    return "color: #94a3b8"

styled = (
    df.style
    .applymap(_colour, subset=["Change %"])
    .format({"Price": "{:,.2f}", "Change %": "{:+.2f}%"})
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# ── Price history chart ───────────────────────────────────────────────────────
st.subheader("📊 Price History")

c_sel, c_per = st.columns([2, 3])
with c_sel:
    selected = st.selectbox("Select stock", tickers)
with c_per:
    period = st.radio("Period", ["1wk", "1mo", "3mo", "6mo", "1y"], horizontal=True, index=1)

with st.spinner(f"Loading {selected} history…"):
    hist = get_stock_history(selected, period)

if not hist.empty:
    fig = go.Figure(data=[go.Candlestick(
        x=hist.index,
        open=hist["Open"], high=hist["High"],
        low=hist["Low"],   close=hist["Close"],
        increasing_line_color="#22c55e",
        decreasing_line_color="#ef4444",
    )])
    fig.update_layout(
        title=f"{selected} – Candlestick Chart",
        xaxis_title="Date", yaxis_title="Price",
        height=420,
        xaxis_rangeslider_visible=False,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No price history available for this ticker.")

st.divider()

# ── Watchlist Arbitrage ───────────────────────────────────────────────────────
st.subheader("⚡ ארביטראז׳ מניות  |  Dual-Listed Arbitrage")
st.caption(
    "For Israeli stocks listed on both TASE and NYSE/NASDAQ, compares the TASE price (₪) "
    "with the foreign price converted to ₪ using the live USD/ILS rate. "
    "A gap > 0.5 % may signal a trading opportunity."
)

if st.button("🔍 Scan Watchlist for Arbitrage", use_container_width=True):
    with st.spinner("Loading dual-listed prices…"):
        try:
            _, usd_ils = get_rates_df()
        except Exception:
            usd_ils = 3.7   # fallback
        wl_arb_df = get_watchlist_arbitrage(tickers, usd_ils)
        st.session_state["wl_arb"] = wl_arb_df

if "wl_arb" in st.session_state:
    wl_arb_df = st.session_state["wl_arb"]
    if wl_arb_df.empty:
        st.info(
            "No dual-listed pairs found in your watchlist.\n\n"
            "Try adding stocks like **NICE**, **CHKP**, **MNDY**, **CYBR**, **TEVA** "
            "and their TASE equivalents (e.g. NICE.TA)."
        )
    else:
        def _gap_col(val):
            if isinstance(val, float):
                if val > 0.5:  return "color: #22c55e; font-weight: bold"
                if val < -0.5: return "color: #ef4444; font-weight: bold"
            return "color: #94a3b8"

        def _sig_col(val):
            if isinstance(val, str) and "⚡" in val:
                return "color: #f59e0b; font-weight: bold"
            return ""

        styled_wl = (
            wl_arb_df.style
            .applymap(_gap_col, subset=["Gap %"])
            .applymap(_sig_col, subset=["Signal"])
            .format({"TASE (₪)": "{:,.2f}", "NYSE in ₪": "{:,.2f}",
                     "NYSE (USD)": "{:,.2f}", "Gap %": "{:+.2f}%"})
        )
        st.dataframe(styled_wl, use_container_width=True, hide_index=True)

        fig_wl = go.Figure(go.Bar(
            x=wl_arb_df["Stock"],
            y=wl_arb_df["Gap %"],
            marker_color=["#22c55e" if g > 0 else "#ef4444" for g in wl_arb_df["Gap %"]],
        ))
        fig_wl.update_layout(
            title="TASE vs NYSE Price Gap (%)",
            xaxis_title="Stock", yaxis_title="Gap %",
            height=300, margin=dict(t=40, b=0),
        )
        st.plotly_chart(fig_wl, use_container_width=True)
else:
    st.caption("Click 'Scan Watchlist for Arbitrage' to check your stocks.")

st.divider()

# ── Remove stock ──────────────────────────────────────────────────────────────
st.subheader("🗑️ Remove from Watchlist")
to_remove = st.selectbox("Select stock to remove", ["— select —"] + tickers, key="remove_sel")
if to_remove != "— select —":
    if st.button(f"Remove {to_remove}", type="secondary"):
        res = remove_from_watchlist(token, user.id, to_remove)
        if res["success"]:
            st.success(f"Removed {to_remove}")
            st.rerun()
        else:
            st.error(res.get("error", "Could not remove"))
