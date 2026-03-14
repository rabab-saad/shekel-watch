import { Router, Request, Response } from 'express';
import { requireAuth } from '../middleware/auth';
import { supabase } from '../config/supabase';
import { logger } from '../utils/logger';

const router = Router();

type AuthedReq = Request & { user: { id: string } };

// POST /api/paper-trade
router.post('/', requireAuth, async (req: Request, res: Response) => {
  const { user } = req as AuthedReq;
  const { symbol, action, quantity, currentPrice } = req.body as {
    symbol:       string;
    action:       'buy' | 'sell';
    quantity:     number;
    currentPrice: number;
  };

  if (!symbol || !action || !quantity || !currentPrice) {
    res.status(400).json({ error: 'Missing required fields' });
    return;
  }

  try {
    if (action === 'buy') {
      // 1. Fetch or create virtual_balance
      let { data: bal } = await supabase
        .from('virtual_balance')
        .select('balance_ils')
        .eq('user_id', user.id)
        .single();

      if (!bal) {
        await supabase
          .from('virtual_balance')
          .insert({ user_id: user.id, balance_ils: 100000 });
        bal = { balance_ils: 100000 };
      }

      // 2. Check funds
      const cost = quantity * currentPrice;
      if (bal.balance_ils < cost) {
        res.status(400).json({ error: 'Insufficient virtual balance' });
        return;
      }

      // 3. Deduct balance
      const newBalance = bal.balance_ils - cost;
      await supabase
        .from('virtual_balance')
        .update({ balance_ils: newBalance, updated_at: new Date().toISOString() })
        .eq('user_id', user.id);

      // 4. Upsert portfolio row
      const { data: existing } = await supabase
        .from('virtual_portfolio')
        .select('quantity, avg_buy_price')
        .eq('user_id', user.id)
        .eq('symbol', symbol)
        .single();

      if (existing) {
        const newQty = existing.quantity + quantity;
        const newAvg = (existing.quantity * existing.avg_buy_price + quantity * currentPrice) / newQty;
        await supabase
          .from('virtual_portfolio')
          .update({ quantity: newQty, avg_buy_price: newAvg })
          .eq('user_id', user.id)
          .eq('symbol', symbol);
      } else {
        await supabase
          .from('virtual_portfolio')
          .insert({ user_id: user.id, symbol, quantity, avg_buy_price: currentPrice, currency: 'ILS' });
      }

      res.json({ success: true, newBalance, action: 'buy', symbol, quantity });

    } else if (action === 'sell') {
      // 1. Check holdings
      const { data: holding } = await supabase
        .from('virtual_portfolio')
        .select('quantity, avg_buy_price')
        .eq('user_id', user.id)
        .eq('symbol', symbol)
        .single();

      if (!holding || holding.quantity < quantity) {
        res.status(400).json({ error: 'Insufficient holdings' });
        return;
      }

      // 2. Fetch balance (create if missing)
      let { data: bal } = await supabase
        .from('virtual_balance')
        .select('balance_ils')
        .eq('user_id', user.id)
        .single();

      if (!bal) {
        await supabase
          .from('virtual_balance')
          .insert({ user_id: user.id, balance_ils: 100000 });
        bal = { balance_ils: 100000 };
      }

      // 3. Credit proceeds
      const proceeds  = quantity * currentPrice;
      const newBalance = bal.balance_ils + proceeds;

      await supabase
        .from('virtual_balance')
        .update({ balance_ils: newBalance, updated_at: new Date().toISOString() })
        .eq('user_id', user.id);

      // 4. Reduce or delete portfolio row
      const newQty = holding.quantity - quantity;
      if (newQty === 0) {
        await supabase
          .from('virtual_portfolio')
          .delete()
          .eq('user_id', user.id)
          .eq('symbol', symbol);
      } else {
        await supabase
          .from('virtual_portfolio')
          .update({ quantity: newQty })
          .eq('user_id', user.id)
          .eq('symbol', symbol);
      }

      res.json({ success: true, newBalance, action: 'sell', symbol, quantity });

    } else {
      res.status(400).json({ error: 'action must be buy or sell' });
    }

  } catch (err) {
    logger.error('paper-trade error', err);
    res.status(500).json({ error: 'Trade failed' });
  }
});

export default router;
