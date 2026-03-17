import { Router, Request, Response } from 'express';
import axios from 'axios';
import yahooFinance from 'yahoo-finance2';
import { getBatchQuotes, getQuote, getHistory } from '../services/yahooFinanceService';
import { logger } from '../utils/logger';

const router = Router();

// GET /api/stocks/search?q=apple
// Uses Yahoo Finance's autoc endpoint — no crumb, no cookies, no header overflow.
router.get('/search', async (req: Request, res: Response) => {
  const q = String(req.query.q ?? '').trim();
  if (!q) { res.status(400).json({ error: 'q is required' }); return; }
  try {
    const autoc = await axios.get('https://query2.finance.yahoo.com/v1/finance/search', {
      params: { q, quotesCount: 10, newsCount: 0, enableFuzzyQuery: false },
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1)',
        'Accept':     'application/json',
      },
      timeout: 12_000,
      maxRedirects: 3,
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const quotes = ((autoc.data?.quotes ?? []) as any[])
      .filter((r: { symbol?: string; quoteType?: string }) => r.symbol && r.quoteType !== 'OPTION')
      .slice(0, 10)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .map((r: any) => ({
        symbol:   r.symbol                                as string,
        name:     (r.longname || r.shortname || r.symbol) as string,
        typeDisp: (r.typeDisp || r.quoteType || 'EQUITY') as string,
        exchange: (r.exchange || '')                      as string,
      }));

    res.json({ quotes });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    logger.error('Stock search failed', { query: q, error: msg });
    res.status(500).json({ error: `Search failed: ${msg}` });
  }
});

// GET /api/stocks/:ticker/detail — rich metadata (sector, beta, PE, 52-wk, etc.)
router.get('/:ticker/detail', async (req: Request, res: Response) => {
  const ticker = req.params.ticker;
  try {
    const [quoteRes, summaryRes] = await Promise.allSettled([
      getQuote(ticker),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (yahooFinance as any).quoteSummary(
        ticker,
        { modules: ['price', 'summaryDetail', 'assetProfile', 'defaultKeyStatistics'] },
        { validateResult: false },
      ),
    ]);

    const q = quoteRes.status   === 'fulfilled' ? quoteRes.value   : null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const s = summaryRes.status === 'fulfilled' ? (summaryRes.value as any) : null;

    res.json({
      symbol:        ticker,
      name:          q?.name        ?? ticker,
      price:         q?.price       ?? 0,
      changePercent: q?.changePercent ?? 0,
      currency:      q?.currency    ?? 'USD',
      marketState:   q?.marketState ?? 'CLOSED',
      marketCap:     s?.price?.marketCap             ?? s?.summaryDetail?.marketCap ?? null,
      pe:            s?.summaryDetail?.trailingPE    ?? null,
      volume:        s?.price?.regularMarketVolume   ?? s?.summaryDetail?.volume    ?? null,
      week52High:    s?.summaryDetail?.fiftyTwoWeekHigh ?? null,
      week52Low:     s?.summaryDetail?.fiftyTwoWeekLow  ?? null,
      sector:        s?.assetProfile?.sector         ?? null,
      industry:      s?.assetProfile?.industry       ?? null,
      beta:          s?.summaryDetail?.beta          ?? s?.defaultKeyStatistics?.beta ?? null,
    });
  } catch (err) {
    logger.error(`Detail fetch failed for ${ticker}`, err);
    res.status(500).json({ error: `Failed to fetch detail for ${ticker}` });
  }
});

// GET /api/stocks?tickers=LUMI.TA,TEVA.TA
router.get('/', async (req: Request, res: Response) => {
  const raw = (req.query.tickers as string) ?? '';
  const tickers = raw.split(',').map(t => t.trim()).filter(Boolean);

  if (!tickers.length) {
    res.status(400).json({ error: 'Provide at least one ticker via ?tickers=X,Y' });
    return;
  }

  try {
    const quotes = await getBatchQuotes(tickers);
    res.json(quotes);
  } catch (err) {
    logger.error('Failed to fetch batch quotes', err);
    res.status(500).json({ error: 'Failed to fetch stock data' });
  }
});

// GET /api/stocks/:ticker/history?period=3mo
router.get('/:ticker/history', async (req: Request, res: Response) => {
  const period = (req.query.period as string) || '3mo';
  try {
    const bars = await getHistory(req.params.ticker, period as any);
    res.json(bars);
  } catch (err) {
    logger.error(`Failed to fetch history for ${req.params.ticker}`, err);
    res.status(500).json({ error: `Failed to fetch history for ${req.params.ticker}` });
  }
});

// GET /api/stocks/:ticker
router.get('/:ticker', async (req: Request, res: Response) => {
  try {
    const quote = await getQuote(req.params.ticker);
    res.json(quote);
  } catch (err) {
    logger.error(`Failed to fetch quote for ${req.params.ticker}`, err);
    res.status(404).json({ error: `No data found for ticker: ${req.params.ticker}` });
  }
});

export default router;
