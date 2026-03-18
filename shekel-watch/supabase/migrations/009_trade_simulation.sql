-- 009_trade_simulation: Transaction history + pending orders for Trade tab

-- ── Completed trade log ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS paper_trades (
  id            UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       UUID        NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  symbol        TEXT        NOT NULL,
  action        TEXT        NOT NULL CHECK (action IN ('buy','sell')),
  units         NUMERIC(18,6) NOT NULL CHECK (units > 0),
  price_ils     NUMERIC(18,4) NOT NULL CHECK (price_ils > 0),
  total_ils     NUMERIC(18,4) NOT NULL,
  order_type    TEXT        NOT NULL DEFAULT 'market'
                  CHECK (order_type IN ('market','limit','stop_loss','take_profit')),
  trigger_price NUMERIC(18,4),
  executed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE paper_trades ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own trades"
  ON paper_trades FOR ALL USING (auth.uid() = user_id);

-- ── Unexecuted conditional orders ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pending_orders (
  id            UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       UUID        NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  symbol        TEXT        NOT NULL,
  action        TEXT        NOT NULL CHECK (action IN ('buy','sell')),
  units         NUMERIC(18,6) NOT NULL CHECK (units > 0),
  order_type    TEXT        NOT NULL
                  CHECK (order_type IN ('limit','stop_loss','take_profit')),
  trigger_price NUMERIC(18,4) NOT NULL CHECK (trigger_price > 0),
  status        TEXT        NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','executed','cancelled')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  executed_at   TIMESTAMPTZ
);

ALTER TABLE pending_orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own orders"
  ON pending_orders FOR ALL USING (auth.uid() = user_id);
