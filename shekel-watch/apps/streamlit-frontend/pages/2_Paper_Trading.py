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

tab_search, tab_portfolio, tab_analysis, tab_ai = st.tabs(
    [t("tab_search"), t("tab_portfolio"), t("tab_analysis"), t("tab_ai")]
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SEARCH & ADD
# ═══════════════════════════════════════════════════════════════════════════════

with tab_search:
    st.subheader(t("search_instruments"))
    st.caption(t("search_caption"))

    col_q, col_btn = st.columns([4, 1])
    with col_q:
        query = st.text_input(
            "Search",
            placeholder=t("search_placeholder"),
            label_visibility="collapsed",
            key="search_query",
        )
    with col_btn:
        do_search = st.button(t("search_btn"), use_container_width=True)

    if do_search and query:
        with st.spinner(t("searching")):
            try:
                result = client.search_stocks(query)
                hits   = result.get("quotes", [])
            except APIError as e:
                hits = []
                st.error(t("search_failed_msg").format(error=e.message))

        if not hits:
            st.info(t("no_results"))
        else:
            st.markdown(t("results_found").format(n=len(hits)))
            for i, h in enumerate(hits):
                ca, cb, cc, cd, ce = st.columns([1.5, 3.5, 1.2, 1.2, 1])
                ca.markdown(f"**{h.get('symbol', '')}**")
                cb.write(h.get("name", ""))
                cc.write(h.get("typeDisp", ""))
                cd.write(h.get("exchange", ""))
                if ce.button(t("select"), key=f"sel_{h['symbol']}_{i}"):
                    st.session_state["selected_ticker"] = h["symbol"]
                    st.session_state["selected_name"]   = h.get("name", h["symbol"])

    # ── Detail Panel ──────────────────────────────────────────────────────────

    selected = st.session_state.get("selected_ticker")
    if selected:
        st.divider()
        sel_name = st.session_state.get("selected_name", selected)
        st.subheader(f"📋 {selected}  ·  {sel_name}")

        with st.spinner(t("loading_symbol").format(ticker=selected)):
            try:
                detail          = client.get_stock_detail(selected)
                is_detail_stale = False
                st.session_state[f"_detail_{selected}"] = detail
            except APIError:
                detail          = st.session_state.get(f"_detail_{selected}", {})
                is_detail_stale = bool(detail)

        if not detail:
            st.warning(t("could_not_load_detail"))
        else:
            if is_detail_stale:
                st.warning(t("stale_data_warning"))

            # Key metrics row
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            cur_symbol = detail.get("currency", "")
            m1.metric(t("price"),    f"{cur_symbol} {detail.get('price', 0):.4f}")
            m2.metric(t("change"),   fmt_pct(detail.get("changePercent", 0)))
            m3.metric(t("mkt_cap"),  _fmt_large(detail.get("marketCap")))
            m4.metric(t("pe"),       f"{detail.get('pe'):.1f}" if detail.get("pe") else "—")
            m5.metric(t("week52_high"), f"{detail.get('week52High'):.2f}" if detail.get("week52High") else "—")
            m6.metric(t("week52_low"),  f"{detail.get('week52Low'):.2f}"  if detail.get("week52Low")  else "—")

            sec_parts = [detail.get("sector"), detail.get("industry")]
            sec_line  = "  ·  ".join(s for s in sec_parts if s)
            if sec_line:
                st.caption(t("sector_industry").format(val=sec_line))

            # Price chart
            period_opts = {
                "1 Day": "1wk", "1 Week": "1wk", "1 Month": "1mo",
                "3 Months": "3mo", "1 Year": "1y",
            }
            period_label = st.select_slider(
                t("chart_period"), options=list(period_opts.keys()), value="1 Month",
                key="detail_period",
            )
            try:
                bars = client.get_stock_history(selected, period_opts[period_label])
            except APIError:
                bars = []

            if bars:
                df_bars = pd.DataFrame(bars)
                fig = px.area(
                    df_bars, x="time", y="close",
                    title=f"{selected} — {period_label}",
                    labels={"time": "", "close": "Price"},
                    template="plotly_dark",
                    color_discrete_sequence=["#38bdf8"],
                )
                fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=280)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(t("chart_unavailable"))

            # Add to Portfolio
            st.markdown(f"#### {t('add_to_portfolio_heading')}")

            existing_alloc = next(
                (float(p["quantity"]) for p in positions if p["symbol"] == selected), 0.0
            )
            if existing_alloc > 0:
                st.info(t("already_allocated").format(amount=fmt_ils(existing_alloc), ticker=selected))

            max_add = remaining + existing_alloc

            with st.form(f"add_form_{selected}"):
                alloc = st.number_input(
                    t("allocation_amount"),
                    min_value=100.0,
                    max_value=float(max(max_add, 100.0)),
                    value=float(min(10_000.0, max(max_add, 100.0))),
                    step=100.0,
                    format="%.0f",
                    help=t("available_budget_help").format(budget=fmt_ils(max_add)),
                )
                add_submitted = st.form_submit_button(t("add_btn"), use_container_width=True)

            if add_submitted:
                if alloc > max_add + 0.01:
                    st.error(t("exceeds_budget").format(budget=fmt_ils(max_add)))
                else:
                    usd_rate      = _usd_ils()
                    cur_price_ils = _price_in_ils(selected, usd_rate)
                    if cur_price_ils <= 0:
                        st.error(t("fetch_price_failed"))
                    else:
                        res = upsert_portfolio_position(
                            token, user_id,
                            symbol        = selected,
                            allocation_ils= alloc,
                            price_ils     = cur_price_ils,
                            currency      = detail.get("currency", "USD"),
                        )
                        if res.get("success"):
                            st.success(t("added_success").format(amount=fmt_ils(alloc), ticker=selected))
                            _load_profile.clear()
                            _live_quote.clear()
                            st.rerun()
                        else:
                            st.error(t("failed_to_save").format(error=res.get("error")))

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
