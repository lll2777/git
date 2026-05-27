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
  const { session } = useAuth();
  const accessToken = session?.access_token ?? "";

  const jobsQuery = useQuery({
    queryKey: ["dataset-jobs", datasetId, accessToken],
    queryFn: () =>
      listDatasetJobs({
        accessToken,
        datasetId: datasetId ?? "",
      }),
    enabled: Boolean(accessToken && datasetId),
    refetchInterval: (query) => {
      const jobs = query.state.data?.jobs ?? [];
      return jobs.some((job) => ["queued", "running"].includes(job.status))
        ? 3000
        : false;
    },
  });

  const enqueueMutation = useMutation({
    mutationFn: () =>
      enqueueAnalysisJob({
        accessToken,
        datasetId: datasetId ?? "",
      }),
    onSuccess: async () => {
      toast.success("Background analysis queued.");
      await queryClient.invalidateQueries({
        queryKey: ["dataset-jobs", datasetId],
      });
      await queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
    onError: (error) => {
      toast.error(
        error instanceof Error
          ? error.message
          : "Analysis job failed to queue.",
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
          <p className="text-sm font-medium text-zinc-100">Background jobs</p>
          <p className="mt-1 text-xs text-zinc-500">
            Queue long-running analysis through Redis and Celery.
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
          Queue analysis
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
            No background jobs yet.
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            Queue an analysis job when Redis and a Celery worker are running.
          </p>
        </div>
      )}

      {jobsQuery.isFetching && !jobsQuery.isLoading ? (
        <div className="mt-3 flex items-center gap-2 text-xs text-zinc-500">
          <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          Refreshing job status
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
              {job.job_type.replaceAll("_", " ")}
            </h3>
            <span
              className={[
                "rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-wide",
                statusClassName[job.status],
              ].join(" ")}
            >
              {job.status}
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
