ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS trading_mode TEXT DEFAULT NULL
    CHECK (trading_mode IN ('beginner', 'pro'));

ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS morning_summary_enabled BOOLEAN DEFAULT false;

-- phone_number already exists — skipped
