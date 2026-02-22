-- ─── Extensions ──────────────────────────────────────────────────────────────
create extension if not exists "uuid-ossp";

-- ─── User Profiles ────────────────────────────────────────────────────────────
-- Auto-created via trigger when a user signs up
create table public.profiles (
  id               uuid primary key references auth.users(id) on delete cascade,
  display_name     text,
  language         text not null default 'en' check (language in ('en', 'he')),
  phone_number     text unique,        -- WhatsApp number e.g. +972501234567
  whatsapp_enabled boolean default false,
  created_at       timestamptz default now(),
  updated_at       timestamptz default now()
);

-- ─── Watchlist ────────────────────────────────────────────────────────────────
create table public.watchlist (
  id         uuid primary key default uuid_generate_v4(),
  user_id    uuid not null references public.profiles(id) on delete cascade,
  ticker     text not null,            -- e.g. "LUMI.TA", "TEVA", "ESLT.TA"
  market     text not null check (market in ('TASE', 'NYSE', 'NASDAQ')),
  added_at   timestamptz default now(),
  unique(user_id, ticker)
);
create index idx_watchlist_user on public.watchlist(user_id);

-- ─── Rate Snapshots ──────────────────────────────────────────────────────────
-- Written hourly by cron job for chart history
create table public.rate_snapshots (
  id         bigint generated always as identity primary key,
  pair       text not null default 'USD_ILS',
  rate       numeric(10,4) not null,
  source     text not null,
  snapped_at timestamptz default now()
);
create index idx_rate_snapshots_time on public.rate_snapshots(snapped_at desc);

-- ─── Dual-Listed Company Pairs ───────────────────────────────────────────────
-- Seed data for arbitrage gap analysis
create table public.dual_listed (
  id            serial primary key,
  name          text not null,
  ticker_tase   text not null unique,
  ticker_nyse   text not null unique,
  sector        text
);

-- ─── Arbitrage Log ───────────────────────────────────────────────────────────
create table public.arbitrage_log (
  id                bigint generated always as identity primary key,
  ticker_tase       text not null,
  ticker_foreign    text not null,
  tase_price_ils    numeric(12,4),
  foreign_price_usd numeric(12,4),
  usd_ils_rate      numeric(10,4),
  gap_percent       numeric(6,3),
  logged_at         timestamptz default now()
);
create index idx_arb_log_ticker on public.arbitrage_log(ticker_tase, logged_at desc);

-- ─── Row Level Security ───────────────────────────────────────────────────────
alter table public.profiles  enable row level security;
alter table public.watchlist enable row level security;

create policy "Users read own profile"
  on public.profiles for select using (auth.uid() = id);

create policy "Users update own profile"
  on public.profiles for update using (auth.uid() = id);

create policy "Users manage own watchlist"
  on public.watchlist for all using (auth.uid() = user_id);

-- ─── Auto-create profile on signup ───────────────────────────────────────────
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles(id)
  values (new.id)
  on conflict do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
