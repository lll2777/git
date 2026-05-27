"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileSpreadsheet, Loader2, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { DatasetQuestionPanel } from "@/features/ai/components/dataset-question-panel";
import { useAuth } from "@/features/auth/auth-provider";
import { ChartRecommendations } from "@/features/charts/components/chart-recommendations";
import {
  analyzeDataset,
  confirmUpload,
  createUploadSession,
  getDatasetPreview,
  getDatasetProfile,
  listDatasets,
} from "@/features/datasets/dataset-api";
import { DashboardPanel } from "@/features/dashboards/components/dashboard-panel";
import { InsightPanel } from "@/features/insights/components/insight-panel";
import { getPublicEnv } from "@/lib/env";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

const ACCEPTED_EXTENSIONS = [".csv", ".xls", ".xlsx"];
const ACCEPTED_MIME_TYPES = [
  "text/csv",
  "application/csv",
  "application/octet-stream",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
];

export function DatasetUploadCard() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const queryClient = useQueryClient();
  const { session, isConfigured, isLoading } = useAuth();
  const supabase = getSupabaseBrowserClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const maxUploadSize = Number(getPublicEnv().maxUploadSizeBytes ?? 26_214_400);

  const datasetsQuery = useQuery({
    queryKey: ["datasets", session?.access_token],
    queryFn: () => listDatasets(session?.access_token ?? ""),
    enabled: Boolean(session?.access_token),
  });
  const readyDataset = datasetsQuery.data?.datasets.find(
    (dataset) => dataset.status === "ready",
  );
  const previewQuery = useQuery({
    queryKey: ["dataset-preview", readyDataset?.id, session?.access_token],
    queryFn: () =>
      getDatasetPreview({
        accessToken: session?.access_token ?? "",
        datasetId: readyDataset?.id ?? "",
      }),
    enabled: Boolean(session?.access_token && readyDataset?.id),
  });
  const profileQuery = useQuery({
    queryKey: ["dataset-profile", readyDataset?.id, session?.access_token],
    queryFn: () =>
      getDatasetProfile({
        accessToken: session?.access_token ?? "",
        datasetId: readyDataset?.id ?? "",
      }),
    enabled: Boolean(session?.access_token && readyDataset?.id),
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!session?.access_token) {
        throw new Error("Sign in before uploading a dataset.");
      }
      if (!supabase) {
        throw new Error("Supabase Storage is not configured.");
      }

      validateFile(file, maxUploadSize);

      setUploadProgress("Creating upload session");
      const uploadSession = await createUploadSession({
        accessToken: session.access_token,
        file,
      });

      setUploadProgress("Uploading to Supabase Storage");
      const { error } = await supabase.storage
        .from(uploadSession.upload.bucket)
        .upload(uploadSession.upload.path, file, {
          cacheControl: "3600",
          contentType: file.type || "application/octet-stream",
          upsert: false,
        });

      if (error) {
        throw error;
      }

      setUploadProgress("Confirming upload");
      const dataset = await confirmUpload({
        accessToken: session.access_token,
        datasetId: uploadSession.dataset.id,
        file,
      });

      setUploadProgress("Parsing and profiling dataset");
      return analyzeDataset({
        accessToken: session.access_token,
        datasetId: dataset.id,
      });
    },
    onSuccess: async () => {
      toast.success("Dataset uploaded.");
      setSelectedFile(null);
      setUploadProgress(null);
      inputRef.current?.form?.reset();
      await queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
    onError: (error) => {
      setUploadProgress(null);
      toast.error(error instanceof Error ? error.message : "Upload failed.");
    },
  });

  const disabled = !isConfigured || !session || uploadMutation.isPending;

  return (
    <div className="rounded-[28px] border border-white/10 bg-[#111317] p-6 shadow-2xl shadow-black/30">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-zinc-400">Dataset upload</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-normal">
            Upload CSV or Excel
          </h2>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-3">
          <FileSpreadsheet
            className="h-5 w-5 text-zinc-300"
            aria-hidden="true"
          />
        </div>
      </div>

      <form
        className="mt-6 space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          if (selectedFile) {
            uploadMutation.mutate(selectedFile);
          }
        }}
      >
        <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed border-white/15 bg-white/[0.03] px-4 py-8 text-center transition hover:bg-white/[0.06]">
          <UploadCloud className="h-7 w-7 text-zinc-300" aria-hidden="true" />
          <span className="mt-3 text-sm font-medium text-zinc-100">
            {selectedFile ? selectedFile.name : "Choose a dataset file"}
          </span>
          <span className="mt-1 text-xs text-zinc-500">
            CSV, XLS, or XLSX up to {formatBytes(maxUploadSize)}
          </span>
          <input
            ref={inputRef}
            className="sr-only"
            type="file"
            accept={ACCEPTED_EXTENSIONS.join(",")}
            disabled={uploadMutation.isPending}
            onChange={(event) => {
              const file = event.target.files?.[0] ?? null;
              setSelectedFile(file);
            }}
          />
        </label>

        {!isConfigured ? (
          <EmptyNotice text="Configure Supabase environment variables before uploading files." />
        ) : null}

        {isConfigured && !isLoading && !session ? (
          <EmptyNotice text="Sign in to upload datasets to your workspace." />
        ) : null}

        {uploadProgress ? (
          <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-sm text-zinc-300">
            {uploadProgress}
          </div>
        ) : null}

        <Button
          className="w-full"
          disabled={disabled || !selectedFile}
          type="submit"
        >
          {uploadMutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              Uploading
            </>
          ) : (
            "Upload dataset"
          )}
        </Button>
      </form>

      <div className="mt-6 border-t border-white/10 pt-5">
        <p className="text-sm font-medium text-zinc-200">Recent datasets</p>
        {datasetsQuery.isLoading ? (
          <div className="mt-3 space-y-2">
            <div className="h-10 rounded-2xl bg-white/[0.05]" />
            <div className="h-10 rounded-2xl bg-white/[0.05]" />
          </div>
        ) : datasetsQuery.data?.datasets.length ? (
          <div className="mt-3 space-y-2">
            {datasetsQuery.data.datasets.slice(0, 3).map((dataset) => (
              <div
                key={dataset.id}
                className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3"
              >
                <span className="truncate text-sm text-zinc-100">
                  {dataset.name}
                </span>
                <span className="text-xs uppercase tracking-wide text-zinc-500">
                  {dataset.status}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-zinc-500">
            No datasets uploaded yet.
          </p>
        )}
      </div>

      <DatasetPreviewPanel
        isLoading={previewQuery.isLoading || profileQuery.isLoading}
        preview={previewQuery.data}
        profile={profileQuery.data}
      />

      <ChartRecommendations datasetId={readyDataset?.id} />

      <DatasetQuestionPanel datasetId={readyDataset?.id} />

      <InsightPanel datasetId={readyDataset?.id} />

      <DashboardPanel
        datasetId={readyDataset?.id}
        datasetName={readyDataset?.name}
      />
    </div>
  );
}

function DatasetPreviewPanel({
  isLoading,
  preview,
  profile,
}: {
  isLoading: boolean;
  preview:
    | {
        columns: string[];
        rows: Record<string, unknown>[];
      }
    | undefined;
  profile:
    | {
        columns: Array<{
          name: string;
          data_type: string;
          missing_count: number;
        }>;
        summary: Record<string, unknown>;
      }
    | undefined;
}) {
  if (isLoading) {
    return (
      <div className="mt-6 rounded-3xl border border-white/10 bg-white/[0.03] p-4">
        <div className="h-4 w-32 rounded-full bg-white/[0.08]" />
        <div className="mt-4 h-24 rounded-2xl bg-white/[0.05]" />
      </div>
    );
  }

  if (!preview || !profile) {
    return null;
  }

  const visibleColumns = preview.columns.slice(0, 4);
  const visibleRows = preview.rows.slice(0, 5);

  return (
    <div className="mt-6 rounded-3xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-zinc-100">Parsed preview</p>
          <p className="mt-1 text-xs text-zinc-500">
            {String(profile.summary.row_count ?? 0)} rows,{" "}
            {String(profile.summary.column_count ?? 0)} columns
          </p>
        </div>
        <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-100">
          Ready
        </span>
      </div>

      <div className="mt-4 overflow-hidden rounded-2xl border border-white/10">
        <div
          className="grid bg-white/[0.06]"
          style={{
            gridTemplateColumns: `repeat(${visibleColumns.length}, minmax(0, 1fr))`,
          }}
        >
          {visibleColumns.map((column) => (
            <div
              key={column}
              className="truncate px-3 py-2 text-xs font-medium text-zinc-300"
            >
              {column}
            </div>
          ))}
        </div>
        {visibleRows.map((row, index) => (
          <div
            key={index}
            className="grid border-t border-white/10"
            style={{
              gridTemplateColumns: `repeat(${visibleColumns.length}, minmax(0, 1fr))`,
            }}
          >
            {visibleColumns.map((column) => (
              <div
                key={column}
                className="truncate px-3 py-2 text-xs text-zinc-500"
              >
                {String(row[column] ?? "")}
              </div>
            ))}
          </div>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {profile.columns.slice(0, 5).map((column) => (
          <span
            key={column.name}
            className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-zinc-300"
          >
            {column.name}: {column.data_type}
          </span>
        ))}
      </div>
    </div>
  );
}

function EmptyNotice({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm text-amber-100">
      {text}
    </div>
  );
}

function validateFile(file: File, maxUploadSize: number) {
  const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (!ACCEPTED_EXTENSIONS.includes(extension)) {
    throw new Error("Only CSV and Excel files are supported.");
  }

  if (file.type && !ACCEPTED_MIME_TYPES.includes(file.type)) {
    throw new Error("Unsupported file content type.");
  }

  if (file.size > maxUploadSize) {
    throw new Error(`File must be smaller than ${formatBytes(maxUploadSize)}.`);
  }
}

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }
  return `${Math.round(bytes / (1024 * 1024))} MB`;
}
