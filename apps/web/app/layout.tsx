import type { Metadata } from "next";
import { AppProviders } from "@/components/providers/app-providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 数据分析",
  description: "生产级 AI 数据分析 SaaS 平台。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning translate="no">
      <body translate="no">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
