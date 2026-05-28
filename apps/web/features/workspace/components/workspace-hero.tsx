"use client";

import Link from "next/link";
import { CheckCircle2, LogIn } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-provider";

export function WorkspaceHero() {
  const { session } = useAuth();

  return (
    <section className="rounded-[28px] border border-white/10 bg-[#111317] p-6 shadow-2xl shadow-black/30">
      <div className="flex h-full min-h-[520px] flex-col justify-between">
        <div>
          <p className="text-sm text-zinc-400">MVP 流程</p>
          <h2 className="mt-3 max-w-2xl text-4xl font-semibold leading-tight tracking-normal">
            上传数据，生成图表，向 AI 提问，并保存仪表盘。
          </h2>
          <div className="mt-8 flex flex-wrap gap-3">
            {session ? (
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm text-emerald-100">
                <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                已登录，可以上传数据
              </div>
            ) : (
              <>
                <Button asChild>
                  <Link href="/login">
                    <LogIn className="h-4 w-4" aria-hidden="true" />
                    登录
                  </Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="/register">创建账号</Link>
                </Button>
              </>
            )}
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {["上传 CSV", "识别字段", "推荐图表", "生成洞察"].map((item) => (
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
  );
}
