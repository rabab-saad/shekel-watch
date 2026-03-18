"""
APIClient — all HTTP calls to the Express backend.
Never calls Supabase or external APIs for data the backend already serves.
"""

import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:3001").rstrip("/")


class APIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class APIClient:
    def __init__(self, token: str | None = None):
        self.base_url = BACKEND_URL
        self.token = token or st.session_state.get("access_token")

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def get(self, path: str, params: dict | None = None) -> dict | list:
        url = f"{self.base_url}{path}"
        resp = requests.get(url, params=params, headers=self._headers(), timeout=15)
        if not resp.ok:
            raise APIError(resp.status_code, resp.text[:200])
        return resp.json()

    def post(self, path: str, body: dict | None = None) -> dict | list:
        url = f"{self.base_url}{path}"
        resp = requests.post(url, json=body or {}, headers=self._headers(), timeout=15)
        if not resp.ok:
            raise APIError(resp.status_code, resp.text[:200])
        return resp.json()

    # ── Convenience wrappers ──────────────────────────────────────────────────

    def get_usd_ils(self) -> dict:
        """GET /api/rates/usd-ils → { rate, source }"""
        return self.get("/api/rates/usd-ils")

    def get_all_rates(self) -> dict:
        """GET /api/rates/all → { rates: [{code, vsUsd, vsIls}], usdIls }"""
        return self.get("/api/rates/all")

    def get_stocks(self, tickers: list[str]) -> list:
        """GET /api/stocks?tickers=X,Y → [{ticker, name, price, changePercent, ...}]"""
        return self.get("/api/stocks", params={"tickers": ",".join(tickers)})

    def get_stock(self, ticker: str) -> dict:
        """GET /api/stocks/:ticker → {ticker, name, price, changePercent, ...}"""
        return self.get(f"/api/stocks/{ticker}")

    def get_stock_history(self, ticker: str, period: str = "3mo") -> list:
        """GET /api/stocks/:ticker/history?period=3mo → [{date, open, high, low, close, volume}]"""
        return self.get(f"/api/stocks/{ticker}/history", params={"period": period})

    def get_arbitrage(self) -> list:
        """GET /api/arbitrage → [{name, taseTicker, nyseTicker, gapPercent, direction, ...}]"""
        return self.get("/api/arbitrage")

    def get_summary(self, lang: str = "en") -> dict:
        """GET /api/summary?lang=en → { summary, language, generatedAt }"""
        return self.get("/api/summary", params={"lang": lang})

    def get_inflation(self) -> dict:
        """GET /api/inflation → { cpiCurrent, cpiBaseline2020, usdIls, usdIlsBaseline2020, timestamp }"""
        return self.get("/api/inflation")

    def post_paper_trade(self, symbol: str, action: str, quantity: int, current_price: float) -> dict:
        """POST /api/paper-trade → { success, newBalance, action, symbol, quantity }"""
        return self.post("/api/paper-trade", {
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "currentPrice": current_price,
        })

    def post_explain(self, term: str, language: str = "en") -> dict:
        """POST /api/explain → { term, explanation, language }"""
        return self.post("/api/explain", {"term": term, "language": language})

    def search_stocks(self, query: str) -> dict:
        """GET /api/stocks/search?q=... → { quotes: [{symbol, name, typeDisp, exchange}] }"""
        return self.get("/api/stocks/search", params={"q": query})

    def get_stock_detail(self, ticker: str) -> dict:
        """GET /api/stocks/:ticker/detail → { symbol, name, price, changePercent, currency,
        marketCap, pe, volume, week52High, week52Low, sector, industry, beta }"""
        return self.get(f"/api/stocks/{ticker}/detail")

    # ── Trade simulation ──────────────────────────────────────────────────────

    def get_trade_balance(self) -> dict:
        """GET /api/trade/balance → { balance_ils }"""
        return self.get("/api/trade/balance")

    def get_trade_history(self, limit: int = 50) -> list:
        """GET /api/trade/history → [{symbol, action, units, price_ils, total_ils, order_type, executed_at}]"""
        return self.get("/api/trade/history", params={"limit": limit})

    def get_trade_pending(self) -> list:
        """GET /api/trade/pending → [{id, symbol, action, units, order_type, trigger_price, status, created_at}]"""
        return self.get("/api/trade/pending")

    def post_trade_execute(self, symbol: str, action: str, units: float, price_ils: float) -> dict:
        """POST /api/trade/execute → { success, newBalance }"""
        return self.post("/api/trade/execute", {
            "symbol": symbol, "action": action,
            "units": units, "priceIls": price_ils,
        })

    def post_trade_order(
        self, symbol: str, action: str, units: float,
        order_type: str, trigger_price: float,
    ) -> dict:
        """POST /api/trade/order → { success, order }"""
        return self.post("/api/trade/order", {
            "symbol": symbol, "action": action, "units": units,
            "orderType": order_type, "triggerPrice": trigger_price,
        })

    def delete_trade_order(self, order_id: str) -> dict:
        """DELETE /api/trade/order/:id → { success }"""
        url  = f"{self.base_url}/api/trade/order/{order_id}"
        resp = requests.delete(url, headers=self._headers(), timeout=15)
        if not resp.ok:
            raise APIError(resp.status_code, resp.text[:200])
        return resp.json()

    def get_market_news(self, lang: str = "en") -> dict:
        """GET /api/market-news?lang=en → { usAnalysis, israelAnalysis, indices, generatedAt }"""
        return self.get("/api/market-news", params={"lang": lang})

    def get_portfolio_analysis(self, symbols: list[str]) -> dict:
        """GET /api/portfolio/analysis?symbols=... → { symbols: {sym: meta}, usdIls }"""
        return self.get("/api/portfolio/analysis", params={"symbols": ",".join(symbols)})

    def post_portfolio_suggestions(
        self,
        positions: list[dict],
        risk_level: str = "medium",
        language: str = "en",
    ) -> dict:
        """POST /api/portfolio/suggestions → { suggestions, generatedAt }"""
        return self.post("/api/portfolio/suggestions", {
            "positions": positions,
            "risk_level": risk_level,
            "language": language,
        })
