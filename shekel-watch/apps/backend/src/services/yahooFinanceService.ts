import yahooFinance from 'yahoo-finance2';
import axios from 'axios';
import { config } from '../config';
import { logger } from '../utils/logger';

export interface QuoteResult {
  ticker: string;
  name: string;
  price: number;
  previousClose: number;
  changePercent: number;
  currency: string;
  marketState: string;
}

// Suppress noisy validation warnings
yahooFinance.setGlobalConfig({
  validation: { logErrors: false, logOptionsErrors: false },
});

// ── In-memory quote cache (60-second TTL) ─────────────────────────────────────
const quoteCache = new Map<string, { value: QuoteResult; expiresAt: number }>();
const QUOTE_TTL_MS = 60_000;

// ── Twelve Data fallback ───────────────────────────────────────────────────────
// Converts yahoo-format tickers to Twelve Data format: NICE.TA → NICE:TASE
function toTwelveDataSymbol(ticker: string): string {
  return ticker.endsWith('.TA') ? ticker.replace('.TA', ':TASE') : ticker;
}

async function getQuoteFromTwelveData(ticker: string): Promise<QuoteResult> {
  const symbol = toTwelveDataSymbol(ticker);
  const { data } = await axios.get('https://api.twelvedata.com/quote', {
    params: { symbol, apikey: config.TWELVE_DATA_API_KEY },
    timeout: 8000,
  });

  if (data.status === 'error' || !data.close) {
    throw new Error(`Twelve Data: no data for ${symbol}`);
  }

  const price         = parseFloat(data.close);
  const previousClose = parseFloat(data.previous_close ?? data.close);
  const changePercent = previousClose ? ((price - previousClose) / previousClose) * 100 : 0;

  return {
    ticker,
    name:          data.name ?? ticker,
    price,
    previousClose,
    changePercent: parseFloat(data.percent_change ?? changePercent.toFixed(4)),
    currency:      data.currency ?? 'USD',
    marketState:   data.is_market_open ? 'REGULAR' : 'CLOSED',
  };
}

// ── Public API ────────────────────────────────────────────────────────────────

export async function getQuote(ticker: string): Promise<QuoteResult> {
  const cached = quoteCache.get(ticker);
  if (cached && cached.expiresAt > Date.now()) return cached.value;

  let result: QuoteResult;

  // Primary: Yahoo Finance
  try {
    const quote = await yahooFinance.quote(ticker);
    if (!quote.regularMarketPrice) throw new Error('No price');

    result = {
      ticker,
      name:          quote.longName ?? quote.shortName ?? ticker,
      price:         quote.regularMarketPrice,
      previousClose: quote.regularMarketPreviousClose ?? 0,
      changePercent: quote.regularMarketChangePercent ?? 0,
      currency:      quote.currency ?? 'USD',
      marketState:   quote.marketState ?? 'CLOSED',
    };
  } catch {
    // Fallback: Twelve Data (handles Yahoo rate-limits)
    logger.warn(`Yahoo Finance failed for ${ticker}, falling back to Twelve Data`);
    result = await getQuoteFromTwelveData(ticker);
  }

  quoteCache.set(ticker, { value: result, expiresAt: Date.now() + QUOTE_TTL_MS });
  return result;
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function getBatchQuotes(tickers: string[]): Promise<QuoteResult[]> {
  const results: QuoteResult[] = [];
  for (const ticker of tickers) {
    try {
      results.push(await getQuote(ticker));
    } catch {
      // skip failed tickers
    }
    await sleep(300); // 300 ms between tickers to avoid rate-limiting
  }
  return results;
}

export interface HistoryBar {
  time:   string; // "YYYY-MM-DD"
  open:   number;
  high:   number;
  low:    number;
  close:  number;
  volume: number;
}

type HistoryPeriod = '1wk' | '1mo' | '3mo' | '6mo' | '1y' | '2y';

const periodToParams: Record<HistoryPeriod, { period1: Date; interval: '1d' | '1wk' }> = {
  '1wk': { period1: new Date(Date.now() - 7   * 86400_000), interval: '1d' },
  '1mo': { period1: new Date(Date.now() - 30  * 86400_000), interval: '1d' },
  '3mo': { period1: new Date(Date.now() - 90  * 86400_000), interval: '1d' },
  '6mo': { period1: new Date(Date.now() - 180 * 86400_000), interval: '1d' },
  '1y':  { period1: new Date(Date.now() - 365 * 86400_000), interval: '1d' },
  '2y':  { period1: new Date(Date.now() - 730 * 86400_000), interval: '1wk' },
};

export async function getHistory(ticker: string, period: HistoryPeriod = '3mo'): Promise<HistoryBar[]> {
  const { period1, interval } = periodToParams[period] ?? periodToParams['3mo'];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rows: any[] = await (yahooFinance as any).historical(ticker, { period1, interval });

  return rows
    .filter(r => r.open != null && r.close != null)
    .map(r => ({
      time:   (r.date as Date).toISOString().slice(0, 10),
      open:   r.open  as number,
      high:   r.high  as number,
      low:    r.low   as number,
      close:  r.close as number,
      volume: (r.volume ?? 0) as number,
    }));
}
