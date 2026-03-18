/**
 * Trade simulation routes — Trade tab in Paper Trading.
 *
 * GET  /api/trade/balance        — virtual cash balance (initialised lazily)
 * GET  /api/trade/history        — completed trade log
 * GET  /api/trade/pending        — open pending orders
 * POST /api/trade/execute        — execute a market order immediately
 * POST /api/trade/order          — place a limit / stop-loss / take-profit order
 * DELETE /api/trade/order/:id    — cancel a pending order
 */

import { Router, Request, Response } from 'express';
import { requireAuth }               from '../middleware/auth';
import { supabase }                  from '../config/supabase';
import { logger }                    from '../utils/logger';
import { getOrInitBalance, executeMarketOrder } from '../jobs/pendingOrderMonitor';

const router = Router();
type AuthedReq = Request & { user: { id: string } };

// ── GET /api/trade/balance ────────────────────────────────────────────────────
router.get('/balance', requireAuth, async (req: Request, res: Response) => {
  const { user } = req as AuthedReq;
  try {
    const balance = await getOrInitBalance(user.id);
    res.json({ balance_ils: balance });
  } catch (err) {
    logger.error('Failed to get trade balance', err);
    res.status(500).json({ error: 'Failed to get balance' });
  }
});

// ── GET /api/trade/history?limit=50 ──────────────────────────────────────────
router.get('/history', requireAuth, async (req: Request, res: Response) => {
  const { user } = req as AuthedReq;
  const limit = Math.min(parseInt(req.query.limit as string) || 50, 200);
  try {
    const { data, error } = await supabase
      .from('paper_trades')
      .select('*')
      .eq('user_id', user.id)
      .order('executed_at', { ascending: false })
      .limit(limit);
    if (error) throw error;
    res.json(data ?? []);
  } catch (err) {
    logger.error('Failed to get trade history', err);
    res.status(500).json({ error: 'Failed to get history' });
  }
});

// ── GET /api/trade/pending ────────────────────────────────────────────────────
router.get('/pending', requireAuth, async (req: Request, res: Response) => {
  const { user } = req as AuthedReq;
  try {
    const { data, error } = await supabase
      .from('pending_orders')
      .select('*')
      .eq('user_id', user.id)
      .eq('status', 'pending')
      .order('created_at', { ascending: false });
    if (error) throw error;
    res.json(data ?? []);
  } catch (err) {
    logger.error('Failed to get pending orders', err);
    res.status(500).json({ error: 'Failed to get pending orders' });
  }
});

// ── POST /api/trade/execute ───────────────────────────────────────────────────
router.post('/execute', requireAuth, async (req: Request, res: Response) => {
  const { user } = req as AuthedReq;
  const { symbol, action, units, priceIls } = req.body as {
    symbol:   string;
    action:   'buy' | 'sell';
    units:    number;
    priceIls: number;
  };

  if (!symbol || !action || !units || !priceIls) {
    res.status(400).json({ error: 'Missing required fields: symbol, action, units, priceIls' });
    return;
  }
  if (!['buy', 'sell'].includes(action)) {
    res.status(400).json({ error: 'action must be buy or sell' });
    return;
  }

  try {
    const result = await executeMarketOrder(user.id, symbol.toUpperCase(), action, Number(units), Number(priceIls), 'market');
    if (!result.success) {
      res.status(400).json({ error: result.error });
      return;
    }
    res.json(result);
  } catch (err) {
    logger.error('Trade execution failed', err);
    res.status(500).json({ error: 'Trade execution failed' });
  }
});

// ── POST /api/trade/order ─────────────────────────────────────────────────────
router.post('/order', requireAuth, async (req: Request, res: Response) => {
  const { user } = req as AuthedReq;
  const { symbol, action, units, orderType, triggerPrice } = req.body as {
    symbol:       string;
    action:       'buy' | 'sell';
    units:        number;
    orderType:    'limit' | 'stop_loss' | 'take_profit';
    triggerPrice: number;
  };

  if (!symbol || !action || !units || !orderType || !triggerPrice) {
    res.status(400).json({ error: 'Missing required fields' });
    return;
  }

  try {
    // Pre-validate balance (for buy) or holdings (for sell)
    if (action === 'buy') {
      const balance     = await getOrInitBalance(user.id);
      const estimatedCost = Number(units) * Number(triggerPrice);
      if (balance < estimatedCost) {
        res.status(400).json({ error: 'Insufficient balance for this order at trigger price' });
        return;
      }
    } else {
      const { data: holding } = await supabase
        .from('virtual_portfolio')
        .select('quantity, avg_buy_price')
        .eq('user_id', user.id)
        .eq('symbol', symbol.toUpperCase())
        .single();

      const heldUnits = holding && Number(holding.avg_buy_price) > 0
        ? Number(holding.quantity) / Number(holding.avg_buy_price)
        : 0;
      if (heldUnits < Number(units) - 0.001) {
        res.status(400).json({ error: 'Insufficient holdings for this sell order' });
        return;
      }
    }

    const { data, error } = await supabase
      .from('pending_orders')
      .insert({
        user_id:       user.id,
        symbol:        symbol.toUpperCase(),
        action,
        units:         Number(units),
        order_type:    orderType,
        trigger_price: Number(triggerPrice),
      })
      .select()
      .single();

    if (error) throw error;
    res.json({ success: true, order: data });
  } catch (err) {
    logger.error('Failed to place pending order', err);
    res.status(500).json({ error: 'Failed to place order' });
  }
});

// ── DELETE /api/trade/order/:id ───────────────────────────────────────────────
router.delete('/order/:id', requireAuth, async (req: Request, res: Response) => {
  const { user } = req as AuthedReq;
  const { id }   = req.params;

  try {
    const { error } = await supabase
      .from('pending_orders')
      .update({ status: 'cancelled' })
      .eq('id', id)
      .eq('user_id', user.id)
      .eq('status', 'pending');

    if (error) throw error;
    res.json({ success: true });
  } catch (err) {
    logger.error('Failed to cancel order', err);
    res.status(500).json({ error: 'Failed to cancel order' });
  }
});

export default router;
