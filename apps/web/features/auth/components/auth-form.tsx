"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { bootstrapCurrentUser } from "@/features/auth/auth-api";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

type AuthMode = "login" | "register";

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const supabase = getSupabaseBrowserClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isRegister = mode === "register";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!supabase) {
      toast.error("Supabase 环境变量尚未配置。");
      return;
    }

    setIsSubmitting(true);
    try {
      if (isRegister) {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: `${window.location.origin}/auth/callback`,
          },
        });

        if (error) {
          throw error;
        }

        if (data.session?.access_token) {
          await tryBootstrap(data.session.access_token);
          toast.success("账号创建成功。");
          router.push("/");
        } else {
          toast.success("请打开邮箱完成账号确认。");
        }
        return;
      }

      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        throw error;
      }

      if (data.session?.access_token) {
        await tryBootstrap(data.session.access_token);
      }

      toast.success("登录成功。");
      router.push("/");
      router.refresh();
    } catch (error) {
      const message = error instanceof Error ? error.message : "认证失败。";
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function tryBootstrap(accessToken: string) {
    try {
      await bootstrapCurrentUser(accessToken);
    } catch {
      toast.warning("已登录，但工作区初始化仍在等待 API 数据库可用。");
    }
  }

  return (
    <div className="w-full max-w-md rounded-[28px] border border-white/10 bg-[#111317] p-6 shadow-2xl shadow-black/30">
      <div>
        <p className="text-sm text-zinc-400">AI 数据分析</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-normal">
          {isRegister ? "创建账号" : "登录"}
        </h1>
      </div>

      {!supabase ? (
        <div className="mt-6 rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4 text-sm text-amber-100">
          使用认证前，请先配置 `NEXT_PUBLIC_SUPABASE_URL` 和
          `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`。
        </div>
      ) : null}

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <label className="block space-y-2">
          <span className="text-sm text-zinc-300">邮箱</span>
          <input
            className="h-11 w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 text-sm text-white outline-none transition focus:border-white/30"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label className="block space-y-2">
          <span className="text-sm text-zinc-300">密码</span>
          <input
            className="h-11 w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 text-sm text-white outline-none transition focus:border-white/30"
            type="password"
            autoComplete={isRegister ? "new-password" : "current-password"}
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        <Button
          className="w-full"
          disabled={isSubmitting || !supabase}
          type="submit"
        >
          {isSubmitting ? "处理中..." : isRegister ? "创建账号" : "登录"}
        </Button>
      </form>

      <p className="mt-5 text-sm text-zinc-400">
        {isRegister ? "已经有账号了？" : "还没有账号？"}{" "}
        <Link
          className="text-white underline-offset-4 hover:underline"
          href={isRegister ? "/login" : "/register"}
        >
          {isRegister ? "登录" : "创建账号"}
        </Link>
      </p>
    </div>
  );
}
