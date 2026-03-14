import yahooFinance from 'yahoo-finance2';
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

export async function getQuote(ticker: string): Promise<QuoteResult> {
  const quote = await yahooFinance.quote(ticker);

  if (!quote.regularMarketPrice) {
    throw new Error(`No price data for ticker: ${ticker}`);
  }

  return {
    ticker,
    name:          quote.longName ?? quote.shortName ?? ticker,
    price:         quote.regularMarketPrice,
    previousClose: quote.regularMarketPreviousClose ?? 0,
    changePercent: quote.regularMarketChangePercent ?? 0,
    currency:      quote.currency ?? 'USD',
    marketState:   quote.marketState ?? 'CLOSED',
  };
}

export async function getBatchQuotes(tickers: string[]): Promise<QuoteResult[]> {
  const results = await Promise.allSettled(tickers.map(t => getQuote(t)));

  return results
    .filter((r): r is PromiseFulfilledResult<QuoteResult> => r.status === 'fulfilled')
    .map(r => r.value);
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
  // yahoo-finance2 types don't always expose `historical` — cast to any
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
