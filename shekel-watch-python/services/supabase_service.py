from supabase import create_client, Client
from services.config import get

SUPABASE_URL      = get("SUPABASE_URL")
SUPABASE_ANON_KEY = get("SUPABASE_ANON_KEY")


def get_client(access_token: str = None) -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if access_token:
        client.postgrest.auth(access_token)
    return client


def sign_in(email: str, password: str) -> dict:
    try:
        client = get_client()
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        return {
            "success": True,
            "user": response.user,
            "access_token": response.session.access_token,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def sign_up(email: str, password: str, display_name: str = "") -> dict:
    try:
        client = get_client()
        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"display_name": display_name}},
        })
        return {"success": True, "user": response.user}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_profile(access_token: str, user_id: str) -> dict:
    try:
        client = get_client(access_token)
        response = client.table("profiles").select("*").eq("id", user_id).single().execute()
        return response.data or {}
    except Exception:
        return {}


def get_watchlist(access_token: str, user_id: str) -> list:
    try:
        client = get_client(access_token)
        response = client.table("watchlist").select("*").eq("user_id", user_id).execute()
        return response.data or []
    except Exception:
        return []


def add_to_watchlist(access_token: str, user_id: str, ticker: str, market: str) -> dict:
    try:
        client = get_client(access_token)
        client.table("watchlist").insert({
            "user_id": user_id,
            "ticker": ticker,
            "market": market,
        }).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def remove_from_watchlist(access_token: str, user_id: str, ticker: str) -> dict:
    try:
        client = get_client(access_token)
        client.table("watchlist").delete().eq("user_id", user_id).eq("ticker", ticker).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
