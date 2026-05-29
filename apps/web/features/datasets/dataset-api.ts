import { apiFetch } from "@/lib/api/client";

export type Dataset = {
  id: string;
  workspace_id: string;
  owner_id: string;
  name: string;
  status: "created" | "uploaded" | "processing" | "ready" | "failed";
  row_count: number | null;
  column_count: number | null;
  storage_bucket: string | null;
  storage_path: string | null;
  original_filename: string | null;
  content_type: string | null;
  size_bytes: number | null;
  error_message: string | null;
};

export type UploadSession = {
  dataset: Dataset;
  upload: {
    bucket: string;
    path: string;
    strategy: "supabase_client_upload";
  };
};

export async function createUploadSession(params: {
  accessToken: string;
  file: File;
}) {
  return apiFetch<UploadSession>("/api/v1/datasets/upload-session", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${params.accessToken}`,
    },
    body: JSON.stringify({
      filename: params.file.name,
      content_type: params.file.type || "application/octet-stream",
      size_bytes: params.file.size,
    }),
  });
}

export async function confirmUpload(params: {
  accessToken: string;
  datasetId: string;
  file: File;
}) {
  return apiFetch<Dataset>(
    `/api/v1/datasets/${params.datasetId}/confirm-upload`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
      body: JSON.stringify({
        size_bytes: params.file.size,
        content_type: params.file.type || "application/octet-stream",
      }),
    },
  );
}

export async function listDatasets(accessToken: string) {
  return apiFetch<{ datasets: Dataset[] }>("/api/v1/datasets", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function analyzeDataset(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<Dataset>(`/api/v1/datasets/${params.datasetId}/analyze`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${params.accessToken}`,
    },
  });
}

export type DatasetPreview = {
  dataset_id: string;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
};

export type DatasetProfile = {
  dataset: Dataset;
  columns: Array<{
    name: string;
    original_name: string;
    data_type: string;
    semantic_type: string | null;
    nullable: boolean;
    missing_count: number;
    unique_count: number | null;
  }>;
  summary: Record<string, unknown>;
  missing_values: Record<string, unknown>;
  outliers: Record<string, unknown>;
  correlations: Record<string, unknown>;
  time_series: Record<string, unknown>;
  categorical_aggregates: Record<string, unknown>;
};

export type ChartKind =
  | "area"
  | "bar"
  | "composed"
  | "horizontal_bar"
  | "line"
  | "pie"
  | "scatter";

export type ChartConfig = {
  xKey: string;
  yKey?: string;
  xLabel?: string;
  yLabel?: string;
  series?: Array<{
    key: string;
    label: string;
    type: "area" | "bar" | "line";
  }>;
  data: Array<Record<string, string | number | null>>;
};

export type Chart = {
  id: string;
  dataset_id: string;
  title: string;
  chart_type: ChartKind;
  config: ChartConfig;
  query_spec: Record<string, unknown>;
  created_by: string;
};

export type ChartRecommendationResponse = {
  charts: Chart[];
};

export type AIMessage = {
  id: string;
  conversation_id: string;
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  provider: string | null;
  model: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
};

export type AIConversation = {
  id: string;
  dataset_id: string;
  title: string;
  status: string;
};

export type DatasetChatResponse = {
  conversation: AIConversation;
  answer: AIMessage;
  messages: AIMessage[];
  tool_calls: Array<Record<string, unknown>>;
};

export type Insight = {
  id: string;
  dataset_id: string;
  title: string;
  summary: string;
  insight_type:
    | "summary"
    | "trend"
    | "anomaly"
    | "correlation"
    | "business"
    | "warning";
  severity: "info" | "low" | "medium" | "high";
  evidence: Record<string, unknown>;
  provider: string | null;
  model: string | null;
  source: "deterministic" | "ai" | "user";
  created_at: string | null;
};

export type InsightResponse = {
  insights: Insight[];
};

export type DashboardSummary = {
  id: string;
  workspace_id: string;
  dataset_id: string;
  title: string;
  description: string | null;
  layout: Record<string, unknown>;
  status: string;
  chart_count: number;
  insight_count: number;
  created_at: string | null;
  updated_at: string | null;
};

export type Dashboard = DashboardSummary & {
  charts: Chart[];
  insights: Insight[];
};

export type DashboardListResponse = {
  dashboards: DashboardSummary[];
};

export type JobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

export type Job = {
  id: string;
  workspace_id: string;
  dataset_id: string | null;
  job_type: string;
  status: JobStatus;
  progress: number;
  celery_task_id: string | null;
  payload: Record<string, unknown>;
  result: Record<string, unknown>;
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type JobListResponse = {
  jobs: Job[];
};

export type AgentStep = {
  id: string;
  run_id: string;
  step_name: string;
  status: "running" | "succeeded" | "failed" | "skipped";
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
};

export type AgentRun = {
  id: string;
  workspace_id: string;
  dataset_id: string;
  objective: string;
  status: "running" | "succeeded" | "failed" | "cancelled";
  result: Record<string, unknown>;
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
  steps: AgentStep[];
};

export type AgentRunListResponse = {
  runs: AgentRun[];
};

export async function getDatasetPreview(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<DatasetPreview>(
    `/api/v1/datasets/${params.datasetId}/preview`,
    {
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
    },
  );
}

export async function getDatasetProfile(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<DatasetProfile>(
    `/api/v1/datasets/${params.datasetId}/profile`,
    {
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
    },
  );
}

export async function listCharts(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<ChartRecommendationResponse>(
    `/api/v1/datasets/${params.datasetId}/charts`,
    {
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
    },
  );
}

export async function recommendCharts(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<ChartRecommendationResponse>(
    `/api/v1/datasets/${params.datasetId}/charts/recommend`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
    },
  );
}

export async function askDatasetQuestion(params: {
  accessToken: string;
  datasetId: string;
  question: string;
  conversationId?: string | null;
}) {
  return apiFetch<DatasetChatResponse>(
    `/api/v1/datasets/${params.datasetId}/ai/chat`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
      body: JSON.stringify({
        question: params.question,
        conversation_id: params.conversationId,
      }),
    },
  );
}

export async function listInsights(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<InsightResponse>(
    `/api/v1/datasets/${params.datasetId}/insights`,
    {
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
    },
  );
}

export async function generateInsights(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<InsightResponse>(
    `/api/v1/datasets/${params.datasetId}/insights/generate`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
    },
  );
}

export async function listDashboards(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<DashboardListResponse>(
    `/api/v1/datasets/${params.datasetId}/dashboards`,
    {
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
    },
  );
}

export async function saveDashboard(params: {
  accessToken: string;
  datasetId: string;
  title?: string;
  description?: string;
}) {
  return apiFetch<Dashboard>(
    `/api/v1/datasets/${params.datasetId}/dashboards`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
      body: JSON.stringify({
        title: params.title,
        description: params.description,
      }),
    },
  );
}

export async function enqueueAnalysisJob(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<Job>(`/api/v1/datasets/${params.datasetId}/analysis-jobs`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${params.accessToken}`,
    },
  });
}

export async function listDatasetJobs(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<JobListResponse>(
    `/api/v1/datasets/${params.datasetId}/jobs`,
    {
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
    },
  );
}

export async function runDatasetAgent(params: {
  accessToken: string;
  datasetId: string;
  objective: string;
}) {
  return apiFetch<AgentRun>(`/api/v1/datasets/${params.datasetId}/agent-runs`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${params.accessToken}`,
    },
    body: JSON.stringify({
      objective: params.objective,
    }),
  });
}

export async function listAgentRuns(params: {
  accessToken: string;
  datasetId: string;
}) {
  return apiFetch<AgentRunListResponse>(
    `/api/v1/datasets/${params.datasetId}/agent-runs`,
    {
      headers: {
        Authorization: `Bearer ${params.accessToken}`,
      },
    },
  );
}
