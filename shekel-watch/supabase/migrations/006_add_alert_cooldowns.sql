CREATE TABLE IF NOT EXISTS public.alert_cooldowns (
  user_id        UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  symbol         TEXT NOT NULL,
  last_alerted_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, symbol)
);

ALTER TABLE public.alert_cooldowns ENABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.alert_cooldowns TO authenticated;

DROP POLICY IF EXISTS "Users manage own cooldowns" ON public.alert_cooldowns;

CREATE POLICY "Users manage own cooldowns"
  ON public.alert_cooldowns FOR ALL
  USING ((SELECT auth.uid()) = user_id);
