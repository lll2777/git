# STEP 1 Architecture

## 1. Design Intent

This project is designed as a real SaaS system, not a demo. The architecture
separates product workflows, data processing, AI orchestration, persistence, and
deployment boundaries so each layer can evolve without rewriting the platform.

Core principles:

- Frontend and backend are separated in a monorepo.
- Business logic goes through service layers.
- Database access goes through repository layers.
- AI calls go through `aiService` only.
- Model vendors are hidden behind provider adapters.
- Long-running data work runs through Redis and Celery.
- Supabase handles user identity and object storage.
- PostgreSQL remains the source of truth for metadata, dashboards, jobs, and sharing.

## 2. System Architecture

```mermaid
flowchart LR
  User["User"] --> Web["Next.js App Router Frontend"]
  Web --> SupabaseAuth["Supabase Auth"]
  Web --> SupabaseStorage["Supabase Storage"]
  Web --> API["FastAPI Backend"]

  API --> AuthGuard["JWT Auth Guard"]
  AuthGuard --> Services["Service Layer"]

  Services --> DatasetService["Dataset Service"]
  Services --> ChartService["Chart Service"]
  Services --> DashboardService["Dashboard Service"]
  Services --> AIService["AI Service"]
  Services --> JobService["Job Service"]

  DatasetService --> Pandas["pandas/numpy Analysis Engine"]
  AIService --> ProviderFactory["AI Provider Factory"]
  ProviderFactory --> Mimo["MimoProvider"]
  ProviderFactory -. later .-> OpenAI["OpenAIProvider"]
  ProviderFactory -. later .-> DeepSeek["DeepSeekProvider"]
  ProviderFactory -. later .-> Qwen["QwenProvider"]
  ProviderFactory -. later .-> Claude["ClaudeProvider"]

  Services --> Repositories["Repository Layer"]
  Repositories --> Postgres["PostgreSQL"]

  JobService --> Redis["Redis Broker"]
  Redis --> Celery["Celery Workers"]
  Celery --> DatasetService
  Celery --> AIService

  SupabaseStorage --> FileObjects["CSV/Excel Objects"]
```

## 3. Technical Architecture

### Frontend

- Next.js App Router with TypeScript.
- TailwindCSS for styling.
- shadcn/ui for accessible primitives and a consistent design system.
- React Query for server state, caching, retries, and optimistic dashboard updates.
- Zustand for local UI state such as editor panels, selected chart, filters, and layout.
- Recharts for MVP chart rendering.
- ECharts is reserved for advanced chart types and large interactive dashboards.

Frontend module boundaries:

- `app`: route shells, layouts, server components where useful.
- `features`: domain modules such as auth, datasets, dashboards, charts, AI chat.
- `components`: reusable UI components and app shell.
- `lib/api`: typed API clients.
- `stores`: Zustand stores.
- `hooks`: reusable UI and data hooks.

### Backend

- FastAPI running inside the local conda `pytorch` environment.
- Python version follows the current `pytorch` environment. Current detected version:
  `Python 3.10.20`.
- No project venv is created.
- pandas and numpy handle local data profiling, cleaning, summaries, correlation,
  outlier detection, and chart candidate generation.
- Pydantic schemas define API input and output contracts.
- Repositories own PostgreSQL reads and writes.
- Services own business workflows.
- Celery workers own slow or retryable tasks.
- Structured logs are emitted from API and worker processes.

### Auth And Storage

- Supabase Auth is the identity provider.
- Frontend receives Supabase session tokens.
- Backend verifies Supabase JWTs before accessing protected resources.
- Supabase Storage stores uploaded files.
- PostgreSQL stores file metadata, inferred schema, dashboard state, AI outputs, and
  share configuration.

### AI Provider Boundary

Every AI capability must pass through:

```text
API route -> service -> aiService -> provider factory -> selected AIProvider
```

Business code must not import or call Mimo, OpenAI, DeepSeek, Qwen, or Claude SDKs
directly.

Required interface:

```python
class AIProvider:
    async def chat(self, messages, tools=None, metadata=None): ...
    async def analyze_data(self, dataset_profile, question=None): ...
    async def generate_insight(self, dataset_profile, chart_context=None): ...
    async def generate_chart_config(self, dataset_profile, intent=None): ...
```

Initial implementation:

- `MimoProvider`
- Provider selected with `AI_PROVIDER=mimo`
- Default model selected with `MIMO_MODEL=mimo-v2-flash`

Reserved implementations:

- `OpenAIProvider`
- `DeepSeekProvider`
- `QwenProvider`
- `ClaudeProvider`

## 4. Data Flow

### Upload And Analysis Flow

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Next.js
  participant SB as Supabase Storage
  participant API as FastAPI
  participant PG as PostgreSQL
  participant R as Redis
  participant W as Celery Worker
  participant AI as aiService

  U->>FE: Select CSV/Excel
  FE->>API: Create upload session
  API->>PG: Create dataset record
  API-->>FE: Signed upload target and dataset id
  FE->>SB: Upload file
  FE->>API: Confirm upload
  API->>PG: Store file metadata
  API->>R: Enqueue profiling job
  W->>SB: Download file
  W->>W: Clean, infer schema, profile data
  W->>AI: Generate chart plan and insights
  AI-->>W: Charts and business insights
  W->>PG: Persist profile, charts, insights
  FE->>API: Poll or subscribe to job status
  API-->>FE: Analysis complete
  FE->>API: Load dashboard
```

### AI Question Flow

```mermaid
sequenceDiagram
  participant FE as Next.js Chat UI
  participant API as FastAPI
  participant PG as PostgreSQL
  participant AIS as aiService
  participant P as Selected Provider

  FE->>API: Ask question for dataset/dashboard
  API->>PG: Load dataset profile and allowed context
  API->>AIS: chat(messages, tools, metadata)
  AIS->>P: Provider-specific request
  P-->>AIS: Answer and tool calls
  AIS-->>API: Normalized AI response
  API->>PG: Save conversation and messages
  API-->>FE: Answer, citations, optional chart actions
```

## 5. Database Design

PostgreSQL is the metadata and product state database. Supabase Storage owns file
bytes; PostgreSQL stores references and analysis results.

### Core Tables

```sql
create table profiles (
  id uuid primary key,
  email text not null,
  display_name text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table workspaces (
  id uuid primary key,
  owner_id uuid not null references profiles(id),
  name text not null,
  slug text not null unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table workspace_members (
  workspace_id uuid not null references workspaces(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'member', 'viewer')),
  created_at timestamptz not null default now(),
  primary key (workspace_id, user_id)
);

create table datasets (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  owner_id uuid not null references profiles(id),
  name text not null,
  status text not null check (status in ('created', 'uploaded', 'processing', 'ready', 'failed')),
  row_count integer,
  column_count integer,
  storage_bucket text,
  storage_path text,
  original_filename text,
  content_type text,
  size_bytes bigint,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table dataset_columns (
  id uuid primary key,
  dataset_id uuid not null references datasets(id) on delete cascade,
  name text not null,
  original_name text not null,
  data_type text not null check (data_type in ('string', 'number', 'integer', 'boolean', 'datetime', 'category', 'unknown')),
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

create table dataset_profiles (
  dataset_id uuid primary key references datasets(id) on delete cascade,
  summary jsonb not null,
  missing_values jsonb not null default '{}'::jsonb,
  outliers jsonb not null default '{}'::jsonb,
  correlations jsonb not null default '{}'::jsonb,
  time_series jsonb not null default '{}'::jsonb,
  categorical_aggregates jsonb not null default '{}'::jsonb,
  generated_at timestamptz not null default now()
);

create table dashboards (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  dataset_id uuid references datasets(id) on delete set null,
  owner_id uuid not null references profiles(id),
  name text not null,
  description text,
  layout jsonb not null default '{}'::jsonb,
  filters jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table charts (
  id uuid primary key,
  dashboard_id uuid not null references dashboards(id) on delete cascade,
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

create table insights (
  id uuid primary key,
  dataset_id uuid not null references datasets(id) on delete cascade,
  dashboard_id uuid references dashboards(id) on delete cascade,
  title text not null,
  body text not null,
  insight_type text not null check (insight_type in ('summary', 'trend', 'anomaly', 'correlation', 'business', 'warning')),
  severity text not null check (severity in ('info', 'low', 'medium', 'high')),
  evidence jsonb not null default '{}'::jsonb,
  created_by text not null check (created_by in ('system', 'ai')),
  created_at timestamptz not null default now()
);

create table ai_conversations (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  dataset_id uuid references datasets(id) on delete cascade,
  dashboard_id uuid references dashboards(id) on delete cascade,
  user_id uuid not null references profiles(id),
  title text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table ai_messages (
  id uuid primary key,
  conversation_id uuid not null references ai_conversations(id) on delete cascade,
  role text not null check (role in ('system', 'user', 'assistant', 'tool')),
  content text not null,
  tool_calls jsonb not null default '[]'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table analysis_jobs (
  id uuid primary key,
  workspace_id uuid not null references workspaces(id) on delete cascade,
  dataset_id uuid references datasets(id) on delete cascade,
  job_type text not null,
  status text not null check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
  progress integer not null default 0,
  result jsonb not null default '{}'::jsonb,
  error_message text,
  celery_task_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz
);

create table share_links (
  id uuid primary key,
  dashboard_id uuid not null references dashboards(id) on delete cascade,
  token text not null unique,
  access_type text not null check (access_type in ('public', 'password', 'workspace')),
  password_hash text,
  expires_at timestamptz,
  created_by uuid not null references profiles(id),
  created_at timestamptz not null default now()
);

create table audit_logs (
  id uuid primary key,
  workspace_id uuid references workspaces(id) on delete cascade,
  actor_id uuid references profiles(id),
  action text not null,
  entity_type text not null,
  entity_id uuid,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
```

Indexes to add in implementation:

- `datasets(workspace_id, created_at desc)`
- `dashboards(workspace_id, updated_at desc)`
- `charts(dashboard_id)`
- `insights(dataset_id, created_at desc)`
- `analysis_jobs(dataset_id, status)`
- `ai_messages(conversation_id, created_at)`
- `share_links(token)`

## 6. API Design

All protected backend routes require a valid Supabase JWT.

### Auth And User

Supabase handles registration, login, password reset, and session refresh on the
frontend. Backend routes validate tokens and expose profile bootstrap APIs.

| Method | Path                   | Purpose                                                |
| ------ | ---------------------- | ------------------------------------------------------ |
| GET    | `/api/v1/me`           | Return current user profile and workspace memberships  |
| POST   | `/api/v1/me/bootstrap` | Create profile and default workspace after first login |

### Datasets

| Method | Path                                           | Purpose                                                |
| ------ | ---------------------------------------------- | ------------------------------------------------------ |
| POST   | `/api/v1/datasets/upload-session`              | Create dataset record and signed storage upload target |
| POST   | `/api/v1/datasets/{dataset_id}/confirm-upload` | Confirm storage upload and enqueue profiling           |
| GET    | `/api/v1/datasets`                             | List datasets in workspace                             |
| GET    | `/api/v1/datasets/{dataset_id}`                | Get dataset metadata                                   |
| GET    | `/api/v1/datasets/{dataset_id}/preview`        | Return paginated preview rows                          |
| GET    | `/api/v1/datasets/{dataset_id}/profile`        | Return inferred schema and statistical profile         |
| DELETE | `/api/v1/datasets/{dataset_id}`                | Delete dataset metadata and storage object             |

### Charts

| Method | Path                                             | Purpose                         |
| ------ | ------------------------------------------------ | ------------------------------- |
| POST   | `/api/v1/datasets/{dataset_id}/charts/recommend` | Generate chart candidates       |
| POST   | `/api/v1/charts`                                 | Create chart                    |
| PATCH  | `/api/v1/charts/{chart_id}`                      | Update chart config or position |
| DELETE | `/api/v1/charts/{chart_id}`                      | Delete chart                    |

### AI

| Method | Path                                         | Purpose                                        |
| ------ | -------------------------------------------- | ---------------------------------------------- |
| POST   | `/api/v1/ai/chat`                            | Ask dataset or dashboard question              |
| POST   | `/api/v1/ai/insights`                        | Generate business insights                     |
| POST   | `/api/v1/ai/chart-config`                    | Generate chart config through provider adapter |
| POST   | `/api/v1/ai/agent/run`                       | Start agent workflow                           |
| GET    | `/api/v1/ai/conversations`                   | List conversations                             |
| GET    | `/api/v1/ai/conversations/{conversation_id}` | Read conversation messages                     |

### Dashboards

| Method | Path                                | Purpose                                 |
| ------ | ----------------------------------- | --------------------------------------- |
| POST   | `/api/v1/dashboards`                | Create dashboard                        |
| GET    | `/api/v1/dashboards`                | List dashboards                         |
| GET    | `/api/v1/dashboards/{dashboard_id}` | Read dashboard with charts and insights |
| PATCH  | `/api/v1/dashboards/{dashboard_id}` | Update metadata, layout, filters        |
| DELETE | `/api/v1/dashboards/{dashboard_id}` | Delete dashboard                        |

### Sharing

| Method | Path                                            | Purpose                      |
| ------ | ----------------------------------------------- | ---------------------------- |
| POST   | `/api/v1/dashboards/{dashboard_id}/share-links` | Create share link            |
| GET    | `/api/v1/share/{token}`                         | Read public shared dashboard |
| DELETE | `/api/v1/share-links/{share_link_id}`           | Revoke share link            |

### Jobs

| Method | Path                           | Purpose               |
| ------ | ------------------------------ | --------------------- |
| GET    | `/api/v1/jobs/{job_id}`        | Get async task status |
| POST   | `/api/v1/jobs/{job_id}/cancel` | Request cancellation  |

## 7. AI And Data Analysis Capabilities

### Deterministic Analysis Engine

The backend computes first-pass facts before involving AI:

- Missing value detection.
- Type inference.
- Numeric summaries.
- Categorical summaries.
- Outlier detection using IQR and z-score where appropriate.
- Correlation analysis for numeric columns.
- Time series detection for datetime columns.
- Aggregation candidates for categorical plus numeric columns.
- Chart candidate scoring.

AI receives structured dataset profiles, not raw full files by default. This
reduces cost, protects privacy, and makes results reproducible.

### AI Capabilities

MVP:

- Chat over dataset profile and preview samples.
- Business insights from deterministic profile.
- Chart configuration generation.
- Tool calling for safe actions such as "create_chart", "add_insight", and
  "update_dashboard_layout".

Later:

- Streaming answers.
- Agent workflow orchestration.
- SQL agent over governed query interfaces.
- Report generator.
- Vector retrieval for long-lived semantic memory.

## 8. Project Directory Structure

```text
.
|-- apps
|   |-- web
|   |   |-- app
|   |   |-- components
|   |   |-- features
|   |   |-- hooks
|   |   |-- lib
|   |   |-- stores
|   |   |-- styles
|   |   `-- tests
|   `-- api
|       |-- app
|       |   |-- api
|       |   |   `-- v1
|       |   |-- core
|       |   |-- db
|       |   |-- models
|       |   |-- repositories
|       |   |-- schemas
|       |   |-- services
|       |   |   |-- ai
|       |   |   |   |-- providers
|       |   |   |   `-- tools
|       |   |   |-- analysis
|       |   |   |-- charts
|       |   |   `-- dashboards
|       |   |-- tasks
|       |   |-- workers
|       |   `-- main.py
|       |-- tests
|       `-- pyproject.toml
|-- packages
|   |-- config
|   |-- eslint-config
|   `-- types
|-- infra
|   |-- docker
|   |-- postgres
|   |-- redis
|   `-- supabase
|-- docs
|-- scripts
|-- docker-compose.yml
|-- .env.example
|-- AGENTS.md
`-- MEMORY.md
```

## 9. Environment Variables

Implementation will add `.env.example` with these groups:

```dotenv
APP_ENV=development
LOG_LEVEL=info

DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/ai_analytics
REDIS_URL=redis://localhost:6379/0

SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
SUPABASE_STORAGE_BUCKET=datasets

AI_PROVIDER=mimo

MIMO_API_KEY=
MIMO_MODEL=mimo-v2-flash

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini

DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=

QWEN_API_KEY=
QWEN_MODEL=

CLAUDE_API_KEY=
CLAUDE_MODEL=
```

## 10. Development Roadmap

### STEP 1: Architecture

Status: complete.

Deliverables:

- System architecture.
- Technical architecture.
- Data flow.
- Database design.
- API design.
- Monorepo directory plan.
- Development roadmap.

### STEP 2: Project Initialization

Deliverables:

- Monorepo skeleton.
- Next.js frontend with App Router.
- FastAPI backend inside conda `pytorch`.
- Docker and docker-compose for PostgreSQL and Redis.
- `.env.example`.
- ESLint, Prettier, Husky, and Git hooks.
- Basic health check routes.

Important local note:

- Current shell cannot run `node` or `npm` successfully. Before STEP 2, install or expose
  a working Node.js runtime in PATH. npm package versions should be resolved at that time.
- Because the C drive has limited space, dependency downloads, caches, generated files,
  containers, datasets, and other large artifacts should be kept on the D drive whenever
  the tooling allows it.

### STEP 3: Authentication

Deliverables:

- Supabase Auth UI.
- Session handling.
- Backend JWT verification.
- Profile bootstrap.
- Workspace bootstrap.
- Protected app shell.

### STEP 4: File Upload

Deliverables:

- CSV upload UX.
- Supabase signed upload flow.
- Dataset metadata records.
- Upload progress, error states, and empty states.

### STEP 5: CSV Parsing

Deliverables:

- pandas parser.
- Preview endpoint.
- Type inference.
- Missing value and outlier detection.
- Correlation and summary statistics.

### STEP 6: Automatic Charts

Deliverables:

- Rule-based chart recommendations.
- Recharts renderer.
- Chart config schema.
- Empty and loading states.

### STEP 7: AI Q&A

Deliverables:

- AIProvider interface.
- MimoProvider.
- aiService.
- Dataset-aware chat.
- Conversation persistence.

### STEP 8: AI Insights

Deliverables:

- Insight generation.
- Trend, anomaly, correlation, and business summary outputs.
- Evidence metadata.
- Insight cards.

### STEP 9: Dashboards

Deliverables:

- Dashboard CRUD.
- Layout persistence.
- Chart persistence.
- Filters.
- Save and restore flow.

### STEP 10: Async Tasks

Deliverables:

- Redis broker.
- Celery workers.
- Job status endpoints.
- Worker logging.
- Retry and failure handling.

### STEP 11: AI Agent

Deliverables:

- Tool calling.
- Agent workflow runner.
- Guarded tool registry.
- Chart and insight actions.
- Optional streaming in later iteration.

### STEP 12: Deployment

Deliverables:

- Vercel frontend deployment.
- Railway or Render backend deployment.
- Docker image for backend.
- Runtime env documentation.
- Production readiness checklist.

## 11. Open Risks And Decisions

- Node.js/npm is not currently usable in this local shell. This blocks frontend
  initialization until fixed.
- Mimo API details must be verified from official documentation before coding
  `MimoProvider`; the adapter boundary prevents vendor details from leaking into
  product code.
- Large file support is intentionally later-phase. MVP should set upload size limits
  and analyze sampled previews plus deterministic profiles.
- Supabase Auth and PostgreSQL ownership must be carefully aligned. Backend API
  authorization should enforce workspace membership even if Supabase RLS is also used.
