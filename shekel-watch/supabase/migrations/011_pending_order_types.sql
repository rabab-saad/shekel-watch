-- 011_pending_order_types.sql
-- Extend pending_orders to support stop and stop-limit order types.

-- 1. Add limit_price column (used by stop_limit orders only, NULL for others)
ALTER TABLE public.pending_orders
  ADD COLUMN IF NOT EXISTS limit_price NUMERIC(18,4);

-- 2. Widen order_type CHECK to include the two new types
ALTER TABLE public.pending_orders
  DROP CONSTRAINT IF EXISTS pending_orders_order_type_check;

ALTER TABLE public.pending_orders
  ADD CONSTRAINT pending_orders_order_type_check
    CHECK (order_type IN ('limit','stop_loss','take_profit','stop','stop_limit'));
