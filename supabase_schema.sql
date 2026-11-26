create extension if not exists pgcrypto;

create table if not exists public.news_events (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  summary text,
  article_url text not null unique,
  source_name text,
  published_at timestamptz,
  company text not null default 'Ryanair',
  threat_level text not null check (threat_level in ('low', 'medium', 'high', 'critical')),
  threat_reason text,
  pr_draft text,
  pr_citation text,
  pr_draft_generated_at timestamptz,
  slack_channel_id text,
  slack_message_ts text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.news_events enable row level security;

create or replace function public.set_news_events_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_news_events_updated_at on public.news_events;
create trigger set_news_events_updated_at
before update on public.news_events
for each row execute function public.set_news_events_updated_at();
