import Link from "next/link";
import { Activity, BarChart3, Database, LogIn, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DatasetUploadCard } from "@/features/datasets/components/dataset-upload-card";

const metrics = [
  { label: "Datasets", value: "0", icon: Database },
  { label: "Dashboards", value: "0", icon: BarChart3 },
  { label: "Insights", value: "0", icon: Sparkles },
  { label: "Jobs", value: "0", icon: Activity },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#08090a] text-white">
      <section className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 py-6">
        <header className="flex items-center justify-between border-b border-white/10 pb-5">
          <div>
            <p className="text-sm text-zinc-400">AI Data Analysis SaaS</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-normal">
              Analytics Workspace
            </h1>
          </div>
          <div className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-zinc-300">
            STEP 3 auth
          </div>
        </header>

        <div className="grid flex-1 gap-6 py-8 lg:grid-cols-[1.15fr_0.85fr]">
          <section className="rounded-[28px] border border-white/10 bg-[#111317] p-6 shadow-2xl shadow-black/30">
            <div className="flex h-full min-h-[520px] flex-col justify-between">
              <div>
                <p className="text-sm text-zinc-400">MVP flow</p>
                <h2 className="mt-3 max-w-2xl text-4xl font-semibold leading-tight tracking-normal">
                  Upload data, generate charts, ask questions, and save
                  dashboards.
                </h2>
                <div className="mt-8 flex flex-wrap gap-3">
                  <Button asChild>
                    <Link href="/login">
                      <LogIn className="h-4 w-4" aria-hidden="true" />
                      Sign in
                    </Link>
                  </Button>
                  <Button asChild variant="outline">
                    <Link href="/register">Create account</Link>
                  </Button>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  "Upload CSV",
                  "Infer schema",
                  "Recommend charts",
                  "Generate insights",
                ].map((item) => (
                  <div
                    key={item}
                    className="rounded-2xl border border-white/10 bg-white/[0.04] p-4"
                  >
                    <p className="text-sm font-medium text-zinc-100">{item}</p>
                    <div className="mt-4 h-2 rounded-full bg-white/10">
                      <div className="h-2 w-1/3 rounded-full bg-white/70" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

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
