import { getBatchQuotes } from './yahooFinanceService';
import { getUsdIlsRate } from './currencyService';
import { supabase } from '../config/supabase';

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

export async function calculateArbitrageGaps(): Promise<ArbitrageResult[]> {
  const { data: pairs, error } = await supabase
    .from('dual_listed')
    .select('*');

  if (error || !pairs?.length) return [];

  const { rate: usdIlsRate } = await getUsdIlsRate();

  const allTickers = [
    ...pairs.map((p: { ticker_tase: string }) => p.ticker_tase),
    ...pairs.map((p: { ticker_nyse: string }) => p.ticker_nyse),
  ];

  const quotes = await getBatchQuotes(allTickers);
  const quoteMap = new Map(quotes.map(q => [q.ticker, q]));

  const results: ArbitrageResult[] = [];

  for (const pair of pairs) {
    const taseQuote    = quoteMap.get(pair.ticker_tase);
    const foreignQuote = quoteMap.get(pair.ticker_nyse);

    if (!taseQuote || !foreignQuote) continue;

    const tasePriceIls    = taseQuote.price;
    const foreignPriceIls = foreignQuote.price * usdIlsRate;
    const gapPercent      = ((tasePriceIls / foreignPriceIls) - 1) * 100;

    results.push({
      name:            pair.name,
      tickerTase:      pair.ticker_tase,
      tickerForeign:   pair.ticker_nyse,
      tasePriceIls,
      foreignPriceUsd: foreignQuote.price,
      foreignPriceIls,
      usdIlsRate,
      gapPercent:      parseFloat(gapPercent.toFixed(3)),
      direction:
        gapPercent > 0.5  ? 'TASE_PREMIUM'
        : gapPercent < -0.5 ? 'FOREIGN_PREMIUM'
        : 'PARITY',
    });
  }

  results.sort((a, b) => Math.abs(b.gapPercent) - Math.abs(a.gapPercent));
  return results;
}
