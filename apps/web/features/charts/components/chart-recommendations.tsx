"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Loader2, Sparkles } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import {
  type Chart,
  listCharts,
  recommendCharts,
} from "@/features/datasets/dataset-api";

type ChartRecommendationsProps = {
  datasetId: string | undefined;
};

export function ChartRecommendations({ datasetId }: ChartRecommendationsProps) {
  const queryClient = useQueryClient();
  const { getAccessToken, session } = useAuth();

  const chartsQuery = useQuery({
    queryKey: ["dataset-charts", datasetId, session?.user.id],
    queryFn: async () =>
      listCharts({
        accessToken: await requireAccessToken(getAccessToken),
        datasetId: datasetId ?? "",
      }),
    enabled: Boolean(session?.user.id && datasetId),
  });

  const recommendMutation = useMutation({
    mutationFn: async () =>
      recommendCharts({
        accessToken: await requireAccessToken(getAccessToken),
        datasetId: datasetId ?? "",
      }),
    onSuccess: async () => {
      toast.success("图表已生成。");
      await queryClient.invalidateQueries({
        queryKey: ["dataset-charts", datasetId],
      });
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "图表推荐失败。");
    },
  });

  if (!datasetId) {
    return null;
  }

  const charts = chartsQuery.data?.charts ?? [];
  const isBusy = chartsQuery.isLoading || recommendMutation.isPending;

  return (
    <section className="mt-6 border-t border-white/10 pt-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-zinc-100">推荐图表</p>
          <p className="mt-1 text-xs text-zinc-500">
            基于字段类型识别结果，生成可解释的图表建议。
          </p>
        </div>
        <Button
          disabled={recommendMutation.isPending}
          onClick={() => recommendMutation.mutate()}
          type="button"
          variant={charts.length ? "outline" : "default"}
        >
          {recommendMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          )}
          生成图表
        </Button>
      </div>

      {isBusy ? (
        <ChartSkeleton />
      ) : charts.length ? (
        <div className="mt-4 grid gap-4 xl:grid-cols-2">
          {charts.map((chart) => (
            <ChartCard chart={chart} key={chart.id} />
          ))}
        </div>
      ) : (
        <div className="mt-4 flex min-h-44 flex-col items-center justify-center rounded-3xl border border-dashed border-white/15 bg-white/[0.03] px-4 text-center">
          <BarChart3 className="h-6 w-6 text-zinc-400" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium text-zinc-200">
            还没有图表建议。
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            数据画像完成后，可以生成候选图表。
          </p>
        </div>
      )}
    </section>
  );
}

function ChartCard({ chart }: { chart: Chart }) {
  const { data } = chart.config;
  const hasData = Array.isArray(data) && data.length > 0;

  return (
    <article className="min-h-80 rounded-3xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-medium text-zinc-100">
            {chart.title}
          </h3>
          <p className="mt-1 text-xs uppercase tracking-wide text-zinc-500">
            {chart.chart_type}
          </p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-zinc-400">
          {chart.created_by}
        </span>
      </div>

      {hasData ? (
        <div className="mt-4 h-60">
          <ResponsiveContainer height="100%" width="100%">
            {renderChart(chart)}
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="mt-4 flex h-60 items-center justify-center rounded-2xl bg-white/[0.03] text-sm text-zinc-500">
          暂无可渲染数据
        </div>
      )}
    </article>
  );
}

function renderChart(chart: Chart) {
  const { data, xKey, yKey } = chart.config;
  const gridColor = "rgba(255,255,255,0.08)";
  const axisColor = "rgba(212,212,216,0.72)";

  if (chart.chart_type === "line") {
    return (
      <LineChart data={data}>
        <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
        <XAxis dataKey={xKey} stroke={axisColor} tick={{ fontSize: 11 }} />
        <YAxis stroke={axisColor} tick={{ fontSize: 11 }} />
        <Tooltip contentStyle={tooltipStyle} />
        <Line
          dataKey={yKey}
          dot={false}
          stroke="#a7f3d0"
          strokeWidth={2}
          type="monotone"
        />
      </LineChart>
    );
  }

  if (chart.chart_type === "scatter") {
    return (
      <ScatterChart>
        <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
        <XAxis dataKey={xKey} name={xKey} stroke={axisColor} type="number" />
        <YAxis dataKey={yKey} name={yKey} stroke={axisColor} type="number" />
        <Tooltip
          contentStyle={tooltipStyle}
          cursor={{ strokeDasharray: "3 3" }}
        />
        <Scatter data={data} fill="#93c5fd" />
      </ScatterChart>
    );
  }

  return (
    <BarChart data={data}>
      <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
      <XAxis dataKey={xKey} stroke={axisColor} tick={{ fontSize: 11 }} />
      <YAxis stroke={axisColor} tick={{ fontSize: 11 }} />
      <Tooltip contentStyle={tooltipStyle} />
      <Bar dataKey={yKey} fill="#c4b5fd" radius={[8, 8, 0, 0]} />
    </BarChart>
  );
}

function ChartSkeleton() {
  return (
    <div className="mt-4 grid gap-4 xl:grid-cols-2">
      <div className="h-80 rounded-3xl bg-white/[0.04]" />
      <div className="hidden h-80 rounded-3xl bg-white/[0.04] xl:block" />
    </div>
  );
}

const tooltipStyle = {
  background: "#18181b",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: "16px",
  color: "#f4f4f5",
};

async function requireAccessToken(
  getAccessToken: () => Promise<string | null>,
) {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    throw new Error("请先登录，再使用图表功能。");
  }
  return accessToken;
}
