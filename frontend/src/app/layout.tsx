import type { Metadata } from "next";
import { AuthProviderWrapper } from "./AuthProviderWrapper";
import "./globals.css";

export const metadata: Metadata = {
  title: "智域卫康 — 社区慢病智能监护",
  description: "基于 XGBoost + RAG + LLM 的社区健康监护系统",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 text-gray-900">
        <AuthProviderWrapper>{children}</AuthProviderWrapper>
      </body>
    </html>
  );
}
