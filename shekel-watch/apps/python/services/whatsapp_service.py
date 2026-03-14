"""
WhatsApp alert service via Green API.
Sends messages to a user's WhatsApp number when arbitrage opportunities are detected.
"""

import re
import requests
from services.config import get


def _normalise_phone(phone: str) -> str:
    """
    Strips all non-digits.  Ensures Israeli numbers start with 972 (not 0).
    Returns e.g. "972501234567".
    """
    digits = re.sub(r"\D", "", phone)
    # Israeli local format: 05xxxxxxxx → 97205xxxxxxxx? No — strip the leading 0
    if digits.startswith("0") and len(digits) == 10:
        digits = "972" + digits[1:]
    return digits


def send_whatsapp(phone: str, message: str) -> dict:
    """
    Send a WhatsApp message via Green API.

    phone   – phone number (any format, e.g. "+972-50-123-4567" or "0501234567")
    message – plain text message
    """
    instance_id = get("GREENAPI_INSTANCE_ID")
    api_token   = get("GREENAPI_TOKEN")

    if not instance_id or not api_token:
        return {"success": False, "error": "Green API credentials not configured"}

    chat_id = f"{_normalise_phone(phone)}@c.us"
    url     = (
        f"https://api.green-api.com/waInstance{instance_id}"
        f"/sendMessage/{api_token}"
    )

    try:
        resp = requests.post(
            url,
            json={"chatId": chat_id, "message": message},
            timeout=10,
        )
        data = resp.json()
        # Green API returns {"idMessage": "..."} on success
        if "idMessage" in data:
            return {"success": True, "id": data["idMessage"]}
        return {"success": False, "error": str(data)}
    except Exception as e:
        return {"success": False, "error": str(e)}
