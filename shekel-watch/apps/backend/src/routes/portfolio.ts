/**
 * Portfolio analysis & AI suggestion endpoints.
 *
 * GET  /api/portfolio/analysis?symbols=AAPL,TEVA.TA
 *   Returns per-symbol metadata (sector, beta, PE, 52-wk, 30-day volatility)
 *   plus the current USD/ILS rate for client-side ILS conversion.
 *
 * POST /api/portfolio/suggestions
 *   Body: { positions, risk_level, language }
 *   Returns GPT-4o-mini suggestions personalised to the portfolio + risk preference.
 */

import { Router, Request, Response } from 'express';
import yahooFinance from 'yahoo-finance2';
import OpenAI from 'openai';
import { requireAuth } from '../middleware/auth';
import { getHistory } from '../services/yahooFinanceService';
import { getUsdIlsRate } from '../services/currencyService';
import { config } from '../config';
import { logger } from '../utils/logger';

const router = Router();
const openai = new OpenAI({ apiKey: config.OPENAI_API_KEY });

// ── Helpers ──────────────────────────────────────────────────────────────────

function stdDev(values: number[]): number {
  if (values.length < 2) return 0;
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((a, b) => a + (b - mean) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
}

async function getSymbolMeta(ticker: string) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const summaryRes = await (yahooFinance as any).quoteSummary(ticker, {
    modules: ['price', 'summaryDetail', 'assetProfile', 'defaultKeyStatistics'],
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  }).catch(() => null) as any;

  // 30-day daily volatility
  let volatility30d = 0;
  try {
    const bars = await getHistory(ticker, '1mo');
    if (bars.length >= 2) {
      const returns = bars.slice(1).map((b, i) =>
        bars[i].close > 0 ? (b.close - bars[i].close) / bars[i].close : 0
      );
      volatility30d = parseFloat((stdDev(returns) * 100).toFixed(4));
    }
  } catch { /* skip volatility if history unavailable */ }

  return {
    marketCap:  summaryRes?.price?.marketCap             ?? summaryRes?.summaryDetail?.marketCap ?? null,
    pe:         summaryRes?.summaryDetail?.trailingPE    ?? null,
    volume:     summaryRes?.price?.regularMarketVolume   ?? summaryRes?.summaryDetail?.volume    ?? null,
    week52High: summaryRes?.summaryDetail?.fiftyTwoWeekHigh ?? null,
    week52Low:  summaryRes?.summaryDetail?.fiftyTwoWeekLow  ?? null,
    sector:     summaryRes?.assetProfile?.sector         ?? null,
    industry:   summaryRes?.assetProfile?.industry       ?? null,
    beta:       summaryRes?.summaryDetail?.beta          ?? summaryRes?.defaultKeyStatistics?.beta ?? null,
    volatility30d,
  };
}

// ── GET /api/portfolio/analysis?symbols=AAPL,MSFT ────────────────────────────

router.get('/analysis', requireAuth, async (req: Request, res: Response) => {
  const raw = String(req.query.symbols ?? '').trim();
  if (!raw) { res.status(400).json({ error: 'symbols query param required' }); return; }

  const symbols = raw.split(',').map(s => s.trim()).filter(Boolean).slice(0, 20);

  try {
    const [usdIls, ...metaResults] = await Promise.allSettled([
      getUsdIlsRate(),
      ...symbols.map(s => getSymbolMeta(s)),
    ]);

    const rate = usdIls.status === 'fulfilled' ? usdIls.value.rate : 3.7;

    const symbolMap: Record<string, ReturnType<typeof getSymbolMeta> extends Promise<infer T> ? T : never> = {};
    symbols.forEach((sym, i) => {
      const r = metaResults[i];
      if (r.status === 'fulfilled') symbolMap[sym] = r.value;
    });

    res.json({ symbols: symbolMap, usdIls: rate });
  } catch (err) {
    logger.error('Portfolio analysis failed', err);
    res.status(500).json({ error: 'Analysis failed' });
  }
});

// ── POST /api/portfolio/suggestions ──────────────────────────────────────────

interface PositionSummary {
  symbol:          string;
  name:            string;
  allocation_ils:  number;
  current_value_ils: number;
  pnl_pct:         number;
  weight_pct:      number;
  sector:          string | null;
  beta:            number | null;
  volatility30d:   number;
}

router.post('/suggestions', requireAuth, async (req: Request, res: Response) => {
  const { positions, risk_level, language } = req.body as {
    positions:  PositionSummary[];
    risk_level: 'low' | 'medium' | 'high';
    language:   'en' | 'he';
  };

  if (!positions?.length) { res.status(400).json({ error: 'positions required' }); return; }

  const lang    = language === 'he' ? 'Hebrew' : 'English';
  const isHe    = language === 'he';
  const riskMap = { low: isHe ? 'נמוך' : 'Low', medium: isHe ? 'בינוני' : 'Medium', high: isHe ? 'גבוה' : 'High' };

  // Build position summary string
  const posLines = positions.map(p =>
    `  - ${p.symbol} (${p.name}): ₪${p.allocation_ils.toLocaleString()} allocated` +
    `, current value ₪${p.current_value_ils.toLocaleString()}` +
    `, P&L ${p.pnl_pct >= 0 ? '+' : ''}${p.pnl_pct.toFixed(1)}%` +
    `, weight ${p.weight_pct.toFixed(1)}%` +
    (p.sector ? `, sector: ${p.sector}` : '') +
    (p.beta    ? `, beta: ${p.beta.toFixed(2)}` : '') +
    (p.volatility30d ? `, 30d-vol: ${p.volatility30d.toFixed(2)}%` : '')
  ).join('\n');

  const sectorMap: Record<string, number> = {};
  positions.forEach(p => {
    const s = p.sector ?? 'Other';
    sectorMap[s] = (sectorMap[s] ?? 0) + p.weight_pct;
  });
  const sectorLines = Object.entries(sectorMap)
    .map(([s, w]) => `  ${s}: ${w.toFixed(1)}%`)
    .join('\n');

  const prompt = `You are a portfolio advisor. Respond entirely in ${lang}.

User's selected risk level: ${riskMap[risk_level] ?? risk_level}

Portfolio positions:
${posLines}

Sector breakdown:
${sectorLines}

Please provide 4–6 concise, actionable suggestions covering:
1. Rebalancing (flag overweight/underweight positions, suggest adjustments)
2. Risk alignment (compare portfolio beta/volatility to the selected risk level — flag misalignment)
3. Sector concentration warnings (flag sectors > 40% of portfolio)
4. Specific add/reduce/replace ideas based on P&L trends and diversification
5. Any notable momentum or risk alerts

Format as a numbered list. Be specific, reference actual symbols and percentages from the data.`;

  try {
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 700,
      temperature: 0.5,
    });
    const suggestions = completion.choices[0]?.message?.content?.trim() ?? 'No suggestions available.';
    res.json({ suggestions, generatedAt: new Date().toISOString() });
  } catch (err) {
    logger.error('Portfolio suggestions failed', err);
    res.status(500).json({ error: 'AI suggestions failed' });
  }
});

export default router;
