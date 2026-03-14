import { getHistory } from '../services/yahooFinanceService';
import { supabase } from '../config/supabase';
import { logger } from '../utils/logger';

function stddev(values: number[]): number {
  if (values.length < 2) return 0;
  const mean = values.reduce((s, v) => s + v, 0) / values.length;
  const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
}

function volatilityToRisk(vol: number): number {
  if (vol < 1) return 1;
  if (vol < 2) return 3;
  if (vol < 3) return 5;
  if (vol < 5) return 7;
  return 10;
}

export async function runUpdateRiskScores(): Promise<void> {
  logger.info('Risk score update: starting');

  try {
    // Fetch all distinct tickers from watchlist
    const { data: rows, error } = await supabase
      .from('watchlist')
      .select('ticker');

    if (error || !rows) {
      logger.error('Risk score update: failed to fetch watchlist', error);
      return;
    }

    const tickers = [...new Set(rows.map((r: { ticker: string }) => r.ticker))];
    logger.info(`Risk score update: processing ${tickers.length} tickers`);

    for (const ticker of tickers) {
      try {
        const bars = await getHistory(ticker, '1mo');
        if (bars.length < 3) {
          logger.warn(`Risk score update: not enough data for ${ticker}`);
          continue;
        }

        const closes = bars.map(b => b.close);
        const dailyReturns: number[] = [];
        for (let i = 1; i < closes.length; i++) {
          dailyReturns.push((closes[i] - closes[i - 1]) / closes[i - 1]);
        }

        const vol       = stddev(dailyReturns) * 100; // as percentage
        const riskScore = volatilityToRisk(vol);

        const { error: upErr } = await supabase
          .from('watchlist')
          .update({ risk_score: riskScore })
          .eq('ticker', ticker);

        if (upErr) {
          logger.error(`Risk score update: DB update failed for ${ticker}`, upErr);
        } else {
          logger.info(`Risk score update: ${ticker} vol=${vol.toFixed(2)}% → score=${riskScore}`);
        }
      } catch (err) {
        logger.error(`Risk score update: error processing ${ticker}`, err);
      }
    }

    logger.info('Risk score update: complete');
  } catch (err) {
    logger.error('Risk score update: job failed', err);
  }
}
