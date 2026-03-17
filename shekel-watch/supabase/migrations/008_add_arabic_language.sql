-- Allow Arabic ('ar') as a valid language option in profiles.
-- The original constraint only permitted 'en' and 'he'.

ALTER TABLE profiles
  DROP CONSTRAINT IF EXISTS profiles_language_check;

ALTER TABLE profiles
  ADD CONSTRAINT profiles_language_check
  CHECK (language IN ('en', 'he', 'ar'));
