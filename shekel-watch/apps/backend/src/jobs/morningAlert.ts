import { supabase } from '../config/supabase';
import { getUsdIlsRate } from '../services/currencyService';
import { getBatchQuotes } from '../services/yahooFinanceService';
import { sendWhatsAppMessage } from '../services/whatsappService';
import { nowInIsrael } from '../utils/israelTime';
import { logger } from '../utils/logger';
import OpenAI from 'openai';
import { config } from '../config';

const openai = new OpenAI({ apiKey: config.OPENAI_API_KEY });

// ── Shared data helpers ────────────────────────────────────────────────────────

async function getYesterdayRate(): Promise<number | null> {
  const { data } = await supabase
    .from('rate_snapshots')
    .select('rate')
    .eq('pair', 'USD_ILS')
    .order('snapped_at', { ascending: false })
    .limit(2);

  if (!data || data.length < 2) return null;
  return (data[1] as { rate: number }).rate;
}

interface TopGap {
  symbol:     string;
  gapPercent: number;
}

async function getTopArbitrageGap(): Promise<TopGap | null> {
  const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();

  const { data } = await supabase
    .from('price_snapshots')
    .select('symbol, tase_price_ils, ny_price_usd, exchange_rate')
    .gte('captured_at', twoHoursAgo);

  if (!data?.length) return null;

  type Snap = {
    symbol:         string;
    tase_price_ils: number;
    ny_price_usd:   number;
    exchange_rate:  number;
  };

  let best: TopGap | null = null;

  for (const row of data as Snap[]) {
    if (!row.ny_price_usd || !row.exchange_rate) continue;
    const implied  = row.ny_price_usd * row.exchange_rate;
    const gapPct   = ((row.tase_price_ils - implied) / implied) * 100;
    if (!best || Math.abs(gapPct) > Math.abs(best.gapPercent)) {
      best = { symbol: row.symbol, gapPercent: gapPct };
    }
  }

  return best;
}

// ── Per-user helpers ───────────────────────────────────────────────────────────

async function getUserPortfolioPnL(userId: string, currentRate: number): Promise<number> {
  const { data: holdings } = await supabase
    .from('virtual_portfolio')
    .select('symbol, quantity, avg_buy_price, currency')
    .eq('user_id', userId);

  if (!holdings?.length) return 0;

  type Holding = {
    symbol:        string;
    quantity:      number;
    avg_buy_price: number;
    currency:      string;
  };

  const symbols  = (holdings as Holding[]).map(h => h.symbol);
  const quotes   = await getBatchQuotes(symbols);
  const priceMap = new Map(quotes.map(q => [q.ticker, q.price]));

  let pnl = 0;
  for (const h of holdings as Holding[]) {
    let currentPrice = priceMap.get(h.symbol) ?? 0;
    if (h.currency === 'USD') currentPrice *= currentRate;
    pnl += (currentPrice - h.avg_buy_price) * h.quantity;
  }

  return pnl;
}

async function generateBeginnerTip(rate: number): Promise<string> {
  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{
        role: 'user',
        content:
          `Generate one short investment tip in Hebrew for a beginner Israeli investor. ` +
          `Max 15 words. Today's USD/ILS: ${rate.toFixed(4)}.`,
      }],
    });
    return response.choices[0].message.content?.trim() ?? '';
  } catch (err) {
    logger.warn('Morning alert: failed to generate beginner tip', err);
    return 'בדקו את המגמות בשוק לפני ביצוע פעולות';
  }
}

// ── Main job ──────────────────────────────────────────────────────────────────

export async function runMorningAlert(): Promise<void> {
  // Guard: only run if it is actually 08:xx in Israel (handles DST)
  const israelHour = nowInIsrael().hour();
  if (israelHour !== 8) {
    logger.info(`Skipping morning alert — Israel hour is ${israelHour}, not 8`);
    return;
  }

  // 1. Fetch eligible users
  const { data: users, error } = await supabase
    .from('profiles')
    .select('id, display_name, phone_number, trading_mode')
    .eq('whatsapp_enabled', true)
    .eq('morning_summary_enabled', true)
    .not('phone_number', 'is', null)
    .not('trading_mode', 'is', null);

  if (error || !users?.length) {
    logger.info('No eligible users for morning alert');
    return;
  }

  // 2. Fetch shared data once (parallel)
  const [rateResult, yesterdayRate, topGap] = await Promise.all([
    getUsdIlsRate(),
    getYesterdayRate(),
    getTopArbitrageGap(),
  ]);

  const rate       = rateResult.rate;
  const rateChange = yesterdayRate
    ? parseFloat((((rate - yesterdayRate) / yesterdayRate) * 100).toFixed(2))
    : 0;

  logger.info(
    `Morning alert: rate=₪${rate.toFixed(4)} rateChange=${rateChange}%` +
    ` topGap=${topGap ? `${topGap.symbol} ${topGap.gapPercent.toFixed(2)}%` : 'none'}`
  );

  // Generate beginner tip once (reused for all beginner users)
  const hasBeginners = (users as { trading_mode: string }[]).some(u => u.trading_mode === 'beginner');
  const aiTip = hasBeginners ? await generateBeginnerTip(rate) : '';

  // 3. Per-user send
  for (const user of users as {
    id:           string;
    display_name: string | null;
    phone_number: string;
    trading_mode: 'beginner' | 'pro';
  }[]) {
    if (!user.phone_number) continue;

    const name = user.display_name ?? 'משקיע';

    try {
      let message: string;

      if (user.trading_mode === 'beginner') {
        // Fetch personal virtual portfolio P&L
        let pnlStr = '—';
        try {
          const pnl = await getUserPortfolioPnL(user.id, rate);
          pnlStr = pnl >= 0
            ? `📈 +₪${pnl.toFixed(2)}`
            : `📉 ₪${Math.abs(pnl).toFixed(2)}`;
        } catch (err) {
          logger.warn(`Morning alert: P&L fetch failed for ${user.id}`, err);
        }

        const rateArrow = rateChange >= 0 ? '⬆️ +' : '⬇️ ';
        message =
          `בוקר טוב ${name}! 🌅\n` +
          `הדולר עומד על ₪${rate.toFixed(4)} (${rateArrow}${rateChange}% מאתמול)\n` +
          `הפורטפוליו הוירטואלי שלך: ${pnlStr}\n` +
          `💡 טיפ: ${aiTip}`;

      } else {
        // PRO
        const rateSign = rateChange >= 0 ? '+' : '';
        const gapLine  = topGap
          ? `Top gap: ${topGap.symbol} ${topGap.gapPercent >= 0 ? '+' : ''}${topGap.gapPercent.toFixed(2)}% (TASE vs NYSE)`
          : 'Top gap: No significant gaps detected';

        message =
          `⚡ ${name} — Market opens in ~90 min\n` +
          `USD/ILS: ${rate.toFixed(4)} (${rateSign}${rateChange}%)\n` +
          `${gapLine}\n` +
          `Check arbitrage scanner before open 📊`;
      }

      await sendWhatsAppMessage(user.phone_number, message);
      logger.info(`Morning alert sent to ${user.phone_number} (${user.trading_mode})`);
    } catch (err) {
      logger.error(`Failed to send morning alert to ${user.phone_number}`, err);
    }
  }
}
