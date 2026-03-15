/**
 * /api/crew  —  Proxy to the Python FastAPI microservice.
 * Exposes CrewAI multi-agent features (market summary, WhatsApp alert
 * composition) and currency arbitrage detection to the Node backend / React
 * frontend without the caller needing to know about the Python service.
 */

import { Router, Request, Response } from 'express';
import axios from 'axios';
import { getAllRates } from '../services/currencyService';
import { getBatchQuotes } from '../services/yahooFinanceService';
import { logger } from '../utils/logger';

const router = Router();

const PYTHON_URL = process.env.PYTHON_API_URL || 'http://localhost:8501';

const TICKERS = ['LUMI.TA', 'HARL.TA', 'TEVA.TA', 'ESLT.TA', 'NICE.TA', 'CHKP.TA'];

// ── GET /api/crew/summary ─────────────────────────────────────────────────────
// CrewAI multi-agent market summary (richer than the direct-GPT /api/summary)
router.get('/summary', async (req: Request, res: Response) => {
  try {
    const [{ rates, usdIls }, stocks] = await Promise.all([
      getAllRates(),
      getBatchQuotes(TICKERS),
    ]);

    const currencyData = rates
      .map(r => `${r.code}/USD: ${r.vsUsd.toFixed(4)}, ${r.code}/ILS: ${r.vsIls.toFixed(4)}`)
      .join('\n');

    const marketData =
      stocks
        .map(s => `${s.ticker} (${s.name}): ₪${s.price} (${s.changePercent >= 0 ? '+' : ''}${s.changePercent.toFixed(2)}%)`)
        .join('\n') + `\nUSD/ILS: ${usdIls}`;

    const { data } = await axios.post(
      `${PYTHON_URL}/market-summary`,
      { market_data: marketData, currency_data: currencyData },
      { timeout: 60_000 }
    );

    res.json({ summary: data.summary, generatedAt: new Date().toISOString() });
  } catch (err) {
    logger.error('crew/summary failed', err);
    res.status(500).json({ error: 'AI summary unavailable' });
  }
});

// ── GET /api/crew/currency-arbitrage ─────────────────────────────────────────
// Detects gaps between direct X/ILS rates and implied X→USD→ILS conversion
router.get('/currency-arbitrage', async (_req: Request, res: Response) => {
  try {
    const { rates, usdIls } = await getAllRates();
    const vsUsd: Record<string, number> = Object.fromEntries(
      rates.map(r => [r.code, r.vsUsd])
    );

    const { data } = await axios.post(
      `${PYTHON_URL}/currency-arbitrage`,
      { vs_usd: vsUsd, usd_ils: usdIls },
      { timeout: 15_000 }
    );

    res.json(data);
  } catch (err) {
    logger.error('crew/currency-arbitrage failed', err);
    res.status(500).json({ error: 'Currency arbitrage unavailable' });
  }
});

// ── POST /api/crew/compose-alert ─────────────────────────────────────────────
// CrewAI composes an emoji-rich WhatsApp alert from arbitrage opportunity lists
router.post('/compose-alert', async (req: Request, res: Response) => {
  try {
    const { currency_opps = [], stock_opps = [] } = req.body;

    const { data } = await axios.post(
      `${PYTHON_URL}/compose-alert`,
      { currency_opps, stock_opps },
      { timeout: 30_000 }
    );

    res.json(data);
  } catch (err) {
    logger.error('crew/compose-alert failed', err);
    res.status(500).json({ error: 'Alert composition unavailable' });
  }
});

export default router;
