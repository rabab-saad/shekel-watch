"""
Chart rendering helpers using Plotly.
render_area_chart   — beginner mode, simple area chart
render_candlestick_chart — pro mode, candlestick + RSI + MACD subplots
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


def _parse_history(bars: list) -> pd.DataFrame:
    """Normalize raw history list from the backend into a DataFrame."""
    if not bars:
        return pd.DataFrame()
    df = pd.DataFrame(bars)
    # Handle both 'date' and 'timestamp' column names
    for col in ("date", "time", "timestamp", "t"):
        if col in df.columns:
            df["date"] = pd.to_datetime(df[col])
            break
    for price_col in ("close", "Close", "adjClose"):
        if price_col in df.columns:
            df["close"] = df[price_col]
            break
    for col in ("open", "Open"):
        if col in df.columns:
            df["open"] = df[col]
    for col in ("high", "High"):
        if col in df.columns:
            df["high"] = df[col]
    for col in ("low", "Low"):
        if col in df.columns:
            df["low"] = df[col]
    return df.sort_values("date").reset_index(drop=True)


def render_area_chart(bars: list, ticker: str = "", color: str = "#2563eb"):
    """Simple area chart for beginner mode."""
    df = _parse_history(bars)
    if df.empty or "close" not in df.columns:
        st.info("No price history available.")
        return

    fig = px.area(
        df,
        x="date",
        y="close",
        title=f"{ticker} Price History" if ticker else "Price History",
        labels={"close": "Price", "date": "Date"},
        color_discrete_sequence=[color],
    )
    fig.update_layout(
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        font_color="#f1f5f9",
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="#334155")
    fig.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig, use_container_width=True)


def _calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))


def _calc_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def render_candlestick_chart(bars: list, ticker: str = ""):
    """Pro mode: candlestick + RSI + MACD subplots."""
    df = _parse_history(bars)
    required = {"date", "open", "high", "low", "close"}
    if df.empty or not required.issubset(df.columns):
        st.info("Insufficient OHLC data for candlestick chart.")
        return

    df["rsi"] = _calc_rsi(df["close"])
    macd_line, signal_line, macd_hist = _calc_macd(df["close"])
    df["macd"] = macd_line
    df["macd_signal"] = signal_line
    df["macd_hist"] = macd_hist

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.2, 0.2],
        vertical_spacing=0.02,
        subplot_titles=(f"{ticker} Candlestick", "RSI (14)", "MACD"),
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
            name="Price",
        ),
        row=1, col=1,
    )

    # RSI
    fig.add_trace(
        go.Scatter(x=df["date"], y=df["rsi"], line=dict(color="#a78bfa", width=1.5), name="RSI"),
        row=2, col=1,
    )
    fig.add_hline(y=70, line=dict(color="#ef4444", dash="dash", width=1), row=2, col=1)
    fig.add_hline(y=30, line=dict(color="#22c55e", dash="dash", width=1), row=2, col=1)

    # MACD
    colors = ["#22c55e" if v >= 0 else "#ef4444" for v in df["macd_hist"]]
    fig.add_trace(
        go.Bar(x=df["date"], y=df["macd_hist"], marker_color=colors, name="MACD Hist", opacity=0.7),
        row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df["date"], y=df["macd"], line=dict(color="#60a5fa", width=1.5), name="MACD"),
        row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df["date"], y=df["macd_signal"], line=dict(color="#f59e0b", width=1.5), name="Signal"),
        row=3, col=1,
    )

    fig.update_layout(
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        font_color="#f1f5f9",
        height=650,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
        xaxis_rangeslider_visible=False,
    )
    for i in range(1, 4):
        fig.update_xaxes(gridcolor="#334155", row=i, col=1)
        fig.update_yaxes(gridcolor="#334155", row=i, col=1)

    st.plotly_chart(fig, use_container_width=True)
