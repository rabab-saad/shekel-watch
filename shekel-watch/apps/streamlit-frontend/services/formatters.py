"""
Formatting helpers — currency, percentages, Hebrew labels.
"""


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
    """English risk label for a 0–10 risk score."""
    s = float(score)
    if s <= 3:
        return "Low"
    elif s <= 6:
        return "Medium"
    return "High"


def risk_label_he(score: int | float) -> str:
    """Hebrew risk label for a 0–10 risk score."""
    s = float(score)
    if s <= 3:
        return "נמוך"
    elif s <= 6:
        return "בינוני"
    return "גבוה"


def arb_direction_label(direction: str) -> str:
    """Human-readable arbitrage direction label."""
    mapping = {
        "TASE_PREMIUM": "TASE Premium 📈",
        "FOREIGN_PREMIUM": "Foreign Premium 📉",
        "PARITY": "Parity ≈",
    }
    return mapping.get(direction, direction)


def arb_direction_label_he(direction: str) -> str:
    mapping = {
        "TASE_PREMIUM": "פרמיה בבורסה 📈",
        "FOREIGN_PREMIUM": "פרמיה בחו\"ל 📉",
        "PARITY": "שוויון ≈",
    }
    return mapping.get(direction, direction)


def mode_label(mode: str | None) -> str:
    if mode == "beginner":
        return "🌱 Simple / פשוט"
    elif mode == "pro":
        return "⚡ Pro / מקצועי"
    return "Unknown"
