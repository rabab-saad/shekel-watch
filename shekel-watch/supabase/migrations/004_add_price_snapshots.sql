CREATE TABLE IF NOT EXISTS public.price_snapshots (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol          TEXT NOT NULL,
  tase_price_ils  NUMERIC,
  ny_price_usd    NUMERIC,
  exchange_rate   NUMERIC,
  gap_percent     NUMERIC GENERATED ALWAYS AS (
    CASE
      WHEN tase_price_ils IS NOT NULL
        AND ny_price_usd   IS NOT NULL
        AND exchange_rate   > 0
      THEN ROUND(
        ((tase_price_ils - (ny_price_usd * exchange_rate))
          / (ny_price_usd * exchange_rate)) * 100,
        4
      )
      ELSE NULL
    END
  ) STORED,
  captured_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_snapshots_symbol_time
  ON public.price_snapshots(symbol, captured_at DESC);
