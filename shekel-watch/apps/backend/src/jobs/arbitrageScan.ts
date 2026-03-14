import { getQuote } from '../services/yahooFinanceService';
import { getUsdIlsRate } from '../services/currencyService';
import { supabase } from '../config/supabase';
import { nowInIsrael } from '../utils/israelTime';
import { logger } from '../utils/logger';

// Mirrors the frontend DUAL_LISTED data — single source of truth on the server
const DUAL_LISTED = [
  { symbol: 'TEVA', taseSymbol: 'TEVA.TA' },
  { symbol: 'CHKP', taseSymbol: 'CHKP.TA' },
  { symbol: 'NICE', taseSymbol: 'NICE.TA'  },
  { symbol: 'MNDY', taseSymbol: 'MNDY.TA'  },
  { symbol: 'WIX',  taseSymbol: 'WIX.TA'   },
  { symbol: 'GLBE', taseSymbol: 'GLBE.TA'  },
];

function isMarketHours(): boolean {
  const now   = nowInIsrael();
  const h     = now.hour();
  const m     = now.minute();
  const total = h * 60 + m;
  // 09:00–17:30 IST, Mon–Fri (day 1 = Mon, 5 = Fri in dayjs)
  const day = now.day(); // 0=Sun, 1=Mon … 6=Sat
  return day >= 1 && day <= 5 && total >= 9 * 60 && total <= 17 * 60 + 30;
}

export async function runArbitrageScan(): Promise<void> {
  if (!isMarketHours()) {
    logger.info('Arbitrage scan: outside market hours, skipping');
    return;
  }

  logger.info('Arbitrage scan: starting');

  let usdIls: number;
  try {
    const rate = await getUsdIlsRate();
    usdIls = rate.rate;
  } catch (err) {
    logger.error('Arbitrage scan: failed to fetch USD/ILS', err);
    return;
  }

  for (const pair of DUAL_LISTED) {
    try {
      const [nyseQuote, taseQuote] = await Promise.all([
        getQuote(pair.symbol),
        getQuote(pair.taseSymbol),
      ]);

      const { error } = await supabase.from('price_snapshots').insert({
        symbol:        pair.symbol,
        tase_price_ils: taseQuote.price,
        ny_price_usd:   nyseQuote.price,
        exchange_rate:  usdIls,
      });

      if (error) {
        logger.error(`Arbitrage scan: insert failed for ${pair.symbol}`, error);
      } else {
        logger.info(`Arbitrage scan: ${pair.symbol} TASE=₪${taseQuote.price.toFixed(2)} NYSE=$${nyseQuote.price.toFixed(2)} rate=${usdIls.toFixed(4)}`);
      }
    } catch (err) {
      logger.error(`Arbitrage scan: error processing ${pair.symbol}`, err);
    }
  }

  logger.info('Arbitrage scan: complete');
}
