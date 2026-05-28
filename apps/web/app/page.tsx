import { Activity, BarChart3, Database, Sparkles } from "lucide-react";

import { DatasetUploadCard } from "@/features/datasets/components/dataset-upload-card";
import { WorkspaceHero } from "@/features/workspace/components/workspace-hero";

const metrics = [
  { label: "数据集", value: "0", icon: Database },
  { label: "仪表盘", value: "0", icon: BarChart3 },
  { label: "洞察", value: "0", icon: Sparkles },
  { label: "任务", value: "0", icon: Activity },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#08090a] text-white">
      <section className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 py-6">
        <header className="flex items-center justify-between border-b border-white/10 pb-5">
          <div>
            <p className="text-sm text-zinc-400">AI 数据分析</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-normal">
              分析工作台
            </h1>
          </div>
          <div className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-zinc-300">
            STEP 11 AI 智能体
          </div>
        </header>

        <div className="grid flex-1 gap-6 py-8 lg:grid-cols-[1.15fr_0.85fr]">
          <WorkspaceHero />

          <aside className="space-y-4">
            <DatasetUploadCard />
            {metrics.map((metric) => {
              const Icon = metric.icon;
              return (
                <div
                  key={metric.label}
                  className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-zinc-400">{metric.label}</p>
                    <Icon
                      className="h-5 w-5 text-zinc-400"
                      aria-hidden="true"
                    />
                  </div>
                  <p className="mt-5 text-3xl font-semibold tracking-normal">
                    {metric.value}
                  </p>
                </div>
              );
            })}
          </aside>
        </div>
      </section>
    </main>
  );
}
