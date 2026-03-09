declare module 'yahoo-finance2' {
  interface Quote {
    longName?: string;
    shortName?: string;
    regularMarketPrice?: number;
    regularMarketPreviousClose?: number;
    regularMarketChangePercent?: number;
    currency?: string;
    marketState?: string;
  }

  const yahooFinance: {
    setGlobalConfig(opts: { validation?: { logErrors?: boolean; logOptionsErrors?: boolean } }): void;
    quote(ticker: string): Promise<Quote>;
  };

  export default yahooFinance;
}
