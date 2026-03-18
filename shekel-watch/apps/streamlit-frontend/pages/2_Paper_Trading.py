"""
Paper Trading — Portfolio Builder with full analysis & AI suggestions.

Tabs:
  1. 🔍 Search & Add   — find any instrument, view detail panel, allocate NIS
  2. 📊 Portfolio       — positions, investment amount, risk level, cash remaining
  3. 📈 Analysis        — allocation donut, risk assessment, sector diversification
  4. 🤖 AI Suggestions  — GPT-powered personalised recommendations
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Paper Trading — Shekel-Watch", page_icon="💹", layout="wide")

from streamlit_autorefresh import st_autorefresh
from components.auth import require_auth, render_sidebar_user
from components.mode_toggle import render_mode_toggle
from components.lang_selector import render_lang_selector
from services.api_client import APIClient, APIError
from services.supabase_client import (
    get_profile,
    update_investment_config,
    get_virtual_portfolio,
    upsert_portfolio_position,
    remove_portfolio_position,
)
from services.formatters import fmt_ils, fmt_pct
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

# Auto-refresh every 60 s
st_autorefresh(interval=60_000, key="pt_autorefresh")

client  = APIClient()
token   = st.session_state["access_token"]
user_id = st.session_state["user_id"]
lang    = st.session_state.get("language", "en")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_large(val) -> str:
    """Format large numbers (market cap) as T / B / M."""
    if val is None:
        return "—"
    try:
        v = float(val)
    except (TypeError, ValueError):
        return "—"
    if v >= 1e12:
        return f"${v / 1e12:.2f}T"
    if v >= 1e9:
        return f"${v / 1e9:.2f}B"
    if v >= 1e6:
        return f"${v / 1e6:.2f}M"
    return f"${v:,.0f}"


@st.cache_data(ttl=60, show_spinner=False)
def _live_quote(ticker: str) -> dict:
    try:
        return client.get_stock(ticker)
    except APIError:
        return {}


@st.cache_data(ttl=60, show_spinner=False)
def _usd_ils() -> float:
    try:
        return float(client.get_usd_ils().get("rate", 3.7))
    except APIError:
        return 3.7


def _price_in_ils(ticker: str, usd_ils_rate: float) -> float:
    q     = _live_quote(ticker)
    price = float(q.get("price") or 0)
    cur   = (q.get("currency") or "USD").upper()
    if cur == "ILS":
        return price
    if cur == "GBX":          # British pence → GBP × rough GBP/USD
        return price / 100 * usd_ils_rate * 0.79
    return price * usd_ils_rate  # default: treat as USD


# ── Load profile (investment_amount, risk_level) ──────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def _load_profile(uid: str, _tok: str) -> dict:
    return get_profile(_tok, uid)


profile           = _load_profile(user_id, token)
investment_amount = float(profile.get("investment_amount") or 0)
risk_level        = profile.get("risk_level") or "medium"

# ── First-visit: Investment Amount Setup ──────────────────────────────────────

if investment_amount < 1000:
    st.title(t("setup_title"))
    st.markdown(t("setup_description"))
    with st.form("setup_form"):
        amt = st.number_input(
            t("total_investment_label"),
            min_value=1000.0,
            max_value=10_000_000.0,
            value=100_000.0,
            step=1000.0,
            format="%.0f",
        )
        submitted = st.form_submit_button(t("start_portfolio"), use_container_width=True)
    if submitted:
        res = update_investment_config(token, user_id, investment_amount=amt, risk_level="medium")
        if res.get("success"):
            _load_profile.clear()
            st.rerun()
        else:
            st.error(f"Could not save: {res.get('error')}")
    st.stop()

# ── Page header ───────────────────────────────────────────────────────────────

st.title(t("paper_trading_title"))

positions = get_virtual_portfolio(token, user_id)

total_allocated = sum(float(p.get("quantity", 0)) for p in positions)
remaining       = investment_amount - total_allocated
pct_used        = (total_allocated / investment_amount * 100) if investment_amount else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric(t("total_budget"),     fmt_ils(investment_amount))
c2.metric(t("allocated"),        fmt_ils(total_allocated),  f"{pct_used:.1f}%")
c3.metric(t("unallocated_cash"), fmt_ils(remaining))
rl_icons = {
    "low":    t("risk_low"),
    "medium": t("risk_medium"),
    "high":   t("risk_high"),
}
c4.metric(t("risk_level"), rl_icons.get(risk_level, risk_level.capitalize()))

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_portfolio, tab_analysis, tab_ai, tab_trade = st.tabs(
    [t("tab_portfolio"), t("tab_analysis"), t("tab_ai"), t("tab_trade")]
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: PORTFOLIO
# ═══════════════════════════════════════════════════════════════════════════════

with tab_portfolio:
    st.subheader(t("my_portfolio"))

    # Settings
    with st.expander(t("investment_settings"), expanded=False):
        with st.form("settings_form"):
            new_amt = st.number_input(
                t("total_investment_amount"),
                min_value=1000.0,
                value=investment_amount,
                step=1000.0,
                format="%.0f",
            )
            new_risk = st.select_slider(
                t("risk_level"),
                options=["low", "medium", "high"],
                value=risk_level,
                format_func=lambda x: {
                    "low":    t("risk_low"),
                    "medium": t("risk_medium"),
                    "high":   t("risk_high"),
                }[x],
            )
            save_ok = st.form_submit_button(t("save_settings"), use_container_width=True)
        if save_ok:
            res = update_investment_config(token, user_id,
                                           investment_amount=new_amt, risk_level=new_risk)
            if res.get("success"):
                st.success(t("settings_saved"))
                _load_profile.clear()
                st.rerun()
            else:
                st.error(f"Error: {res.get('error')}")

    if not positions:
        st.info(t("no_positions"))
    else:
        usd_rate      = _usd_ils()
        stale_syms: list[str] = []

        st.markdown(f"**{t('positions_count').format(n=len(positions))}**")

        for pos in positions:
            sym       = pos["symbol"]
            alloc_ils = float(pos.get("quantity", 0))
            buy_p_ils = float(pos.get("avg_buy_price") or 1)

            cur_p_ils = _price_in_ils(sym, usd_rate)
            if cur_p_ils <= 0:
                cur_p_ils = buy_p_ils
                stale_syms.append(sym)

            shares        = alloc_ils / buy_p_ils if buy_p_ils > 0 else 0
            cur_value     = shares * cur_p_ils
            pnl_ils       = cur_value - alloc_ils
            pnl_pct       = (pnl_ils / alloc_ils * 100) if alloc_ils > 0 else 0
            weight_pct    = (alloc_ils / investment_amount * 100) if investment_amount > 0 else 0
            pnl_color     = "green" if pnl_ils >= 0 else "red"

            hdr_col, del_col = st.columns([7, 1])
            with hdr_col:
                st.markdown(
                    f"**{sym}** &nbsp;·&nbsp; "
                    f"Allocated: {fmt_ils(alloc_ils)} &nbsp;·&nbsp; "
                    f"{t('current_value')}: {fmt_ils(cur_value)} &nbsp;·&nbsp; "
                    f"P&L: <span style='color:{pnl_color}'>"
                    f"{fmt_ils(pnl_ils)} ({pnl_pct:+.1f}%)</span> &nbsp;·&nbsp; "
                    f"{t('weight')}: {weight_pct:.1f}%",
                    unsafe_allow_html=True,
                )
            with del_col:
                if st.button(t("remove"), key=f"del_{sym}"):
                    res = remove_portfolio_position(token, user_id, sym)
                    if res.get("success"):
                        _live_quote.clear()
                        st.rerun()
                    else:
                        st.error(t("remove_failed").format(error=res.get("error")))
            st.divider()

        if stale_syms:
            st.caption(t("live_price_unavailable").format(tickers=", ".join(stale_syms)))

        st.markdown(f"**{t('cash_unallocated')}:** {fmt_ils(remaining)} ({100 - pct_used:.1f}%)")
        st.progress(min(pct_used / 100, 1.0))

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_analysis:
    if not positions:
        st.info(t("no_positions"))
    else:
        symbols = [p["symbol"] for p in positions]

        @st.cache_data(ttl=120, show_spinner=True)
        def _fetch_analysis(syms_key: str, _tok: str) -> dict:
            try:
                return client.get_portfolio_analysis(syms_key.split(","))
            except APIError:
                return {}

        analysis  = _fetch_analysis(",".join(sorted(symbols)), token)
        meta      = analysis.get("symbols", {})
        usd_rate  = float(analysis.get("usdIls") or _usd_ils())

        # Build enriched position list
        enriched: list[dict] = []
        for pos in positions:
            sym       = pos["symbol"]
            alloc_ils = float(pos.get("quantity", 0))
            buy_p_ils = float(pos.get("avg_buy_price") or 1)
            q         = _live_quote(sym)
            cur_p_raw = float(q.get("price") or 0)
            currency  = (q.get("currency") or "USD").upper()

            if cur_p_raw <= 0:
                cur_p_ils = buy_p_ils
            elif currency == "ILS":
                cur_p_ils = cur_p_raw
            elif currency == "GBX":
                cur_p_ils = cur_p_raw / 100 * usd_rate * 0.79
            else:
                cur_p_ils = cur_p_raw * usd_rate

            shares    = alloc_ils / buy_p_ils if buy_p_ils > 0 else 0
            cur_value = shares * cur_p_ils
            m         = meta.get(sym, {})

            enriched.append({
                "symbol":        sym,
                "name":          q.get("name", sym),
                "allocation_ils": alloc_ils,
                "current_value":  cur_value,
                "pnl_pct":        ((cur_value - alloc_ils) / alloc_ils * 100) if alloc_ils > 0 else 0,
                "sector":         m.get("sector"),
                "beta":           m.get("beta"),
                "volatility30d":  m.get("volatility30d", 0),
                "pe":             m.get("pe"),
                "week52High":     m.get("week52High"),
                "week52Low":      m.get("week52Low"),
            })

        total_alloc_val = sum(e["allocation_ils"] for e in enriched)
        for e in enriched:
            e["weight_pct"] = (e["allocation_ils"] / total_alloc_val * 100) if total_alloc_val > 0 else 0

        # ── Panel A: Allocation Donut ─────────────────────────────────────────
        st.subheader(t("allocation_breakdown"))

        labels = [e["symbol"] for e in enriched]
        values = [e["allocation_ils"] for e in enriched]
        if remaining > 0:
            labels.append(t("cash_unallocated"))
            values.append(remaining)

        fig_donut = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            textinfo="label+percent",
            marker=dict(line=dict(color="#0f172a", width=2)),
        ))
        fig_donut.update_layout(
            template="plotly_dark",
            margin=dict(t=0, b=0, l=0, r=0),
            height=340,
        )
        st.plotly_chart(fig_donut, use_container_width=True)

        # ── Panel B: Risk Assessment ──────────────────────────────────────────
        st.subheader(t("risk_assessment"))

        w_beta = None
        beta_weights = [(e["beta"], e["weight_pct"]) for e in enriched if e["beta"] is not None]
        if beta_weights:
            total_bw = sum(w for _, w in beta_weights)
            if total_bw > 0:
                w_beta = sum(b * w for b, w in beta_weights) / total_bw

        w_vol = None
        vol_weights = [(e["volatility30d"], e["weight_pct"]) for e in enriched if e.get("volatility30d", 0) > 0]
        if vol_weights:
            total_vw = sum(w for _, w in vol_weights)
            if total_vw > 0:
                w_vol = sum(v * w for v, w in vol_weights) / total_vw

        # Map volatility → risk score 1–10
        port_risk_score: int | None = None
        if w_vol is not None:
            if w_vol < 0.5:   port_risk_score = 2
            elif w_vol < 1.0: port_risk_score = 4
            elif w_vol < 2.0: port_risk_score = 6
            elif w_vol < 3.5: port_risk_score = 8
            else:             port_risk_score = 10

        r1, r2, r3 = st.columns(3)
        r1.metric(t("weighted_beta"),
                  f"{w_beta:.2f}" if w_beta is not None else "—",
                  help=t("weighted_beta_help"))
        r2.metric(t("avg_30d_vol"),
                  f"{w_vol:.2f}%" if w_vol is not None else "—",
                  help=t("avg_30d_vol_help"))
        r3.metric(t("portfolio_risk_score"),
                  f"{port_risk_score}/10" if port_risk_score else "—")

        # Risk alignment
        if port_risk_score is not None:
            if risk_level == "low" and port_risk_score > 4:
                st.error(t("risk_mismatch_low").format(score=port_risk_score))
            elif risk_level == "high" and port_risk_score < 5:
                st.warning(t("risk_mismatch_high").format(score=port_risk_score))
            else:
                st.success(t("risk_aligned").format(
                    score=port_risk_score,
                    level=risk_level.capitalize(),
                ))

        # Per-position risk table
        risk_rows = [{
            t("col_symbol"):   e["symbol"],
            t("col_weight_pct"): f"{e['weight_pct']:.1f}%",
            t("col_beta"):     f"{e['beta']:.2f}"           if e["beta"]           is not None else "—",
            t("col_vol_30d"):  f"{e['volatility30d']:.2f}%" if e.get("volatility30d", 0) > 0 else "—",
            t("col_pe"):       f"{e['pe']:.1f}"             if e.get("pe")         is not None else "—",
            t("col_pnl_pct"):  fmt_pct(e["pnl_pct"]),
        } for e in enriched]
        st.dataframe(pd.DataFrame(risk_rows), use_container_width=True, hide_index=True)

        # ── Panel C: Sector Diversification ───────────────────────────────────
        st.subheader(t("sector_diversification"))

        sector_map: dict[str, float] = {}
        for e in enriched:
            s = e["sector"] or "Other / Unknown"
            sector_map[s] = sector_map.get(s, 0.0) + e["weight_pct"]

        df_sec = pd.DataFrame(
            sorted(sector_map.items(), key=lambda x: x[1], reverse=True),
            columns=["Sector", "Weight %"],
        )
        fig_bar = px.bar(
            df_sec, x="Weight %", y="Sector", orientation="h",
            template="plotly_dark",
            color="Weight %",
            color_continuous_scale="Blues",
        )
        fig_bar.update_layout(
            margin=dict(t=10, b=0),
            height=max(200, len(sector_map) * 42),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        for sec, w in sector_map.items():
            if w > 40:
                st.warning(t("sector_concentration_warning").format(sector=sec, weight=w))

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: AI SUGGESTIONS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_ai:
    st.subheader(t("ai_portfolio_suggestions"))

    if not positions:
        st.info(t("build_portfolio_first"))
    else:
        if st.button(t("refresh_suggestions"), use_container_width=False):
            st.session_state.pop("ai_suggestions", None)
            st.session_state.pop("ai_suggestions_at", None)

        if "ai_suggestions" not in st.session_state:
            # Build position summaries for the prompt
            usd_rate_ai   = _usd_ils()
            pos_summaries: list[dict] = []

            ai_meta: dict = {}
            try:
                syms    = [p["symbol"] for p in positions]
                ana     = client.get_portfolio_analysis(syms)
                ai_meta = ana.get("symbols", {})
            except APIError:
                pass

            total_alloc_ai = sum(float(p.get("quantity", 0)) for p in positions)

            for pos in positions:
                sym       = pos["symbol"]
                alloc_ils = float(pos.get("quantity", 0))
                buy_p_ils = float(pos.get("avg_buy_price") or 1)
                q         = _live_quote(sym)
                cur_p_raw = float(q.get("price") or 0)
                currency  = (q.get("currency") or "USD").upper()

                if cur_p_raw <= 0:
                    cur_p_ils = buy_p_ils
                elif currency == "ILS":
                    cur_p_ils = cur_p_raw
                elif currency == "GBX":
                    cur_p_ils = cur_p_raw / 100 * usd_rate_ai * 0.79
                else:
                    cur_p_ils = cur_p_raw * usd_rate_ai

                shares    = alloc_ils / buy_p_ils if buy_p_ils > 0 else 0
                cur_value = shares * cur_p_ils
                pnl_pct   = ((cur_value - alloc_ils) / alloc_ils * 100) if alloc_ils > 0 else 0
                weight    = (alloc_ils / total_alloc_ai * 100) if total_alloc_ai > 0 else 0
                m         = ai_meta.get(sym, {})

                pos_summaries.append({
                    "symbol":            sym,
                    "name":              q.get("name", sym),
                    "allocation_ils":    round(alloc_ils, 2),
                    "current_value_ils": round(cur_value, 2),
                    "pnl_pct":           round(pnl_pct, 2),
                    "weight_pct":        round(weight, 2),
                    "sector":            m.get("sector"),
                    "beta":              m.get("beta"),
                    "volatility30d":     m.get("volatility30d", 0),
                })

            with st.spinner(t("generating_suggestions")):
                try:
                    result = client.post_portfolio_suggestions(
                        positions  = pos_summaries,
                        risk_level = risk_level,
                        language   = lang,
                    )
                    st.session_state["ai_suggestions"]    = result.get("suggestions", "")
                    st.session_state["ai_suggestions_at"] = result.get("generatedAt", "")
                except APIError as e:
                    st.error(t("ai_failed").format(error=e.message))

        suggestions_text = st.session_state.get("ai_suggestions", "")
        generated_at     = st.session_state.get("ai_suggestions_at", "")

        if suggestions_text:
            if generated_at:
                st.caption(t("generated_at").format(time=generated_at[:19].replace("T", " ")))
            st.markdown(suggestions_text)
        else:
            st.info(t("click_refresh"))

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: TRADE
# ═══════════════════════════════════════════════════════════════════════════════

with tab_trade:

    # ── Per-trade 10-second price cache (separate from the 60s portfolio cache) ──
    @st.cache_data(ttl=10, show_spinner=False)
    def _trade_live_quote(ticker: str) -> dict:
        try:
            return client.get_stock(ticker)
        except APIError:
            return {}

    def _trade_price_in_ils(ticker: str, usd_rate: float) -> tuple[float, dict]:
        q     = _trade_live_quote(ticker)
        price = float(q.get("price") or 0)
        cur   = (q.get("currency") or "USD").upper()
        if cur == "ILS":
            return price, q
        if cur == "GBX":
            return price / 100 * usd_rate * 0.79, q
        return price * usd_rate, q

    # ── Cash Banner ───────────────────────────────────────────────────────────
    try:
        bal_data    = client.get_trade_balance()
        trade_cash  = float(bal_data.get("balance_ils", 0))
        cash_ok     = True
    except APIError:
        trade_cash  = 0.0
        cash_ok     = False

    b1, b2 = st.columns(2)
    b1.metric(t("trade_cash_available"), fmt_ils(trade_cash))
    if not cash_ok:
        b1.caption("⚠ Could not load balance")

    st.divider()

    # ── Step 1: Search & Select ───────────────────────────────────────────────
    st.subheader(t("trade_step1_title"))

    tq_col, tb_col = st.columns([4, 1])
    with tq_col:
        trade_query = st.text_input(
            "TSearch", label_visibility="collapsed",
            placeholder=t("search_placeholder"),
            key="trade_search_query",
        )
    with tb_col:
        do_trade_search = st.button(t("search_btn"), key="trade_search_btn", use_container_width=True)

    if do_trade_search and trade_query:
        with st.spinner(t("searching")):
            try:
                hits = client.search_stocks(trade_query).get("quotes", [])
                st.session_state["trade_hits"] = hits
            except APIError as e:
                st.session_state["trade_hits"] = []
                st.error(t("search_failed_msg").format(error=e.message))

    for i, h in enumerate(st.session_state.get("trade_hits", [])):
        ca, cb, cc, cd, ce = st.columns([1.5, 3.5, 1.2, 1.2, 1])
        ca.markdown(f"**{h.get('symbol', '')}**")
        cb.write(h.get("name", ""))
        cc.write(h.get("typeDisp", ""))
        cd.write(h.get("exchange", ""))
        if ce.button(t("trade_select"), key=f"tsel_{h['symbol']}_{i}"):
            st.session_state["trade_ticker"]      = h["symbol"]
            st.session_state["trade_ticker_name"] = h.get("name", h["symbol"])
            st.session_state["trade_ticker_type"] = h.get("typeDisp", "")
            st.session_state.pop("trade_hits",    None)
            st.session_state.pop("trade_preview", None)
            st.rerun()

    # ── Selected Instrument Panel ─────────────────────────────────────────────
    trade_ticker = st.session_state.get("trade_ticker")

    if not trade_ticker:
        st.info(t("trade_no_ticker_selected"))
    else:
        trade_name = st.session_state.get("trade_ticker_name", trade_ticker)
        trade_type = st.session_state.get("trade_ticker_type", "")

        st.divider()
        head_col, clr_col = st.columns([5, 1])
        head_col.subheader(f"📋 {trade_ticker}  ·  {trade_name}")
        if trade_type:
            head_col.caption(trade_type)
        if clr_col.button(t("trade_clear_selection"), key="trade_clear"):
            for k in ("trade_ticker", "trade_ticker_name", "trade_ticker_type", "trade_preview", "trade_hits"):
                st.session_state.pop(k, None)
            st.rerun()

        # ── Live Price ────────────────────────────────────────────────────────
        usd_rate_t           = _usd_ils()
        trade_price_ils, tq  = _trade_price_in_ils(trade_ticker, usd_rate_t)
        change_pct           = float(tq.get("changePercent") or 0)
        is_stale             = trade_price_ils <= 0

        if is_stale:
            trade_price_ils = float(st.session_state.get(f"tp_{trade_ticker}", 0))
        else:
            st.session_state[f"tp_{trade_ticker}"] = trade_price_ils

        ref_col, _ = st.columns([1, 5])
        if ref_col.button(t("trade_refresh_price"), key="trade_price_refresh"):
            _trade_live_quote.clear()
            st.rerun()

        p1, p2, p3, p4 = st.columns(4)
        p1.metric(t("trade_live_price"), fmt_ils(trade_price_ils),
                  delta=fmt_pct(change_pct) if not is_stale else None)
        if is_stale:
            p1.caption(t("trade_stale_price"))
        p2.metric(t("trade_daily_change_label"), fmt_pct(change_pct) if not is_stale else "—")
        p3.metric("High", f"{tq.get('regularMarketDayHigh') or '—'}")
        p4.metric("Low",  f"{tq.get('regularMarketDayLow')  or '—'}")

        # ── Sparkline (1 week history) ────────────────────────────────────────
        try:
            bars = client.get_stock_history(trade_ticker, "1wk")
            if bars:
                df_sp = pd.DataFrame(bars)
                fig_sp = px.line(df_sp, x="time", y="close", template="plotly_dark",
                                 color_discrete_sequence=["#38bdf8"])
                fig_sp.update_layout(
                    height=110, margin=dict(t=0, b=0, l=0, r=0), showlegend=False,
                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_sp, use_container_width=True)
        except APIError:
            pass

        st.divider()

        # ── Holdings for this ticker ──────────────────────────────────────────
        pos_row   = next((p for p in positions if p["symbol"] == trade_ticker), None)
        held_units = 0.0
        if pos_row and float(pos_row.get("avg_buy_price") or 0) > 0:
            held_units = float(pos_row["quantity"]) / float(pos_row["avg_buy_price"])

        # ── Order Form (Steps 2-4) ────────────────────────────────────────────
        st.markdown(f"**{t('trade_action_label')}**")
        trade_action = st.radio(
            t("trade_action_label"), label_visibility="collapsed",
            options=["buy", "sell"],
            format_func=lambda x: t("trade_buy") if x == "buy" else t("trade_sell"),
            key="trade_action_radio",
            horizontal=True,
        )

        if trade_action == "sell":
            if held_units <= 0:
                st.warning(t("trade_sell_no_holding").format(symbol=trade_ticker))
            else:
                st.caption(f"{t('trade_current_holding')}: **{held_units:.4f}** {t('trade_units_held')}")

        trade_units = st.number_input(
            t("trade_units_label"), min_value=0.001, value=1.0, step=1.0,
            format="%.3f", key="trade_units_input",
        )

        # Real-time cost preview
        if trade_price_ils > 0:
            est_total = trade_units * trade_price_ils
            ci1, ci2 = st.columns(2)
            ci1.metric(t("trade_estimated_total"), fmt_ils(est_total))
            if trade_action == "buy":
                ci2.metric(t("trade_available_cash"), fmt_ils(trade_cash))
            else:
                ci2.metric(t("trade_current_holding"),
                           f"{held_units:.4f} {t('trade_units_held')}")

        # Order type
        order_opts = ["market", "limit"]
        if trade_action == "sell":
            order_opts += ["stop_loss", "take_profit"]
        trade_order_type = st.selectbox(
            t("trade_order_type_label"),
            options=order_opts,
            format_func=lambda x: t(f"trade_{x}"),
            key="trade_order_type_select",
        )

        # Trigger price (only for non-market)
        trigger_price = None
        if trade_order_type != "market":
            trigger_helps = {
                "limit":       t("trade_trigger_help_limit_buy") if trade_action == "buy" else t("trade_trigger_help_limit_sell"),
                "stop_loss":   t("trade_trigger_help_stop_loss"),
                "take_profit": t("trade_trigger_help_take_profit"),
            }
            trigger_price = st.number_input(
                t("trade_trigger_price"),
                min_value=0.0001,
                value=max(trade_price_ils, 0.0001),
                step=0.01,
                format="%.4f",
                help=trigger_helps.get(trade_order_type, ""),
                key="trade_trigger_input",
            )

        # ── Preview Button ────────────────────────────────────────────────────
        if st.button(t("trade_preview_btn"), key="trade_preview_btn", use_container_width=True):
            errors = []
            if trade_price_ils <= 0 and trade_order_type == "market":
                errors.append(t("trade_price_required"))
            if trade_units <= 0:
                errors.append(t("trade_units_required"))
            if trade_action == "buy" and trade_order_type == "market":
                if trade_price_ils > 0 and trade_units * trade_price_ils > trade_cash + 0.01:
                    errors.append(t("trade_exceeds_cash").format(available=fmt_ils(trade_cash)))
            if trade_action == "buy" and trade_order_type != "market" and trigger_price:
                if trade_units * trigger_price > trade_cash + 0.01:
                    errors.append(t("trade_exceeds_cash").format(available=fmt_ils(trade_cash)))
            if trade_action == "sell" and trade_units > held_units + 0.001:
                errors.append(t("trade_exceeds_holding").format(holding=f"{held_units:.4f}"))
            if trade_action == "sell" and held_units <= 0:
                errors.append(t("trade_sell_no_holding").format(symbol=trade_ticker))

            if errors:
                for e in errors:
                    st.error(e)
            else:
                exec_price = trigger_price if (trade_order_type != "market" and trigger_price) else trade_price_ils
                st.session_state["trade_preview"] = {
                    "symbol":        trade_ticker,
                    "name":          trade_name,
                    "action":        trade_action,
                    "units":         trade_units,
                    "order_type":    trade_order_type,
                    "trigger_price": trigger_price,
                    "price_ils":     trade_price_ils,
                    "total_ils":     trade_units * exec_price,
                }

        # ── Step 5: Order Confirmation ────────────────────────────────────────
        preview = st.session_state.get("trade_preview")
        if preview and preview.get("symbol") == trade_ticker:
            st.divider()
            st.subheader(t("trade_order_summary"))

            exec_price_disp = (
                preview["trigger_price"]
                if preview["order_type"] != "market" and preview["trigger_price"]
                else preview["price_ils"]
            )
            remaining_after = (
                trade_cash - preview["total_ils"]
                if preview["action"] == "buy"
                else trade_cash + preview["total_ils"]
            )

            sc1, sc2 = st.columns(2)
            with sc1:
                _order_type_key = f"trade_{preview['order_type']}"
                _action_label = t("trade_buy") if preview["action"] == "buy" else t("trade_sell")
                st.markdown(
                    f"**{preview['symbol']}** · {preview['name']}  \n"
                    f"**{t('trade_action_label')}:** {_action_label}  \n"
                    f"**{t('trade_units_label')}:** {preview['units']:.4f}  \n"
                    f"**{t('trade_order_type_label')}:** {t(_order_type_key)}"
                )
            with sc2:
                st.markdown(
                    f"**{t('trade_at_price')}:** {fmt_ils(exec_price_disp)}  \n"
                    f"**{t('trade_estimated_total')}:** {fmt_ils(preview['total_ils'])}  \n"
                    f"**{t('trade_remaining_after')}:** {fmt_ils(remaining_after)}"
                )

            cc1, cc2 = st.columns(2)
            confirmed = cc1.button(t("trade_confirm_order"), key="trade_confirm_btn",
                                   use_container_width=True, type="primary")
            cancelled = cc2.button(t("trade_cancel"), key="trade_cancel_btn",
                                   use_container_width=True)

            if confirmed:
                if preview["order_type"] == "market":
                    with st.spinner(t("trade_executing")):
                        try:
                            result = client.post_trade_execute(
                                symbol    = preview["symbol"],
                                action    = preview["action"],
                                units     = preview["units"],
                                price_ils = preview["price_ils"],
                            )
                            if result.get("success"):
                                st.success(t("trade_order_placed").format(
                                    action=t(f"trade_{preview['action']}"),
                                    units=f"{preview['units']:.4f}",
                                    symbol=preview["symbol"],
                                    total=fmt_ils(preview["total_ils"]),
                                ))
                                st.session_state.pop("trade_preview", None)
                                _live_quote.clear()
                                _trade_live_quote.clear()
                                st.rerun()
                            else:
                                st.error(t("trade_order_failed").format(error=result.get("error", "")))
                        except APIError as e:
                            st.error(t("trade_order_failed").format(error=e.message))
                else:
                    with st.spinner(t("trade_placing_order")):
                        try:
                            result = client.post_trade_order(
                                symbol        = preview["symbol"],
                                action        = preview["action"],
                                units         = preview["units"],
                                order_type    = preview["order_type"],
                                trigger_price = preview["trigger_price"],
                            )
                            if result.get("success"):
                                st.success(t("trade_pending_placed").format(
                                    type    = t(f"trade_{preview['order_type']}"),
                                    symbol  = preview["symbol"],
                                    trigger = f"{preview['trigger_price']:.2f}",
                                ))
                                st.session_state.pop("trade_preview", None)
                                st.rerun()
                            else:
                                st.error(t("trade_order_failed").format(error=result.get("error", "")))
                        except APIError as e:
                            st.error(t("trade_order_failed").format(error=e.message))

            if cancelled:
                st.session_state.pop("trade_preview", None)
                st.rerun()

    # ── Pending Orders ────────────────────────────────────────────────────────
    st.divider()
    st.subheader(t("trade_pending_orders"))

    try:
        pending = client.get_trade_pending()
    except APIError:
        pending = []

    if not pending:
        st.info(t("trade_no_pending"))
    else:
        # Fetch live prices for pending symbols
        pending_syms = list({p["symbol"] for p in pending})
        pend_prices: dict[str, float] = {}
        for sym in pending_syms:
            try:
                pend_prices[sym] = _price_in_ils(sym, _usd_ils())
            except Exception:
                pass

        hdr = st.columns([1.5, 1, 1, 1.5, 1.5, 1.5, 1.5, 1])
        for col, label in zip(hdr, [
            t("trade_col_symbol"), t("trade_col_action"), t("trade_col_units"),
            t("trade_col_type"), t("trade_col_trigger"), t("trade_col_current_price"),
            t("trade_col_created"), "",
        ]):
            col.markdown(f"**{label}**")

        for order in pending:
            sym     = order["symbol"]
            row     = st.columns([1.5, 1, 1, 1.5, 1.5, 1.5, 1.5, 1])
            row[0].write(f"**{sym}**")
            row[1].write(t(f"trade_{order['action']}"))
            row[2].write(f"{float(order['units']):.4f}")
            row[3].write(t(f"trade_{order['order_type']}"))
            row[4].write(fmt_ils(float(order["trigger_price"])))
            live_p = pend_prices.get(sym)
            row[5].write(fmt_ils(live_p) if live_p else "—")
            created = order.get("created_at", "")[:16].replace("T", " ")
            row[6].write(created)
            if row[7].button(t("trade_cancel_order_btn"), key=f"cxl_{order['id']}"):
                try:
                    r = client.delete_trade_order(order["id"])
                    if r.get("success"):
                        st.success(t("trade_order_cancelled"))
                        st.rerun()
                except APIError as e:
                    st.error(str(e))

    # ── Transaction History ───────────────────────────────────────────────────
    with st.expander(t("trade_history"), expanded=False):
        try:
            history = client.get_trade_history(limit=50)
        except APIError:
            history = []

        if not history:
            st.info(t("trade_no_history"))
        else:
            df_hist = pd.DataFrame([{
                t("trade_hist_date"):   h["executed_at"][:19].replace("T", " "),
                t("trade_hist_symbol"): h["symbol"],
                t("trade_hist_action"): t(f"trade_{h['action']}"),
                t("trade_hist_units"):  f"{float(h['units']):.4f}",
                t("trade_hist_price"):  fmt_ils(float(h["price_ils"])),
                t("trade_hist_total"):  fmt_ils(float(h["total_ils"])),
                t("trade_hist_type"):   t(f"trade_{h['order_type']}"),
            } for h in history])
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
