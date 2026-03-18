-- 010_watchlist_enrich: store display name and asset type alongside ticker

ALTER TABLE public.watchlist
  ADD COLUMN IF NOT EXISTS name       TEXT,
  ADD COLUMN IF NOT EXISTS asset_type TEXT;
