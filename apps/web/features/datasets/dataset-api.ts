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
