"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Clock3, Loader2, Play, RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import {
  enqueueAnalysisJob,
  type Job,
  listDatasetJobs,
} from "@/features/datasets/dataset-api";

type AnalysisJobPanelProps = {
  datasetId: string | undefined;
};

const statusClassName = {
  queued: "border-sky-400/20 bg-sky-400/10 text-sky-100",
  running: "border-amber-400/20 bg-amber-400/10 text-amber-100",
  succeeded: "border-emerald-400/20 bg-emerald-400/10 text-emerald-100",
  failed: "border-rose-400/20 bg-rose-400/10 text-rose-100",
  cancelled: "border-zinc-400/20 bg-zinc-400/10 text-zinc-100",
};

export function AnalysisJobPanel({ datasetId }: AnalysisJobPanelProps) {
  const queryClient = useQueryClient();
  const { getAccessToken, session } = useAuth();

  const jobsQuery = useQuery({
    queryKey: ["dataset-jobs", datasetId, session?.user.id],
    queryFn: async () =>
      listDatasetJobs({
        accessToken: await requireAccessToken(getAccessToken),
        datasetId: datasetId ?? "",
      }),
    enabled: Boolean(session?.user.id && datasetId),
    refetchInterval: (query) => {
      const jobs = query.state.data?.jobs ?? [];
      return jobs.some((job) => ["queued", "running"].includes(job.status))
        ? 3000
        : false;
    },
  });

  const enqueueMutation = useMutation({
    mutationFn: async () =>
      enqueueAnalysisJob({
        accessToken: await requireAccessToken(getAccessToken),
        datasetId: datasetId ?? "",
      }),
    onSuccess: async () => {
      toast.success("后台分析任务已入队。");
      await queryClient.invalidateQueries({
        queryKey: ["dataset-jobs", datasetId],
      });
      await queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "分析任务入队失败。",
      );
    },
  });

  if (!datasetId) {
    return null;
  }

  const jobs = jobsQuery.data?.jobs ?? [];
  const isBusy = jobsQuery.isLoading || enqueueMutation.isPending;

  return (
    <section className="mt-6 border-t border-white/10 pt-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-zinc-100">后台任务</p>
          <p className="mt-1 text-xs text-zinc-500">
            通过 Redis 和 Celery 处理耗时分析。
          </p>
        </div>
        <Button
          disabled={enqueueMutation.isPending}
          onClick={() => enqueueMutation.mutate()}
          type="button"
          variant={jobs.length ? "outline" : "default"}
        >
          {enqueueMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Play className="h-4 w-4" aria-hidden="true" />
          )}
          加入分析队列
        </Button>
      </div>

      {isBusy ? (
        <div className="mt-4 h-20 rounded-3xl bg-white/[0.04]" />
      ) : jobs.length ? (
        <div className="mt-4 space-y-2">
          {jobs.slice(0, 4).map((job) => (
            <JobRow job={job} key={job.id} />
          ))}
        </div>
      ) : (
        <div className="mt-4 flex min-h-32 flex-col items-center justify-center rounded-3xl border border-dashed border-white/15 bg-white/[0.03] px-4 text-center">
          <Clock3 className="h-6 w-6 text-zinc-400" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium text-zinc-200">
            还没有后台任务。
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            Redis 和 Celery Worker 启动后，可以加入分析任务。
          </p>
        </div>
      )}

      {jobsQuery.isFetching && !jobsQuery.isLoading ? (
        <div className="mt-3 flex items-center gap-2 text-xs text-zinc-500">
          <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          正在刷新任务状态
        </div>
      ) : null}
    </section>
  );
}

function JobRow({ job }: { job: Job }) {
  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.03] px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-medium text-zinc-100">
              {jobTypeLabel(job.job_type)}
            </h3>
            <span
              className={[
                "rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-wide",
                statusClassName[job.status],
              ].join(" ")}
            >
              {jobStatusLabel(job.status)}
            </span>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-white/70 transition-all"
              style={{ width: `${job.progress}%` }}
            />
          </div>
          {job.error_message ? (
            <p className="mt-2 text-xs text-rose-200">{job.error_message}</p>
          ) : null}
        </div>
        <span className="text-xs text-zinc-500">{job.progress}%</span>
      </div>
    </article>
  );
}

function jobStatusLabel(status: Job["status"]) {
  const labels = {
    queued: "排队中",
    running: "运行中",
    succeeded: "成功",
    failed: "失败",
    cancelled: "已取消",
  };

  return labels[status];
}

function jobTypeLabel(type: string) {
  const labels: Record<string, string> = {
    dataset_analysis: "数据集分析",
  };

  return labels[type] ?? type.replaceAll("_", " ");
}

async function requireAccessToken(
  getAccessToken: () => Promise<string | null>,
) {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    throw new Error("请先登录，再创建后台任务。");
  }
  return accessToken;
}
