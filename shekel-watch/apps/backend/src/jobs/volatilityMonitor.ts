import { supabase } from '../config/supabase';
import { getUsdIlsRate } from '../services/currencyService';
import { sendWhatsAppMessage } from '../services/whatsappService';
import { nowInIsrael } from '../utils/israelTime';
import { logger } from '../utils/logger';

// ── Market-hours gate ─────────────────────────────────────────────────────────

function isMarketHours(): boolean {
  const now  = nowInIsrael();
  const day  = now.day(); // 0=Sun … 6=Sat; TASE trades Sun–Thu
  const mins = now.hour() * 60 + now.minute();
  return day >= 0 && day <= 4 && mins >= 10 * 60 && mins <= 17 * 60 + 30;
}

// ── Message composers ─────────────────────────────────────────────────────────

function buildBeginnerMessage(
  displayName: string,
  symbol: string,
  change: number,
  currentPrice: number
): string {
  const sign = change >= 0 ? '+' : '';
  return (
    `📊 שלום ${displayName}!\n` +
    `${symbol} זז ${sign}${change.toFixed(2)}% ב-10 דקות האחרונות.\n` +
    `מחיר נוכחי: ₪${currentPrice.toFixed(2)}\n` +
    `שווה לבדוק את הפורטפוליו הוירטואלי שלך 👀`
  );
}

function buildProMessage(
  symbol: string,
  change: number,
  currentPrice: number,
  usdIls: number
): string {
  const sign = change >= 0 ? '+' : '';
  return (
    `⚡ VOLATILITY ALERT\n` +
    `${symbol} moved ${sign}${change.toFixed(2)}% in 10 min\n` +
    `Current: ${currentPrice.toFixed(2)} | Volume spike detected\n` +
    `USD/ILS: ${usdIls.toFixed(4)}`
  );
}

// ── Main job ──────────────────────────────────────────────────────────────────

export async function runVolatilityMonitor(): Promise<void> {
  if (!isMarketHours()) return;

  logger.info('Volatility monitor: starting scan');

  // 1. Load alert-eligible users
  const { data: users, error: usersErr } = await supabase
    .from('profiles')
    .select('id, display_name, phone_number, trading_mode')
    .eq('whatsapp_enabled', true)
    .not('phone_number', 'is', null)
    .not('trading_mode', 'is', null);

  if (usersErr || !users?.length) {
    logger.info('Volatility monitor: no eligible users');
    return;
  }

  // 2. Collect all distinct symbols from those users' watchlists
  const userIds = users.map((u: { id: string }) => u.id);

  const { data: watchlistRows, error: wlErr } = await supabase
    .from('watchlist')
    .select('user_id, ticker')
    .in('user_id', userIds);

  if (wlErr || !watchlistRows?.length) {
    logger.info('Volatility monitor: no watchlist entries');
    return;
  }

  // Map symbol → [user_ids]
  const symbolUserMap = new Map<string, string[]>();
  for (const row of watchlistRows as { user_id: string; ticker: string }[]) {
    const existing = symbolUserMap.get(row.ticker) ?? [];
    existing.push(row.user_id);
    symbolUserMap.set(row.ticker, existing);
  }

  // Fetch live USD/ILS once
  let usdIls = 3.7;
  try {
    const rate = await getUsdIlsRate();
    usdIls = rate.rate;
  } catch {
    logger.warn('Volatility monitor: USD/ILS fetch failed, using fallback');
  }

  const cutoff = new Date(Date.now() - 15 * 60 * 1000).toISOString();

  for (const [symbol, watcherIds] of symbolUserMap) {
    try {
      // 2a. Fetch last 2 snapshots within 15 minutes
      const { data: snaps } = await supabase
        .from('price_snapshots')
        .select('tase_price_ils, ny_price_usd, exchange_rate, captured_at')
        .eq('symbol', symbol)
        .gte('captured_at', cutoff)
        .order('captured_at', { ascending: false })
        .limit(2);

      if (!snaps || snaps.length < 2) continue;

      // Use tase_price_ils if available, else ny_price_usd converted
      const price = (snap: typeof snaps[0]) =>
        snap.tase_price_ils != null
          ? snap.tase_price_ils
          : (snap.ny_price_usd ?? 0) * (snap.exchange_rate ?? usdIls);

      const price2 = price(snaps[0]); // newest
      const price1 = price(snaps[1]); // older

      if (price1 === 0) continue;

      const change = ((price2 - price1) / price1) * 100;

      // 2d. Skip small moves
      if (Math.abs(change) < 0.4) continue;

      logger.info(`Volatility monitor: ${symbol} changed ${change.toFixed(2)}%`);

      // 3. Process each watcher
      for (const userId of watcherIds) {
        const user = users.find((u: { id: string }) => u.id === userId);
        if (!user) continue;

        // 3a. Check cooldown (30 minutes)
        const cooldownCutoff = new Date(Date.now() - 30 * 60 * 1000).toISOString();
        const { data: cooldown } = await supabase
          .from('alert_cooldowns')
          .select('last_alerted_at')
          .eq('user_id', userId)
          .eq('symbol', symbol)
          .single();

        if (cooldown?.last_alerted_at && cooldown.last_alerted_at > cooldownCutoff) {
          logger.info(`Volatility monitor: skipping ${symbol} for ${userId} (cooldown)`);
          continue;
        }

        // 3b. Compose message
        const message = user.trading_mode === 'pro'
          ? buildProMessage(symbol, change, price2, usdIls)
          : buildBeginnerMessage(user.display_name ?? 'משתמש', symbol, change, price2);

        // 3c. Send via Green API (exact same call as morningAlert.ts)
        try {
          await sendWhatsAppMessage(user.phone_number, message);
          logger.info(`Volatility monitor: alert sent to ${user.phone_number} for ${symbol}`);
        } catch (err) {
          logger.error(`Volatility monitor: send failed for ${user.phone_number}`, err);
          continue;
        }

        // 3d. Upsert cooldown
        await supabase
          .from('alert_cooldowns')
          .upsert(
            { user_id: userId, symbol, last_alerted_at: new Date().toISOString() },
            { onConflict: 'user_id,symbol' }
          );
      }
    } catch (err) {
      logger.error(`Volatility monitor: error processing ${symbol}`, err);
    }
  }

  logger.info('Volatility monitor: scan complete');
}
