/**
 * Pending Order Monitor
 * Checks all pending orders against live prices and executes any that trigger.
 *
 * Trigger logic:
 *   Limit BUY        → execute if live_price <= trigger_price
 *   Limit SELL       → execute if live_price >= trigger_price
 *   Stop BUY         → market-execute if live_price >= trigger_price (breakout buy)
 *   Stop SELL        → market-execute if live_price <= trigger_price (stop-loss sell)
 *   Stop-Limit BUY   → triggered if live_price >= trigger_price, then only fill if live_price <= limit_price
 *   Stop-Limit SELL  → triggered if live_price <= trigger_price, then only fill if live_price >= limit_price
 *   Stop Loss (legacy) → execute if live_price <= trigger_price  (always sell)
 *   Take Profit (legacy) → execute if live_price >= trigger_price (always sell)
 */

import { supabase } from '../config/supabase';
import { getQuote }  from '../services/yahooFinanceService';
import { logger }    from '../utils/logger';

// ── Shared execute helper (also used by trade.ts route) ──────────────────────

export async function getOrInitBalance(userId: string): Promise<number> {
  const { data: bal } = await supabase
    .from('virtual_balance')
    .select('balance_ils')
    .eq('user_id', userId)
    .single();

  if (bal) return Number(bal.balance_ils);

  // Initialise from investment_amount minus existing allocations
  let initBalance = 100_000;
  const { data: profile } = await supabase
    .from('profiles')
    .select('investment_amount')
    .eq('id', userId)
    .single();

  if (profile?.investment_amount) {
    const { data: positions } = await supabase
      .from('virtual_portfolio')
      .select('quantity')
      .eq('user_id', userId);

    const allocated = (positions ?? []).reduce(
      (sum, p) => sum + Number(p.quantity), 0,
    );
    initBalance = Math.max(0, Number(profile.investment_amount) - allocated);
  }

  await supabase
    .from('virtual_balance')
    .insert({ user_id: userId, balance_ils: initBalance });

  return initBalance;
}

export async function executeMarketOrder(
  userId:        string,
  symbol:        string,
  action:        'buy' | 'sell',
  units:         number,
  priceIls:      number,
  orderType:     string,
  triggerPrice?: number,
): Promise<{ success: boolean; newBalance: number; error?: string }> {
  const totalIls = units * priceIls;

  // Current holding
  const { data: holding } = await supabase
    .from('virtual_portfolio')
    .select('quantity, avg_buy_price')
    .eq('user_id', userId)
    .eq('symbol', symbol)
    .single();

  const heldUnits = holding && Number(holding.avg_buy_price) > 0
    ? Number(holding.quantity) / Number(holding.avg_buy_price)
    : 0;

  const balance = await getOrInitBalance(userId);

  // ── BUY ───────────────────────────────────────────────────────────────────
  if (action === 'buy') {
    if (balance < totalIls) {
      return { success: false, newBalance: balance, error: 'Insufficient virtual balance' };
    }

    const newBalance = balance - totalIls;

    await supabase
      .from('virtual_balance')
      .update({ balance_ils: newBalance, updated_at: new Date().toISOString() })
      .eq('user_id', userId);

    if (holding) {
      const newQuantity  = Number(holding.quantity) + totalIls;
      const newHeldUnits = heldUnits + units;
      const newAvgPrice  = newHeldUnits > 0 ? newQuantity / newHeldUnits : priceIls;
      await supabase
        .from('virtual_portfolio')
        .update({ quantity: newQuantity, avg_buy_price: newAvgPrice })
        .eq('user_id', userId)
        .eq('symbol', symbol);
    } else {
      await supabase
        .from('virtual_portfolio')
        .insert({ user_id: userId, symbol, quantity: totalIls, avg_buy_price: priceIls, currency: 'ILS' });
    }

    await supabase.from('paper_trades').insert({
      user_id: userId, symbol, action: 'buy', units, price_ils: priceIls,
      total_ils: totalIls, order_type: orderType, trigger_price: triggerPrice ?? null,
    });

    return { success: true, newBalance };

  // ── SELL ──────────────────────────────────────────────────────────────────
  } else {
    if (!holding || heldUnits < units - 0.001) {
      return { success: false, newBalance: balance, error: 'Insufficient holdings' };
    }

    const proceeds    = totalIls;
    const newBalance  = balance + proceeds;
    const costBasis   = units * Number(holding.avg_buy_price);
    const newQuantity = Number(holding.quantity) - costBasis;

    await supabase
      .from('virtual_balance')
      .update({ balance_ils: newBalance, updated_at: new Date().toISOString() })
      .eq('user_id', userId);

    if (newQuantity <= 0.01) {
      await supabase
        .from('virtual_portfolio')
        .delete()
        .eq('user_id', userId)
        .eq('symbol', symbol);
    } else {
      await supabase
        .from('virtual_portfolio')
        .update({ quantity: newQuantity })
        .eq('user_id', userId)
        .eq('symbol', symbol);
    }

    await supabase.from('paper_trades').insert({
      user_id: userId, symbol, action: 'sell', units, price_ils: priceIls,
      total_ils: proceeds, order_type: orderType, trigger_price: triggerPrice ?? null,
    });

    return { success: true, newBalance };
  }
}

// ── Main monitor function ─────────────────────────────────────────────────────

export async function checkPendingOrders(): Promise<void> {
  const { data: orders } = await supabase
    .from('pending_orders')
    .select('*')
    .eq('status', 'pending');

  if (!orders || orders.length === 0) return;

  // Fetch live prices for unique symbols
  const symbols = [...new Set(orders.map(o => o.symbol as string))];
  const priceMap = new Map<string, number>();

  await Promise.allSettled(
    symbols.map(async sym => {
      try {
        const q = await getQuote(sym);
        if (q.price > 0) priceMap.set(sym, q.price);
      } catch { /* skip */ }
    }),
  );

  for (const order of orders) {
    const livePrice = priceMap.get(order.symbol as string);
    if (!livePrice) continue;

    let shouldExecute = false;

    if (order.order_type === 'limit') {
      shouldExecute = order.action === 'buy'
        ? livePrice <= Number(order.trigger_price)   // buy cheap
        : livePrice >= Number(order.trigger_price);  // sell high
    } else if (order.order_type === 'stop') {
      // Becomes a market order when stop price is reached
      shouldExecute = order.action === 'buy'
        ? livePrice >= Number(order.trigger_price)   // breakout buy
        : livePrice <= Number(order.trigger_price);  // stop-loss sell
    } else if (order.order_type === 'stop_limit') {
      // Triggered at stop price, fills only if limit price is also satisfied
      const stopPrice  = Number(order.trigger_price);
      const limitPrice = Number(order.limit_price);
      const triggered  = order.action === 'buy'
        ? livePrice >= stopPrice
        : livePrice <= stopPrice;
      if (triggered) {
        shouldExecute = order.action === 'buy'
          ? livePrice <= limitPrice   // don't pay above limit
          : livePrice >= limitPrice;  // don't sell below limit
      }
    } else if (order.order_type === 'stop_loss') {
      shouldExecute = livePrice <= Number(order.trigger_price); // legacy: sell before further loss
    } else if (order.order_type === 'take_profit') {
      shouldExecute = livePrice >= Number(order.trigger_price); // legacy: sell at profit target
    }

    if (!shouldExecute) continue;

    const result = await executeMarketOrder(
      order.user_id as string,
      order.symbol  as string,
      order.action  as 'buy' | 'sell',
      Number(order.units),
      livePrice,
      order.order_type as string,
      Number(order.trigger_price),
    );

    if (result.success) {
      await supabase
        .from('pending_orders')
        .update({ status: 'executed', executed_at: new Date().toISOString() })
        .eq('id', order.id);

      logger.info(`Pending order ${order.id} executed: ${order.action} ${order.units} ${order.symbol} @ ${livePrice}`);
    } else {
      logger.warn(`Pending order ${order.id} could not execute: ${result.error}`);
    }
  }
}
