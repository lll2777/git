"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Loader2, Sparkles } from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
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

const chartColors = [
  "#a7f3d0",
  "#c4b5fd",
  "#93c5fd",
  "#fcd34d",
  "#fda4af",
  "#67e8f9",
  "#f0abfc",
  "#bef264",
];
const chartFontFamily =
  '"Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "Source Han Sans SC", SimHei, Arial, sans-serif';
const commonTick = {
  fill: "rgba(212,212,216,0.78)",
  fontFamily: chartFontFamily,
  fontSize: 11,
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
            基于字段类型、时间序列和分类聚合，生成多角度可解释图表。
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
    <article className="min-h-96 rounded-3xl border border-white/10 bg-white/[0.03] p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-medium text-zinc-100">
            {chartTitle(chart)}
          </h3>
          <p className="mt-1 text-xs text-zinc-500">
            {chartTypeLabel(chart.chart_type)}
          </p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-zinc-400">
          {chart.created_by === "system" ? "系统推荐" : chart.created_by}
        </span>
      </div>

      {hasData ? (
        <div className="mt-4 h-72">
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
  const { data, series, xKey, yKey } = chart.config;
  const valueKey = yKey ?? "value";
  const gridColor = "rgba(255,255,255,0.08)";
  const axisColor = "rgba(212,212,216,0.72)";

  if (chart.chart_type === "area") {
    return (
      <AreaChart data={data} margin={chartMargin}>
        <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
        <XAxis dataKey={xKey} stroke={axisColor} tick={commonTick} />
        <YAxis stroke={axisColor} tick={commonTick} />
        <Tooltip contentStyle={tooltipStyle} formatter={tooltipFormatter} />
        <Area
          dataKey={valueKey}
          fill="#a7f3d0"
          fillOpacity={0.22}
          name={chart.config.yLabel ?? "数值"}
          stroke="#a7f3d0"
          strokeWidth={2}
          type="monotone"
        />
      </AreaChart>
    );
  }

  if (chart.chart_type === "composed" && series?.length) {
    return (
      <ComposedChart data={data} margin={chartMargin}>
        <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
        <XAxis dataKey={xKey} stroke={axisColor} tick={commonTick} />
        <YAxis stroke={axisColor} tick={commonTick} />
        <Tooltip contentStyle={tooltipStyle} formatter={tooltipFormatter} />
        <Legend wrapperStyle={legendStyle} />
        {series.map((item, index) =>
          item.type === "line" ? (
            <Line
              dataKey={item.key}
              dot={false}
              key={item.key}
              name={item.label}
              stroke={chartColors[index % chartColors.length]}
              strokeWidth={2}
              type="monotone"
            />
          ) : (
            <Bar
              dataKey={item.key}
              fill={chartColors[index % chartColors.length]}
              key={item.key}
              name={item.label}
              radius={[8, 8, 0, 0]}
            />
          ),
        )}
      </ComposedChart>
    );
  }

  if (chart.chart_type === "line") {
    return (
      <LineChart data={data} margin={chartMargin}>
        <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
        <XAxis dataKey={xKey} stroke={axisColor} tick={commonTick} />
        <YAxis stroke={axisColor} tick={commonTick} />
        <Tooltip contentStyle={tooltipStyle} formatter={tooltipFormatter} />
        <Line
          dataKey={valueKey}
          dot={false}
          name={chart.config.yLabel ?? "数值"}
          stroke="#a7f3d0"
          strokeWidth={2}
          type="monotone"
        />
      </LineChart>
    );
  }

  if (chart.chart_type === "scatter") {
    return (
      <ScatterChart margin={chartMargin}>
        <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
        <XAxis
          dataKey={xKey}
          name={chart.config.xLabel ?? xKey}
          stroke={axisColor}
          tick={commonTick}
          type="number"
        />
        <YAxis
          dataKey={valueKey}
          name={chart.config.yLabel ?? valueKey}
          stroke={axisColor}
          tick={commonTick}
          type="number"
        />
        <Tooltip
          contentStyle={tooltipStyle}
          cursor={{ strokeDasharray: "3 3" }}
          formatter={tooltipFormatter}
        />
        <Scatter data={data} fill="#93c5fd" name={chartTitle(chart)} />
      </ScatterChart>
    );
  }

  if (chart.chart_type === "pie") {
    return (
      <PieChart margin={chartMargin}>
        <Tooltip contentStyle={tooltipStyle} formatter={tooltipFormatter} />
        <Legend wrapperStyle={legendStyle} />
        <Pie
          cx="50%"
          cy="48%"
          data={data}
          dataKey={valueKey}
          innerRadius="48%"
          label={({ name }) => String(name)}
          labelLine={false}
          nameKey={xKey}
          outerRadius="78%"
          paddingAngle={2}
        >
          {data.map((_, index) => (
            <Cell fill={chartColors[index % chartColors.length]} key={index} />
          ))}
        </Pie>
      </PieChart>
    );
  }

  if (chart.chart_type === "horizontal_bar") {
    return (
      <BarChart data={data} layout="vertical" margin={horizontalBarMargin}>
        <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
        <XAxis stroke={axisColor} tick={commonTick} type="number" />
        <YAxis
          dataKey={xKey}
          stroke={axisColor}
          tick={commonTick}
          type="category"
          width={72}
        />
        <Tooltip contentStyle={tooltipStyle} formatter={tooltipFormatter} />
        <Bar
          dataKey={valueKey}
          fill="#c4b5fd"
          name={chart.config.yLabel ?? "数值"}
          radius={[0, 8, 8, 0]}
        />
      </BarChart>
    );
  }

  return (
    <BarChart data={data} margin={chartMargin}>
      <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
      <XAxis dataKey={xKey} stroke={axisColor} tick={commonTick} />
      <YAxis stroke={axisColor} tick={commonTick} />
      <Tooltip contentStyle={tooltipStyle} formatter={tooltipFormatter} />
      <Bar
        dataKey={valueKey}
        fill="#c4b5fd"
        name={chart.config.yLabel ?? "数值"}
        radius={[8, 8, 0, 0]}
      />
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
  fontFamily: chartFontFamily,
};

const legendStyle = {
  color: "#d4d4d8",
  fontFamily: chartFontFamily,
  fontSize: 12,
};

const chartMargin = {
  bottom: 8,
  left: 4,
  right: 12,
  top: 10,
};

const horizontalBarMargin = {
  bottom: 8,
  left: 12,
  right: 12,
  top: 10,
};

function tooltipFormatter(value: unknown, name: unknown) {
  return [formatChartValue(value), String(name)];
}

function formatChartValue(value: unknown) {
  if (typeof value !== "number") {
    return String(value ?? "");
  }
  return new Intl.NumberFormat("zh-CN", {
    maximumFractionDigits: 2,
  }).format(value);
}

function chartTypeLabel(type: Chart["chart_type"]) {
  const labels: Record<Chart["chart_type"], string> = {
    area: "面积图",
    bar: "柱状图",
    composed: "组合图",
    horizontal_bar: "横向柱状图",
    line: "折线图",
    pie: "环形图",
    scatter: "散点图",
  };

  return labels[type] ?? type;
}

function chartTitle(chart: Chart) {
  const spec = chart.query_spec;
  const category = fieldLabel(String(spec.category ?? ""));
  const metric = fieldLabel(String(spec.metric ?? ""));
  const dateColumn = fieldLabel(String(spec.date_column ?? ""));
  const xAxis = fieldLabel(String(spec.x_axis ?? ""));
  const yAxis = fieldLabel(String(spec.y_axis ?? ""));

  if (chart.chart_type === "pie" && category && metric) {
    return `${metric}按${category}占比`;
  }
  if (
    (chart.chart_type === "bar" || chart.chart_type === "horizontal_bar") &&
    category &&
    metric
  ) {
    return `${metric}按${category}汇总`;
  }
  if (
    (chart.chart_type === "line" || chart.chart_type === "area") &&
    dateColumn &&
    metric
  ) {
    return `${metric}趋势`;
  }
  if (chart.chart_type === "scatter" && xAxis && yAxis) {
    return `${yAxis}与${xAxis}关系`;
  }

  return localizeLegacyTitle(chart.title);
}

function localizeLegacyTitle(title: string) {
  const byMatch = title.match(/^(.+)\s+by\s+(.+)$/i);
  if (byMatch) {
    return `${fieldLabel(byMatch[1])}按${fieldLabel(byMatch[2])}汇总`;
  }

  const overMatch = title.match(/^(.+)\s+over\s+(.+)$/i);
  if (overMatch) {
    return `${fieldLabel(overMatch[1])}趋势`;
  }

  const vsMatch = title.match(/^(.+)\s+vs\s+(.+)$/i);
  if (vsMatch) {
    return `${fieldLabel(vsMatch[1])}与${fieldLabel(vsMatch[2])}关系`;
  }

  return title;
}

function fieldLabel(name: string) {
  const normalized = name.trim().toLowerCase();
  const labels: Record<string, string> = {
    amount: "金额",
    category: "分类",
    channel: "渠道",
    cost: "成本",
    customer: "客户",
    date: "日期",
    margin: "利润率",
    price: "价格",
    product: "产品",
    profit: "利润",
    quantity: "数量",
    region: "区域",
    revenue: "收入",
    sales: "销售额",
    time: "时间",
  };

  return labels[normalized] ?? name.trim();
}

async function requireAccessToken(
  getAccessToken: () => Promise<string | null>,
) {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    throw new Error("请先登录，再使用图表功能。");
  }
  return accessToken;
}
