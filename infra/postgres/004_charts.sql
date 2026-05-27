create extension if not exists pgcrypto;

create table if not exists charts (
  id uuid primary key,
  dashboard_id uuid,
  dataset_id uuid not null references datasets(id) on delete cascade,
  title text not null,
  chart_type text not null,
  config jsonb not null,
  query_spec jsonb not null default '{}'::jsonb,
  position jsonb not null default '{}'::jsonb,
  created_by text not null check (created_by in ('system', 'ai', 'user')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_charts_dataset_id on charts(dataset_id);
create index if not exists idx_charts_dashboard_id on charts(dashboard_id);
