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
  const { getAccessToken, session } = useAuth();

  const insightsQuery = useQuery({
    queryKey: ["dataset-insights", datasetId, session?.user.id],
    queryFn: async () =>
      listInsights({
        accessToken: await requireAccessToken(getAccessToken),
        datasetId: datasetId ?? "",
      }),
    enabled: Boolean(session?.user.id && datasetId),
  });

  const generateMutation = useMutation({
    mutationFn: async () =>
      generateInsights({
        accessToken: await requireAccessToken(getAccessToken),
        datasetId: datasetId ?? "",
      }),
    onSuccess: async () => {
      toast.success("洞察已生成。");
      await queryClient.invalidateQueries({
        queryKey: ["dataset-insights", datasetId],
      });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "洞察生成失败。");
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
          <p className="text-sm font-medium text-zinc-100">业务洞察</p>
          <p className="mt-1 text-xs text-zinc-500">
            结合确定性分析与 AI 解释，生成业务可读结论。
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
          生成洞察
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
            还没有生成洞察。
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            完成解析和图表推荐后，可以生成业务洞察。
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
              {severityLabel(insight.severity)}
            </span>
          </div>
          <p className="mt-2 text-sm leading-6 text-zinc-400">
            {insight.summary}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-zinc-500">
              {insightTypeLabel(insight.insight_type)}
            </span>
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-zinc-500">
              {sourceLabel(insight.source)}
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

function severityLabel(severity: Insight["severity"]) {
  const labels = {
    info: "信息",
    low: "低",
    medium: "中",
    high: "高",
  };

  return labels[severity];
}

function insightTypeLabel(type: string) {
  const labels: Record<string, string> = {
    summary: "摘要",
    warning: "风险",
    trend: "趋势",
    anomaly: "异常",
    correlation: "相关性",
    opportunity: "机会",
  };

  return labels[type] ?? type;
}

function sourceLabel(source: string) {
  const labels: Record<string, string> = {
    deterministic: "规则分析",
    ai: "AI 生成",
  };

  return labels[source] ?? source;
}

async function requireAccessToken(
  getAccessToken: () => Promise<string | null>,
) {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    throw new Error("请先登录，再生成洞察。");
  }
  return accessToken;
}
