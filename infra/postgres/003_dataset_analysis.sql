create extension if not exists pgcrypto;

create table if not exists dataset_columns (
  id uuid primary key,
  dataset_id uuid not null references datasets(id) on delete cascade,
  name text not null,
  original_name text not null,
  data_type text not null check (
    data_type in ('string', 'number', 'integer', 'boolean', 'datetime', 'category', 'unknown')
  ),
  semantic_type text,
  nullable boolean not null default false,
  missing_count integer not null default 0,
  unique_count integer,
  min_value text,
  max_value text,
  mean_value double precision,
  median_value double precision,
  stddev_value double precision,
  profile jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists dataset_profiles (
  dataset_id uuid primary key references datasets(id) on delete cascade,
  summary jsonb not null,
  missing_values jsonb not null default '{}'::jsonb,
  outliers jsonb not null default '{}'::jsonb,
  correlations jsonb not null default '{}'::jsonb,
  time_series jsonb not null default '{}'::jsonb,
  categorical_aggregates jsonb not null default '{}'::jsonb,
  generated_at timestamptz not null default now()
);

create table if not exists dataset_previews (
  dataset_id uuid primary key references datasets(id) on delete cascade,
  columns jsonb not null default '[]'::jsonb,
  rows jsonb not null default '[]'::jsonb,
  generated_at timestamptz not null default now()
);

create index if not exists idx_dataset_columns_dataset_id on dataset_columns(dataset_id);
