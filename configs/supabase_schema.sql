-- Supabase / PostgreSQL schema for Radar user preferences and forecasts

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique,
  display_name text,
  language_preference text not null default 'en',
  persona text not null default 'professional',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.user_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  key text not null,
  value jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, key)
);

create table if not exists public.forecasts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  forecast_data jsonb not null,
  confidence numeric(5,2) not null default 0,
  starting_balance numeric(12,2) not null default 0,
  model text not null default 'prophet',
  min_balance numeric(12,2),
  min_balance_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.scenario_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  description text not null,
  language text not null default 'en',
  low_result jsonb,
  likely_result jsonb,
  high_result jsonb,
  explanation text,
  created_at timestamptz not null default now()
);

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

create index if not exists idx_forecasts_user_id_created_at on public.forecasts (user_id, created_at desc);
create index if not exists idx_scenario_runs_user_id_created_at on public.scenario_runs (user_id, created_at desc);
create index if not exists idx_transactions_user_id_date on public.transactions (user_id, date desc);

alter table public.profiles enable row level security;
alter table public.user_preferences enable row level security;
alter table public.forecasts enable row level security;
alter table public.scenario_runs enable row level security;
alter table public.transactions enable row level security;

create policy "Profiles are readable by owner"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Profiles are updatable by owner"
  on public.profiles for update
  using (auth.uid() = id);

create policy "Preferences are readable by owner"
  on public.user_preferences for select
  using (auth.uid() = user_id);

create policy "Preferences are writable by owner"
  on public.user_preferences for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Forecasts are readable by owner"
  on public.forecasts for select
  using (auth.uid() = user_id);

create policy "Forecasts are writable by owner"
  on public.forecasts for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Scenarios are readable by owner"
  on public.scenario_runs for select
  using (auth.uid() = user_id);

create policy "Scenarios are writable by owner"
  on public.scenario_runs for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "Transactions are readable by owner"
  on public.transactions for select
  using (auth.uid()::text = user_id);

create policy "Transactions are writable by owner"
  on public.transactions for all
  using (auth.uid()::text = user_id)
  with check (auth.uid()::text = user_id);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do update set email = excluded.email, updated_at = now();
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();