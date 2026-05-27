create extension if not exists pgcrypto;

create table if not exists dashboards (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  dataset_id uuid not null references datasets(id) on delete cascade,
  owner_id uuid not null,
  title text not null,
  description text,
  layout jsonb not null default '{"version": 1, "columns": 12, "items": []}'::jsonb,
  status text not null default 'active' check (status in ('active', 'archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists dashboard_items (
  id uuid primary key,
  dashboard_id uuid not null references dashboards(id) on delete cascade,
  item_type text not null check (item_type in ('chart', 'insight')),
  item_id uuid not null,
  position integer not null default 0,
  created_at timestamptz not null default now()
);

create index if not exists idx_dashboards_workspace_id on dashboards(workspace_id);
create index if not exists idx_dashboards_dataset_id on dashboards(dataset_id);
create index if not exists idx_dashboard_items_dashboard_id on dashboard_items(dashboard_id);
create index if not exists idx_dashboard_items_item on dashboard_items(item_type, item_id);
