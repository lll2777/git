create extension if not exists pgcrypto;

create table if not exists insights (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  dataset_id uuid not null references datasets(id) on delete cascade,
  title text not null,
  summary text not null,
  insight_type text not null check (insight_type in ('summary', 'trend', 'anomaly', 'correlation', 'business', 'warning')),
  severity text not null default 'info' check (severity in ('info', 'low', 'medium', 'high')),
  evidence jsonb not null default '{}'::jsonb,
  provider text,
  model text,
  source text not null check (source in ('deterministic', 'ai', 'user')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_insights_workspace_id on insights(workspace_id);
create index if not exists idx_insights_dataset_id on insights(dataset_id);
create index if not exists idx_insights_dataset_created_at on insights(dataset_id, created_at desc);
