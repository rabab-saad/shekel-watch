import { Router, Request, Response } from 'express';
import axios from 'axios';
import yahooFinance from 'yahoo-finance2';
import { getBatchQuotes, getQuote, getHistory } from '../services/yahooFinanceService';
import { logger } from '../utils/logger';

const router = Router();

// ── Yahoo Finance crumb cache ─────────────────────────────────────────────────
// Yahoo's v1 search API requires a session cookie + crumb since ~2024.
// We use axios (already a dependency) which handles redirects and SSL
// more reliably than the global fetch on Railway's network.
const _YH_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36';
let _yhCrumb  = '';
let _yhCookie = '';
let _yhExpiry = 0;

async function ensureYahooCrumb(): Promise<void> {
  if (_yhCrumb && Date.now() < _yhExpiry) return;

  // 1. Visit Yahoo Finance to obtain a session cookie
  const homeRes = await axios.get('https://finance.yahoo.com/', {
    headers: { 'User-Agent': _YH_UA, 'Accept': 'text/html' },
    maxRedirects: 5,
    timeout: 10_000,
  });
  const rawCookies: string[] = Array.isArray(homeRes.headers['set-cookie'])
    ? homeRes.headers['set-cookie']
    : [];
  _yhCookie = rawCookies.map((c: string) => c.split(';')[0].trim()).join('; ');

  // 2. Exchange cookie for a crumb
  const crumbRes = await axios.get('https://query1.finance.yahoo.com/v1/test/getcrumb', {
    headers: { 'User-Agent': _YH_UA, 'Cookie': _yhCookie },
    timeout: 10_000,
    responseType: 'text',
  });
  _yhCrumb  = String(crumbRes.data).trim();
  _yhExpiry = Date.now() + 25 * 60 * 1000; // cache 25 minutes
}

// GET /api/stocks/search?q=apple
router.get('/search', async (req: Request, res: Response) => {
  const q = String(req.query.q ?? '').trim();
  if (!q) { res.status(400).json({ error: 'q is required' }); return; }
  try {
    await ensureYahooCrumb();

    const searchRes = await axios.get('https://query1.finance.yahoo.com/v1/finance/search', {
      params: {
        q,
        quotesCount: 10,
        newsCount: 0,
        enableFuzzyQuery: false,
        quotesQueryId: 'tss_match',
        crumb: _yhCrumb,
      },
      headers: {
        'User-Agent':      _YH_UA,
        'Cookie':          _yhCookie,
        'Accept':          'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer':         'https://finance.yahoo.com/',
      },
      timeout: 12_000,
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const quotes = ((searchRes.data?.quotes ?? []) as any[])
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
    _yhCrumb  = '';   // invalidate cache so next call retries
    _yhExpiry = 0;
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
