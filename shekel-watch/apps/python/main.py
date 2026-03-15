"""
Shekel-Watch Python microservice.
Exposes CrewAI multi-agent features and currency arbitrage as a REST API
consumed by the Node.js backend.  No UI – the React frontend is the only UI.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from services.arbitrage_service import get_currency_arbitrage
from services.crew_service import compose_whatsapp_alert, get_market_summary

app = FastAPI(title="Shekel-Watch Python API", version="1.0.0")


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Market summary (CrewAI multi-agent) ────────────────────────────────────────

class SummaryReq(BaseModel):
    market_data: str
    currency_data: str


@app.post("/market-summary")
def market_summary(req: SummaryReq):
    result = get_market_summary(req.market_data, req.currency_data)
    return {"summary": result}


# ── WhatsApp alert composition (CrewAI) ────────────────────────────────────────

class AlertReq(BaseModel):
    currency_opps: List[Dict[str, Any]] = []
    stock_opps: List[Dict[str, Any]] = []


@app.post("/compose-alert")
def compose_alert(req: AlertReq):
    result = compose_whatsapp_alert(req.currency_opps, req.stock_opps)
    return {"message": result}


# ── Currency arbitrage (direct X/ILS vs implied X→USD→ILS) ────────────────────

class CurrencyArbReq(BaseModel):
    vs_usd: Dict[str, float]   # { "EUR": 1.085, "GBP": 1.263, ... }
    usd_ils: float


@app.post("/currency-arbitrage")
def currency_arbitrage(req: CurrencyArbReq):
    df = get_currency_arbitrage(req.vs_usd, req.usd_ils)
    return {"opportunities": df.to_dict(orient="records") if not df.empty else []}


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PYTHON_PORT", "8501"))
    uvicorn.run(app, host="0.0.0.0", port=port)
