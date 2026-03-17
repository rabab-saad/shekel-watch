-- 007_add_paper_config.sql
-- Adds investment_amount and risk_level to profiles for the portfolio builder.

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS investment_amount NUMERIC DEFAULT 100000,
  ADD COLUMN IF NOT EXISTS risk_level        TEXT    DEFAULT 'medium';
