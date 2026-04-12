-- Minimal idempotent patch for WALLETGO transaction persistence
-- Run this in Supabase SQL Editor if data-service fails with PGRST205 for public.transactions

create extension if not exists pgcrypto;

create table if not exists public.transactions (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  date date not null,
  amount numeric(12,2) not null,
  category text not null,
  description text not null,
  fingerprint text not null,
  created_at timestamptz not null default now(),
  unique (user_id, fingerprint)
);

create index if not exists idx_transactions_user_id_date
  on public.transactions (user_id, date desc);

alter table public.transactions enable row level security;

drop policy if exists "Transactions are readable by owner" on public.transactions;
create policy "Transactions are readable by owner"
  on public.transactions for select
  using (auth.uid()::text = user_id);

drop policy if exists "Transactions are writable by owner" on public.transactions;
create policy "Transactions are writable by owner"
  on public.transactions for all
  using (auth.uid()::text = user_id)
  with check (auth.uid()::text = user_id);
