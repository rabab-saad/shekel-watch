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
  dayHigh?: number;
  dayLow?: number;
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
    dayHigh:       data.high  ? parseFloat(data.high)  : undefined,
    dayLow:        data.low   ? parseFloat(data.low)   : undefined,
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
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      dayHigh:       (quote as any).regularMarketDayHigh ?? undefined,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      dayLow:        (quote as any).regularMarketDayLow  ?? undefined,
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
    } catch (err) {
      logger.warn(`getBatchQuotes: failed to fetch ${ticker}`, { error: err instanceof Error ? err.message : String(err) });
    }
    await sleep(300); // 300 ms between tickers to avoid rate-limiting
  }
  return results;
}

export interface NewsItem {
  title:     string;
  summary:   string;
  publisher: string;
}

export interface IndexQuote {
  ticker:        string;
  name:          string;
  price:         number;
  changePercent: number;
}

const INDEX_TICKERS: { ticker: string; name: string; searchQuery: string }[] = [
  { ticker: '^GSPC',     name: 'S&P 500',    searchQuery: 'S&P 500 market'        },
  { ticker: '^IXIC',     name: 'Nasdaq',     searchQuery: 'Nasdaq stock market'   },
  { ticker: '^DJI',      name: 'Dow Jones',  searchQuery: 'Dow Jones industrial'  },
  { ticker: '^TA35.TA',  name: 'TA-35',      searchQuery: 'Tel Aviv stock exchange TASE' },
  { ticker: '^TA125.TA', name: 'TA-125',     searchQuery: 'Israel stock market'   },
];

async function fetchNewsForQuery(query: string): Promise<NewsItem[]> {
  try {
    const { data } = await axios.get('https://query2.finance.yahoo.com/v1/finance/search', {
      params: { q: query, quotesCount: 0, newsCount: 5, enableFuzzyQuery: false },
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1)',
        'Accept':     'application/json',
      },
      timeout: 10_000,
    });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return ((data?.news ?? []) as any[]).slice(0, 5).map((n: any) => ({
      title:     n.title     ?? '',
      summary:   n.summary   ?? '',
      publisher: n.publisher ?? '',
    }));
  } catch {
    return [];
  }
}

export async function getMarketNews(): Promise<{ news: NewsItem[]; indices: IndexQuote[] }> {
  const [indicesResults, newsResults] = await Promise.all([
    Promise.allSettled(
      INDEX_TICKERS.map(async ({ ticker, name }) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const q = await (yahooFinance as any).quote(ticker, {}, { validateResult: false }) as any;
        return {
          ticker,
          name,
          price:         q?.regularMarketPrice         ?? 0,
          changePercent: q?.regularMarketChangePercent ?? 0,
        } as IndexQuote;
      }),
    ),
    Promise.allSettled(INDEX_TICKERS.map(idx => fetchNewsForQuery(idx.searchQuery))),
  ]);

  const indices = indicesResults
    .filter((r): r is PromiseFulfilledResult<IndexQuote> => r.status === 'fulfilled')
    .map(r => r.value);

  const seen = new Set<string>();
  const news = newsResults
    .filter((r): r is PromiseFulfilledResult<NewsItem[]> => r.status === 'fulfilled')
    .flatMap(r => r.value)
    .filter(n => {
      if (!n.title || seen.has(n.title)) return false;
      seen.add(n.title);
      return true;
    })
    .slice(0, 15);

  return { news, indices };
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

const periodToRange: Record<HistoryPeriod, string> = {
  '1wk': '5d',
  '1mo': '1mo',
  '3mo': '3mo',
  '6mo': '6mo',
  '1y':  '1y',
  '2y':  '2y',
};

async function getHistoryFromYahooChart(ticker: string, period: HistoryPeriod): Promise<HistoryBar[]> {
  const { interval } = periodToParams[period] ?? periodToParams['3mo'];
  const range = periodToRange[period] ?? '3mo';
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(ticker)}`;
  const { data } = await axios.get(url, {
    params: { interval, range, includePrePost: false },
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1)',
      'Accept': 'application/json',
    },
    timeout: 12_000,
  });

  const result = data?.chart?.result?.[0];
  if (!result) throw new Error(`No chart data for ${ticker}`);

  const timestamps: number[]    = result.timestamp ?? [];
  const q                        = result.indicators?.quote?.[0] ?? {};
  const opens: number[]          = q.open   ?? [];
  const highs: number[]          = q.high   ?? [];
  const lows: number[]           = q.low    ?? [];
  const closes: number[]         = q.close  ?? [];
  const volumes: number[]        = q.volume ?? [];

  return timestamps
    .map((ts, i) => ({
      time:   new Date(ts * 1000).toISOString().slice(0, 10),
      open:   opens[i],
      high:   highs[i],
      low:    lows[i],
      close:  closes[i],
      volume: volumes[i] ?? 0,
    }))
    .filter(r => r.open != null && r.close != null);
}

export async function getHistory(ticker: string, period: HistoryPeriod = '3mo'): Promise<HistoryBar[]> {
  // Primary: yahoo-finance2 historical (with validation suppressed)
  try {
    const { period1, interval } = periodToParams[period] ?? periodToParams['3mo'];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const rows: any[] = await (yahooFinance as any).historical(
      ticker,
      { period1, interval },
      { validateResult: false },
    );

    const bars = rows
      .filter(r => r.open != null && r.close != null)
      .map(r => ({
        time:   (r.date as Date).toISOString().slice(0, 10),
        open:   r.open  as number,
        high:   r.high  as number,
        low:    r.low   as number,
        close:  r.close as number,
        volume: (r.volume ?? 0) as number,
      }));

    if (bars.length > 0) return bars;
    throw new Error('Empty result from historical');
  } catch (err) {
    logger.warn(`yahoo-finance2 historical failed for ${ticker}, falling back to chart API`, err);
    return getHistoryFromYahooChart(ticker, period);
  }
}
