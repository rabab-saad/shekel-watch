import { getUsdIlsRate } from '../services/currencyService';
import { supabase } from '../config/supabase';
import { logger } from '../utils/logger';

export async function runRateSnapshot(): Promise<void> {
  try {
    const rate = await getUsdIlsRate();
    const { error } = await supabase.from('rate_snapshots').insert({
      pair:       'USD_ILS',
      rate:       rate.rate,
      source:     rate.source,
      snapped_at: rate.fetchedAt,
    });
    if (error) logger.error('Rate snapshot insert failed', error);
    else logger.info(`Rate snapshot saved: ₪${rate.rate}`);
  } catch (err) {
    logger.error('Rate snapshot job failed', err);
  }
}
