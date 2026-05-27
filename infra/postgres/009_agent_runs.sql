create extension if not exists pgcrypto;

create table if not exists agent_runs (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  dataset_id uuid not null references datasets(id) on delete cascade,
  owner_id uuid not null,
  objective text not null,
  status text not null default 'running' check (status in ('running', 'succeeded', 'failed', 'cancelled')),
  result jsonb not null default '{}'::jsonb,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists agent_steps (
  id uuid primary key,
  run_id uuid not null references agent_runs(id) on delete cascade,
  step_name text not null,
  status text not null default 'running' check (status in ('running', 'succeeded', 'failed', 'skipped')),
  input jsonb not null default '{}'::jsonb,
  output jsonb not null default '{}'::jsonb,
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_agent_runs_workspace_id on agent_runs(workspace_id);
create index if not exists idx_agent_runs_dataset_id on agent_runs(dataset_id);
create index if not exists idx_agent_steps_run_id on agent_steps(run_id);
