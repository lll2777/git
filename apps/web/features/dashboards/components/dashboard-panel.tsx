"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LayoutDashboard, Loader2, Save } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";
import {
  type DashboardSummary,
  listDashboards,
  saveDashboard,
} from "@/features/datasets/dataset-api";

type DashboardPanelProps = {
  datasetId: string | undefined;
  datasetName: string | undefined;
};

export function DashboardPanel({
  datasetId,
  datasetName,
}: DashboardPanelProps) {
  const queryClient = useQueryClient();
  const { session } = useAuth();
  const [title, setTitle] = useState("");
  const accessToken = session?.access_token ?? "";

  const defaultTitle = useMemo(
    () => `${datasetName ?? "Dataset"} dashboard`,
    [datasetName],
  );

  const dashboardsQuery = useQuery({
    queryKey: ["dataset-dashboards", datasetId, accessToken],
    queryFn: () =>
      listDashboards({
        accessToken,
        datasetId: datasetId ?? "",
      }),
    enabled: Boolean(accessToken && datasetId),
  });

  const saveMutation = useMutation({
    mutationFn: () =>
      saveDashboard({
        accessToken,
        datasetId: datasetId ?? "",
        title: title.trim() || defaultTitle,
      }),
    onSuccess: async () => {
      toast.success("Dashboard saved.");
      setTitle("");
      await queryClient.invalidateQueries({
        queryKey: ["dataset-dashboards", datasetId],
      });
    },
    onError: (error) => {
      toast.error(
        error instanceof Error ? error.message : "Dashboard save failed.",
      );
    },
  });

  if (!datasetId) {
    return null;
  }

  const dashboards = dashboardsQuery.data?.dashboards ?? [];
  const isBusy = dashboardsQuery.isLoading || saveMutation.isPending;

  return (
    <section className="mt-6 border-t border-white/10 pt-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-zinc-100">Dashboards</p>
          <p className="mt-1 text-xs text-zinc-500">
            Save chart and insight outputs as reusable dashboard snapshots.
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-3">
          <LayoutDashboard
            className="h-5 w-5 text-zinc-300"
            aria-hidden="true"
          />
        </div>
      </div>

      <div className="mt-4 rounded-3xl border border-white/10 bg-white/[0.03] p-4">
        <label className="text-xs font-medium uppercase tracking-wide text-zinc-500">
          Dashboard title
        </label>
        <input
          className="mt-2 h-11 w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-white/25"
          maxLength={160}
          onChange={(event) => setTitle(event.target.value)}
          placeholder={defaultTitle}
          value={title}
        />
        <Button
          className="mt-3 w-full"
          disabled={saveMutation.isPending}
          onClick={() => saveMutation.mutate()}
          type="button"
        >
          {saveMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Save className="h-4 w-4" aria-hidden="true" />
          )}
          Save dashboard
        </Button>
      </div>

      {isBusy ? (
        <div className="mt-4 space-y-2">
          <div className="h-16 rounded-3xl bg-white/[0.04]" />
          <div className="h-16 rounded-3xl bg-white/[0.04]" />
        </div>
      ) : dashboards.length ? (
        <div className="mt-4 space-y-2">
          {dashboards.slice(0, 4).map((dashboard) => (
            <DashboardRow dashboard={dashboard} key={dashboard.id} />
          ))}
        </div>
      ) : (
        <div className="mt-4 flex min-h-36 flex-col items-center justify-center rounded-3xl border border-dashed border-white/15 bg-white/[0.03] px-4 text-center">
          <LayoutDashboard
            className="h-6 w-6 text-zinc-400"
            aria-hidden="true"
          />
          <p className="mt-3 text-sm font-medium text-zinc-200">
            No dashboards saved yet.
          </p>
          <p className="mt-1 text-xs text-zinc-500">
            Save a dashboard after charts or insights are generated.
          </p>
        </div>
      )}
    </section>
  );
}

function DashboardRow({ dashboard }: { dashboard: DashboardSummary }) {
  return (
    <article className="rounded-3xl border border-white/10 bg-white/[0.03] px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-sm font-medium text-zinc-100">
            {dashboard.title}
          </h3>
          <p className="mt-1 text-xs text-zinc-500">
            {dashboard.chart_count} charts, {dashboard.insight_count} insights
          </p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-zinc-500">
          {dashboard.status}
        </span>
      </div>
    </article>
  );
}
