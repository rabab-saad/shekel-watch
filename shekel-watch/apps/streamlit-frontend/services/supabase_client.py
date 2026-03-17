"""
Supabase client — Auth + direct DB reads only.
Data fetching that the Express backend already handles must use api_client.py instead.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
_SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

if not _SUPABASE_URL or not _SUPABASE_ANON_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")


def get_anon_client() -> Client:
    """Unauthenticated client — for sign-in / sign-up / magic link only."""
    return create_client(_SUPABASE_URL, _SUPABASE_ANON_KEY)


def get_authed_client(access_token: str) -> Client:
    """Authenticated client — RLS-aware, uses the user's JWT."""
    client = create_client(_SUPABASE_URL, _SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)
    return client


# ── Auth helpers ──────────────────────────────────────────────────────────────

def sign_in(email: str, password: str) -> dict:
    try:
        client = get_anon_client()
        resp = client.auth.sign_in_with_password({"email": email, "password": password})
        return {
            "success": True,
            "user_id": resp.user.id,
            "email": resp.user.email,
            "access_token": resp.session.access_token,
            "refresh_token": resp.session.refresh_token,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_up(email: str, password: str, display_name: str = "") -> dict:
    try:
        client = get_anon_client()
        resp = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"display_name": display_name}},
        })
        return {"success": True, "user_id": resp.user.id if resp.user else None}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_google_oauth_url(redirect_to: str) -> dict:
    """
    Start Google OAuth flow (PKCE).
    Returns {"success": True, "url": "https://accounts.google.com/..."} on success.
    The caller must redirect the user to that URL.
    After Google auth, Supabase redirects back to redirect_to with ?code=xxx in the query string.
    """
    try:
        client = get_anon_client()
        response = client.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_to,
                "scopes": "email profile",
            },
        })
        return {"success": True, "url": response.url}
    except Exception as e:
        return {"success": False, "error": str(e)}


def exchange_oauth_code(code: str) -> dict:
    """
    Exchange the ?code= query param returned by Supabase after Google auth.
    Returns the same shape as sign_in() on success.
    """
    try:
        client = get_anon_client()
        resp = client.auth.exchange_code_for_session({"auth_code": code})
        return {
            "success": True,
            "user_id": resp.user.id,
            "email": resp.user.email,
            "access_token": resp.session.access_token,
            "refresh_token": resp.session.refresh_token,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_in_magic_link(email: str) -> dict:
    try:
        client = get_anon_client()
        client.auth.sign_in_with_otp({"email": email})
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def reset_password(email: str) -> dict:
    try:
        client = get_anon_client()
        client.auth.reset_password_email(email)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_password(access_token: str, new_password: str) -> dict:
    try:
        client = get_authed_client(access_token)
        client.auth.update_user({"password": new_password})
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Profile ───────────────────────────────────────────────────────────────────

def get_profile(access_token: str, user_id: str) -> dict:
    try:
        client = get_authed_client(access_token)
        resp = client.table("profiles").select("*").eq("id", user_id).single().execute()
        return resp.data or {}
    except Exception:
        return {}


def update_profile(access_token: str, user_id: str, updates: dict) -> dict:
    try:
        client = get_authed_client(access_token)
        client.table("profiles").update(updates).eq("id", user_id).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Watchlist ─────────────────────────────────────────────────────────────────

def get_watchlist(access_token: str, user_id: str) -> list:
    try:
        client = get_authed_client(access_token)
        resp = client.table("watchlist").select("*").eq("user_id", user_id).execute()
        return resp.data or []
    except Exception:
        return []


def add_to_watchlist(access_token: str, user_id: str, ticker: str, market: str = "TASE") -> dict:
    try:
        client = get_authed_client(access_token)
        client.table("watchlist").insert({
            "user_id": user_id,
            "ticker": ticker.upper().strip(),
            "market": market,
        }).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def remove_from_watchlist(access_token: str, user_id: str, ticker: str) -> dict:
    try:
        client = get_authed_client(access_token)
        client.table("watchlist").delete().eq("user_id", user_id).eq("ticker", ticker).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Paper Trading ─────────────────────────────────────────────────────────────

def get_virtual_balance(access_token: str, user_id: str) -> dict | None:
    try:
        client = get_authed_client(access_token)
        resp = client.table("virtual_balance").select("*").eq("user_id", user_id).single().execute()
        return resp.data
    except Exception:
        return None


def upsert_virtual_balance(access_token: str, user_id: str, balance_ils: float = 100000) -> dict:
    try:
        client = get_authed_client(access_token)
        client.table("virtual_balance").upsert({
            "user_id": user_id,
            "balance_ils": balance_ils,
        }).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_virtual_portfolio(access_token: str, user_id: str) -> list:
    try:
        client = get_authed_client(access_token)
        resp = client.table("virtual_portfolio").select("*").eq("user_id", user_id).execute()
        return resp.data or []
    except Exception:
        return []


# ── Portfolio Builder ──────────────────────────────────────────────────────────
# Uses virtual_portfolio table where:
#   quantity      = allocation amount in ILS
#   avg_buy_price = price per unit in ILS at time of allocation (for P&L)
#   currency      = native currency of the asset (USD, ILS, EUR, etc.)

def upsert_portfolio_position(
    access_token: str,
    user_id: str,
    symbol: str,
    allocation_ils: float,
    price_ils: float,
    currency: str = "USD",
) -> dict:
    """
    Add or replace a portfolio position.
    allocation_ils: total NIS amount allocated.
    price_ils:      price per unit converted to ILS at time of allocation.
    """
    try:
        client = get_authed_client(access_token)
        client.table("virtual_portfolio").upsert({
            "user_id":       user_id,
            "symbol":        symbol.upper().strip(),
            "quantity":      allocation_ils,
            "avg_buy_price": price_ils,
            "currency":      currency,
        }, on_conflict="user_id,symbol").execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def remove_portfolio_position(access_token: str, user_id: str, symbol: str) -> dict:
    try:
        client = get_authed_client(access_token)
        client.table("virtual_portfolio").delete() \
            .eq("user_id", user_id) \
            .eq("symbol", symbol.upper().strip()) \
            .execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_investment_config(
    access_token: str,
    user_id: str,
    investment_amount: float | None = None,
    risk_level: str | None = None,
) -> dict:
    """Persist investment_amount and/or risk_level in the user's profile."""
    updates: dict = {}
    if investment_amount is not None:
        updates["investment_amount"] = investment_amount
    if risk_level is not None:
        updates["risk_level"] = risk_level
    if not updates:
        return {"success": True}
    return update_profile(access_token, user_id, updates)
