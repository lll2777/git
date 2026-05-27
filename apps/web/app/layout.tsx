import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Analytics",
  description: "Production-grade AI data analysis SaaS platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
