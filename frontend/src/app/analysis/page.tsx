"use client";

import { useState } from "react";
import VitalsForm from "@/components/analysis/VitalsForm";
import RiskResult from "@/components/analysis/RiskResult";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { analyzeRisk } from "@/lib/api";
import type { VitalsInput, AnalysisResult } from "@/types";

export default function AnalysisPage() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: VitalsInput) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await analyzeRisk(data);
      setResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "分析失败，请稍后重试";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">🏥 健康风险分析</h1>
        <p className="mt-1 text-sm text-gray-500">
          基于 XGBoost + RAG + LLM 的全流程智能诊断
        </p>
      </div>

      <VitalsForm onSubmit={handleSubmit} loading={loading} />

      {loading && <LoadingSpinner text="正在进行风险计算与智能分析..." />}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          ❌ {error}
        </div>
      )}

      {result && <RiskResult result={result} />}
    </div>
  );
}
