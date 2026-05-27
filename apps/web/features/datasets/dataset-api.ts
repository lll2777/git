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
