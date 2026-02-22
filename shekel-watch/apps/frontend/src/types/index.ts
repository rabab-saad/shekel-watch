export interface RateResult {
  rate: number;
  source: string;
  fetchedAt: string;
}

export interface QuoteResult {
  ticker: string;
  name: string;
  price: number;
  previousClose: number;
  changePercent: number;
  currency: string;
  marketState: string;
}

export interface ArbitrageResult {
  name:            string;
  tickerTase:      string;
  tickerForeign:   string;
  tasePriceIls:    number;
  foreignPriceUsd: number;
  foreignPriceIls: number;
  usdIlsRate:      number;
  gapPercent:      number;
  direction:       'TASE_PREMIUM' | 'FOREIGN_PREMIUM' | 'PARITY';
}

export interface WatchlistItem {
  id:      string;
  ticker:  string;
  market:  'TASE' | 'NYSE' | 'NASDAQ';
  addedAt: string;
}
