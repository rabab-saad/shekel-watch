CREATE TABLE IF NOT EXISTS public.virtual_balance (
  user_id    UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
  balance_ils NUMERIC DEFAULT 100000,
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.virtual_portfolio (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  symbol         TEXT NOT NULL,
  quantity       NUMERIC NOT NULL DEFAULT 0,
  avg_buy_price  NUMERIC NOT NULL,
  currency       TEXT DEFAULT 'ILS',
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, symbol)
);

-- RLS
ALTER TABLE public.virtual_balance    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.virtual_portfolio  ENABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.virtual_balance   TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.virtual_portfolio TO authenticated;

DROP POLICY IF EXISTS "Users manage own balance"    ON public.virtual_balance;
DROP POLICY IF EXISTS "Users manage own portfolio"  ON public.virtual_portfolio;

CREATE POLICY "Users manage own balance"
  ON public.virtual_balance FOR ALL
  USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users manage own portfolio"
  ON public.virtual_portfolio FOR ALL
  USING ((SELECT auth.uid()) = user_id);
