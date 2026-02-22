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
