"""
Formatting helpers — currency, percentages, language-aware labels.
"""

import streamlit as st


def fmt_ils(value: float, decimals: int = 2) -> str:
    """Format as Israeli Shekel: ₪3,456.78"""
    return f"₪{value:,.{decimals}f}"


def fmt_usd(value: float, decimals: int = 2) -> str:
    """Format as US Dollar: $1,234.56"""
    return f"${value:,.{decimals}f}"


def fmt_pct(value: float, decimals: int = 2, sign: bool = True) -> str:
    """Format percentage: +1.23% or -0.45%"""
    prefix = "+" if sign and value >= 0 else ""
    return f"{prefix}{value:.{decimals}f}%"


def pct_delta_color(value: float) -> str:
    """Return 'normal' (green) or 'inverse' (red) for st.metric delta_color."""
    return "normal" if value >= 0 else "inverse"


def risk_label(score: int | float) -> str:
    """Risk label for a 0–10 score — language-aware via t()."""
    from utils.i18n import t
    s = float(score)
    if s <= 3:
        return t("risk_low")
    elif s <= 6:
        return t("risk_medium")
    return t("risk_high")


# Keep for backwards compatibility — callers that explicitly need English
def risk_label_en(score: int | float) -> str:
    s = float(score)
    if s <= 3:   return "Low"
    elif s <= 6: return "Medium"
    return "High"


def arb_direction_label(direction: str) -> str:
    """Human-readable arbitrage direction label — language-aware."""
    from utils.i18n import t
    mapping = {
        "TASE_PREMIUM":    t("tase_premium_label"),
        "FOREIGN_PREMIUM": t("foreign_premium_label"),
        "PARITY":          t("parity_label"),
    }
    return mapping.get(direction, direction)


def mode_label(mode: str | None) -> str:
    from utils.i18n import t
    if mode == "beginner":
        return t("mode_beginner")
    elif mode == "pro":
        return t("mode_pro")
    return mode or ""


# ── Kept for any legacy callers ───────────────────────────────────────────────

def risk_label_he(score: int | float) -> str:
    s = float(score)
    if s <= 3:   return "נמוך"
    elif s <= 6: return "בינוני"
    return "גבוה"


def arb_direction_label_he(direction: str) -> str:
    mapping = {
        "TASE_PREMIUM":    'פרמיה בבורסה 📈',
        "FOREIGN_PREMIUM": 'פרמיה בחו"ל 📉',
        "PARITY":          "שוויון ≈",
    }
    return mapping.get(direction, direction)
