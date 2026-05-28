"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  Clock3,
  FileSpreadsheet,
  Loader2,
  TriangleAlert,
  UploadCloud,
} from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { AgentPanel } from "@/features/agent/components/agent-panel";
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
import { AnalysisJobPanel } from "@/features/jobs/components/analysis-job-panel";
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
  const { getAccessToken, session, isConfigured, isLoading } = useAuth();
  const supabase = getSupabaseBrowserClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const maxUploadSize = Number(getPublicEnv().maxUploadSizeBytes ?? 26_214_400);

  const datasetsQuery = useQuery({
    queryKey: ["datasets", session?.user.id],
    queryFn: async () => listDatasets(await requireAccessToken(getAccessToken)),
    enabled: Boolean(session?.user.id),
  });
  const datasets = datasetsQuery.data?.datasets ?? [];
  const latestDataset = datasets[0];
  const readyDataset = datasets.find((dataset) => dataset.status === "ready");
  const previewQuery = useQuery({
    queryKey: ["dataset-preview", readyDataset?.id, session?.user.id],
    queryFn: async () =>
      getDatasetPreview({
        accessToken: await requireAccessToken(getAccessToken),
        datasetId: readyDataset?.id ?? "",
      }),
    enabled: Boolean(session?.user.id && readyDataset?.id),
  });
  const profileQuery = useQuery({
    queryKey: ["dataset-profile", readyDataset?.id, session?.user.id],
    queryFn: async () =>
      getDatasetProfile({
        accessToken: await requireAccessToken(getAccessToken),
        datasetId: readyDataset?.id ?? "",
      }),
    enabled: Boolean(session?.user.id && readyDataset?.id),
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const accessToken = await getAccessToken();
      if (!accessToken) {
        throw new Error("请先登录，再上传数据集。");
      }
      if (!supabase) {
        throw new Error("Supabase Storage 尚未配置。");
      }

      validateFile(file, maxUploadSize);

      setUploadProgress("正在创建上传会话");
      const uploadSession = await createUploadSession({
        accessToken,
        file,
      });

      setUploadProgress("正在上传到 Supabase Storage");
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

      setUploadProgress("正在确认上传结果");
      const dataset = await confirmUpload({
        accessToken: await requireAccessToken(getAccessToken),
        datasetId: uploadSession.dataset.id,
        file,
      });

      setUploadProgress("正在解析并分析数据集");
      return analyzeDataset({
        accessToken: await requireAccessToken(getAccessToken),
        datasetId: dataset.id,
      });
    },
    onSuccess: async (dataset) => {
      if (dataset.status === "ready") {
        toast.success("数据集已解析完成。");
      } else if (dataset.status === "failed") {
        toast.error(dataset.error_message || "数据集分析失败。");
      } else {
        toast.info(`数据集状态：${datasetStatusLabel(dataset.status)}。`);
      }
      setSelectedFile(null);
      setUploadProgress(null);
      inputRef.current?.form?.reset();
      await queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
    onError: (error) => {
      setUploadProgress(null);
      toast.error(error instanceof Error ? error.message : "上传失败。");
    },
  });

  const disabled = !isConfigured || !session || uploadMutation.isPending;

  return (
    <div className="rounded-[28px] border border-white/10 bg-[#111317] p-6 shadow-2xl shadow-black/30">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-zinc-400">数据集上传</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-normal">
            上传 CSV 或 Excel
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
            {selectedFile ? selectedFile.name : "选择数据文件"}
          </span>
          <span className="mt-1 text-xs text-zinc-500">
            支持 CSV、XLS、XLSX，最大 {formatBytes(maxUploadSize)}
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
          <EmptyNotice text="上传文件前，请先配置 Supabase 环境变量。" />
        ) : null}

        {isConfigured && !isLoading && !session ? (
          <EmptyNotice text="登录后才能把数据集上传到你的工作区。" />
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
              上传中
            </>
          ) : (
            "上传数据集"
          )}
        </Button>
      </form>

      <div className="mt-6 border-t border-white/10 pt-5">
        <p className="text-sm font-medium text-zinc-200">最近的数据集</p>
        {datasetsQuery.isLoading ? (
          <div className="mt-3 space-y-2">
            <div className="h-10 rounded-2xl bg-white/[0.05]" />
            <div className="h-10 rounded-2xl bg-white/[0.05]" />
          </div>
        ) : datasets.length ? (
          <div className="mt-3 space-y-2">
            {datasets.slice(0, 3).map((dataset) => (
              <div
                key={dataset.id}
                className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3"
              >
                <span className="truncate text-sm text-zinc-100">
                  {dataset.name}
                </span>
                <span className="text-xs uppercase tracking-wide text-zinc-500">
                  {datasetStatusLabel(dataset.status)}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-zinc-500">还没有上传数据集。</p>
        )}
      </div>

      <DatasetStatusPanel
        dataset={latestDataset}
        isLoading={datasetsQuery.isLoading}
      />

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

      <AnalysisJobPanel datasetId={readyDataset?.id} />

      <AgentPanel datasetId={readyDataset?.id} />
    </div>
  );
}

async function requireAccessToken(
  getAccessToken: () => Promise<string | null>,
) {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    throw new Error("请先登录，再使用工作区。");
  }
  return accessToken;
}

function DatasetStatusPanel({
  dataset,
  isLoading,
}: {
  dataset:
    | {
        name: string;
        status: string;
        row_count: number | null;
        column_count: number | null;
        error_message: string | null;
      }
    | undefined;
  isLoading: boolean;
}) {
  if (isLoading || !dataset) {
    return null;
  }

  const status = getDatasetStatusCopy(dataset);
  const Icon = status.icon;

  return (
    <div
      className={["mt-5 rounded-3xl border p-4", status.className].join(" ")}
    >
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
        <div className="min-w-0">
          <p className="text-sm font-medium">{status.title}</p>
          <p className="mt-1 text-sm opacity-80">{status.description}</p>
          {dataset.status === "ready" ? (
            <p className="mt-2 text-xs opacity-70">
              {dataset.row_count ?? 0} 行，{dataset.column_count ?? 0} 列
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function getDatasetStatusCopy(dataset: {
  name: string;
  status: string;
  error_message: string | null;
}) {
  if (dataset.status === "ready") {
    return {
      icon: CheckCircle2,
      title: `${dataset.name} 已就绪`,
      description: "下方已开放预览、字段画像、图表、洞察和仪表盘工具。",
      className: "border-emerald-400/20 bg-emerald-400/10 text-emerald-100",
    };
  }

  if (dataset.status === "failed") {
    return {
      icon: TriangleAlert,
      title: `${dataset.name} 分析失败`,
      description:
        dataset.error_message ||
        "文件已上传，但解析阶段失败，且后端没有记录到更具体的错误。",
      className: "border-rose-400/20 bg-rose-400/10 text-rose-100",
    };
  }

  if (dataset.status === "uploaded") {
    return {
      icon: Clock3,
      title: `${dataset.name} 已上传`,
      description:
        "文件已进入 Supabase Storage，正在等待解析或需要重新触发解析。",
      className: "border-sky-400/20 bg-sky-400/10 text-sky-100",
    };
  }

  return {
    icon: Clock3,
    title: `${dataset.name} 上传会话已创建`,
    description: "上传尚未确认。请重新选择文件并再次上传。",
    className: "border-amber-400/20 bg-amber-400/10 text-amber-100",
  };
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
          <p className="text-sm font-medium text-zinc-100">解析预览</p>
          <p className="mt-1 text-xs text-zinc-500">
            {String(profile.summary.row_count ?? 0)} 行，
            {String(profile.summary.column_count ?? 0)} 列
          </p>
        </div>
        <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-100">
          已就绪
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
    throw new Error("目前仅支持 CSV 和 Excel 文件。");
  }

  if (file.type && !ACCEPTED_MIME_TYPES.includes(file.type)) {
    throw new Error("文件内容类型暂不支持。");
  }

  if (file.size > maxUploadSize) {
    throw new Error(`文件必须小于 ${formatBytes(maxUploadSize)}。`);
  }
}

function datasetStatusLabel(status: string) {
  const labels: Record<string, string> = {
    created: "已创建",
    uploaded: "已上传",
    processing: "处理中",
    ready: "已就绪",
    failed: "失败",
  };

  return labels[status] ?? status;
}

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }
  return `${Math.round(bytes / (1024 * 1024))} MB`;
}
