"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bot,
  CheckCircle2,
  Loader2,
  Play,
  Workflow,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import {
  type AgentRun,
  listAgentRuns,
  runDatasetAgent,
} from "@/features/datasets/dataset-api";

type AgentPanelProps = {
  datasetId: string | undefined;
};

const statusClassName = {
  running: "border-amber-400/20 bg-amber-400/10 text-amber-100",
  succeeded: "border-emerald-400/20 bg-emerald-400/10 text-emerald-100",
  failed: "border-rose-400/20 bg-rose-400/10 text-rose-100",
  cancelled: "border-zinc-400/20 bg-zinc-400/10 text-zinc-100",
  skipped: "border-zinc-400/20 bg-zinc-400/10 text-zinc-100",
};

export function AgentPanel({ datasetId }: AgentPanelProps) {
  const queryClient = useQueryClient();
  const { session } = useAuth();
  const accessToken = session?.access_token ?? "";

  const runsQuery = useQuery({
    queryKey: ["dataset-agent-runs", datasetId, accessToken],
    queryFn: () =>
      listAgentRuns({
        accessToken,
        datasetId: datasetId ?? "",
      }),
    enabled: Boolean(accessToken && datasetId),
  });

  const runMutation = useMutation({
    mutationFn: () =>
      runDatasetAgent({
        accessToken,
        datasetId: datasetId ?? "",
        objective: "prepare_dashboard",
      }),
    onSuccess: async () => {
      toast.success("Agent workflow completed.");
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["dataset-agent-runs", datasetId],
        }),
        queryClient.invalidateQueries({
          queryKey: ["dataset-charts", datasetId],
        }),
        queryClient.invalidateQueries({
          queryKey: ["dataset-insights", datasetId],
        }),
        queryClient.invalidateQueries({
          queryKey: ["dataset-dashboards", datasetId],
        }),
      ]);
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Agent workflow failed.",
      );
    },
  });

  if (!datasetId) {
    return null;
  }

  const runs = runsQuery.data?.runs ?? [];
  const isBusy = runsQuery.isLoading || runMutation.isPending;

  return (
    <section className="mt-6 border-t border-white/10 pt-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-zinc-100">AI Agent</p>
          <p className="mt-1 text-xs text-zinc-500">
            Run a controlled workflow across charts, insights, and dashboards.
          </p>
        </div>
        <Button
          disabled={runMutation.isPending}
          onClick={() => runMutation.mutate()}
          type="button"
          variant={runs.length ? "outline" : "default"}
        >
          {runMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Play className="h-4 w-4" aria-hidden="true" />
          )}
          Run agent
        </Button>
      </div>

      {isBusy ? (
        <div className="mt-4 h-28 rounded-3xl bg-white/[0.04]" />
      ) : runs.length ? (
        <div className="mt-4 space-y-3">
          {runs.slice(0, 3).map((run) => (
            <AgentRunCard key={run.id} run={run} />
          ))}
        </div>
      ) : (
        <div className="mt-4 flex min-h-36 flex-col items-center justify-center rounded-3xl border border-dashed border-white/15 bg-white/[0.03] px-4 text-center">
          <Bot className="h-6 w-6 text-zinc-400" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium text-zinc-200">
            No agent runs yet.
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            Run the agent after the dataset profile is ready.
          </p>
        </div>
      )}
    </section>
  );
}

function AgentRunCard({ run }: { run: AgentRun }) {
  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Workflow className="h-4 w-4 text-zinc-400" aria-hidden="true" />
            <h3 className="truncate text-sm font-medium text-zinc-100">
              {run.objective.replaceAll("_", " ")}
            </h3>
          </div>
          <p className="mt-1 text-xs text-zinc-500">
            {run.steps.length} audited steps
          </p>
        </div>
        <StatusBadge status={run.status} />
      </div>

      <div className="mt-4 space-y-2">
        {run.steps.map((step) => (
          <div
            className="flex items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/[0.03] px-3 py-2"
            key={step.id}
          >
            <div className="flex min-w-0 items-center gap-2">
              {step.status === "succeeded" ? (
                <CheckCircle2
                  className="h-4 w-4 text-emerald-200"
                  aria-hidden="true"
                />
              ) : step.status === "failed" ? (
                <XCircle className="h-4 w-4 text-rose-200" aria-hidden="true" />
              ) : (
                <Loader2
                  className="h-4 w-4 animate-spin text-amber-200"
                  aria-hidden="true"
                />
              )}
              <span className="truncate text-xs text-zinc-300">
                {step.step_name.replaceAll("_", " ")}
              </span>
            </div>
            <StatusBadge status={step.status} />
          </div>
        ))}
      </div>

      {run.error_message ? (
        <p className="mt-3 text-xs text-rose-200">{run.error_message}</p>
      ) : null}
    </article>
  );
}

function StatusBadge({ status }: { status: keyof typeof statusClassName }) {
  return (
    <span
      className={[
        "shrink-0 rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-wide",
        statusClassName[status],
      ].join(" ")}
    >
      {status}
    </span>
  );
}
