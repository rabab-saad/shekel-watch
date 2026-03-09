import { supabase } from '../config/supabase';
import { getUsdIlsRate } from '../services/currencyService';
import { calculateArbitrageGaps } from '../services/arbitrageService';
import { getBatchQuotes } from '../services/yahooFinanceService';
import { generateMarketSummary } from '../services/chatgptService';
import { sendWhatsAppMessage } from '../services/whatsappService';
import { nowInIsrael } from '../utils/israelTime';
import { logger } from '../utils/logger';

const TASE_TICKERS = ['LUMI.TA', 'TEVA.TA', 'ESLT.TA', 'HARL.TA', 'CHKP.TA'];

export async function runMorningAlert(): Promise<void> {
  // Guard: only run if it is actually 08:xx in Israel (handles DST)
  const israelHour = nowInIsrael().hour();
  if (israelHour !== 8) {
    logger.info(`Skipping morning alert — Israel hour is ${israelHour}, not 8`);
    return;
  }

  const { data: users, error } = await supabase
    .from('profiles')
    .select('phone_number, language')
    .eq('whatsapp_enabled', true)
    .not('phone_number', 'is', null);

  if (error || !users?.length) {
    logger.info('No WhatsApp-enabled users for morning alert');
    return;
  }

  const [rate, stocks, gaps] = await Promise.all([
    getUsdIlsRate(),
    getBatchQuotes(TASE_TICKERS),
    calculateArbitrageGaps(),
  ]);

  // Pre-generate both language summaries
  const [enSummary, heSummary] = await Promise.all([
    generateMarketSummary({ rate, stocks, arbitrage: gaps, language: 'en' }),
    generateMarketSummary({ rate, stocks, arbitrage: gaps, language: 'he' }),
  ]);

  const summaries = { en: enSummary, he: heSummary };
  const dateStr = nowInIsrael().format('dddd, DD/MM/YYYY');

  for (const user of users) {
    if (!user.phone_number) continue;
    const lang = (user.language ?? 'en') as 'en' | 'he';
    const summary = summaries[lang];

    const message = lang === 'he'
      ? `🌅 *בוקר טוב — ${dateStr}*\n💵 דולר: ₪${rate.rate.toFixed(4)}\n\n${summary}`
      : `🌅 *Good morning — ${dateStr}*\n💵 USD: ₪${rate.rate.toFixed(4)}\n\n${summary}`;

    try {
      await sendWhatsAppMessage(user.phone_number, message);
      logger.info(`Morning alert sent to ${user.phone_number}`);
    } catch (err) {
      logger.error(`Failed to send morning alert to ${user.phone_number}`, err);
    }
  }
}
