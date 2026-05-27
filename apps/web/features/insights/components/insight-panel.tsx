"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Lightbulb, Loader2, Sparkles, TriangleAlert } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import {
  generateInsights,
  type Insight,
  listInsights,
} from "@/features/datasets/dataset-api";

type InsightPanelProps = {
  datasetId: string | undefined;
};

const severityClassName = {
  info: "border-sky-400/20 bg-sky-400/10 text-sky-100",
  low: "border-emerald-400/20 bg-emerald-400/10 text-emerald-100",
  medium: "border-amber-400/20 bg-amber-400/10 text-amber-100",
  high: "border-rose-400/20 bg-rose-400/10 text-rose-100",
};

export function InsightPanel({ datasetId }: InsightPanelProps) {
  const queryClient = useQueryClient();
  const { session } = useAuth();
  const accessToken = session?.access_token ?? "";

  const insightsQuery = useQuery({
    queryKey: ["dataset-insights", datasetId, accessToken],
    queryFn: () =>
      listInsights({
        accessToken,
        datasetId: datasetId ?? "",
      }),
    enabled: Boolean(accessToken && datasetId),
  });

  const generateMutation = useMutation({
    mutationFn: () =>
      generateInsights({
        accessToken,
        datasetId: datasetId ?? "",
      }),
    onSuccess: async () => {
      toast.success("Insights generated.");
      await queryClient.invalidateQueries({
        queryKey: ["dataset-insights", datasetId],
      });
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Insight generation failed.",
      );
    },
  });

  if (!datasetId) {
    return null;
  }

  const insights = insightsQuery.data?.insights ?? [];
  const isBusy = insightsQuery.isLoading || generateMutation.isPending;

  return (
    <section className="mt-6 border-t border-white/10 pt-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-zinc-100">Business insights</p>
          <p className="mt-1 text-xs text-zinc-500">
            Deterministic analysis plus AI-generated business interpretation.
          </p>
        </div>
        <Button
          disabled={generateMutation.isPending}
          onClick={() => generateMutation.mutate()}
          type="button"
          variant={insights.length ? "outline" : "default"}
        >
          {generateMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          )}
          Generate insights
        </Button>
      </div>

      {isBusy ? (
        <div className="mt-4 space-y-3">
          <div className="h-28 rounded-3xl bg-white/[0.04]" />
          <div className="h-28 rounded-3xl bg-white/[0.04]" />
        </div>
      ) : insights.length ? (
        <div className="mt-4 space-y-3">
          {insights.map((insight) => (
            <InsightCard insight={insight} key={insight.id} />
          ))}
        </div>
      ) : (
        <div className="mt-4 flex min-h-44 flex-col items-center justify-center rounded-3xl border border-dashed border-white/15 bg-white/[0.03] px-4 text-center">
          <Lightbulb className="h-6 w-6 text-zinc-400" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium text-zinc-200">
            No insights generated yet.
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            Generate insights after parsing and chart recommendation.
          </p>
        </div>
      )}
    </section>
  );
}

function InsightCard({ insight }: { insight: Insight }) {
  const Icon = insight.insight_type === "warning" ? TriangleAlert : Lightbulb;

  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-start gap-3">
        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-2">
          <Icon className="h-4 w-4 text-zinc-300" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-medium text-zinc-100">
              {insight.title}
            </h3>
            <span
              className={[
                "rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-wide",
                severityClassName[insight.severity],
              ].join(" ")}
            >
              {insight.severity}
            </span>
          </div>
          <p className="mt-2 text-sm leading-6 text-zinc-400">
            {insight.summary}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-zinc-500">
              {insight.insight_type}
            </span>
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-zinc-500">
              {insight.source}
            </span>
            {insight.provider ? (
              <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-zinc-500">
                {insight.provider}
              </span>
            ) : null}
          </div>
        </div>
      </div>
    </article>
  );
}
