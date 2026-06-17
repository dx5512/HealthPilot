"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import RiskBadge from "@/components/ui/RiskBadge";
import type { AnalysisResult } from "@/types";

interface RiskResultProps {
  result: AnalysisResult;
}

export default function RiskResult({ result }: RiskResultProps) {
  const scorePercent = (result.risk_score * 100).toFixed(1);

  return (
    <div className="space-y-4">
      {/* 预警提示 */}
      {result.alerts_triggered.length > 0 && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="font-semibold text-red-700">
            ⚠️ 检测到 {result.alerts_triggered.length} 条健康预警，请前往{" "}
            <a href="/alerts" className="underline">预警中心</a> 查看。
          </p>
        </div>
      )}

      {/* 风险等级 */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-4">
          <RiskBadge level={result.risk_level} size="lg" />
          <span className="text-lg text-gray-600">
            风险概率：<span className="font-bold text-gray-900">{scorePercent}%</span>
          </span>
        </div>
      </div>

      {/* 报告 + 引用 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* AI 报告 */}
        <div className="lg:col-span-2 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-3 text-lg font-semibold text-gray-900">📝 AI 健康建议</h3>
          <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {result.health_advice}
            </ReactMarkdown>
          </div>
        </div>

        {/* 参考依据 */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-3 text-lg font-semibold text-gray-900">📚 参考依据</h3>
          {result.guideline_refs.length > 0 ? (
            <ul className="space-y-3">
              {result.guideline_refs.map((ref, i) => (
                <li key={i} className="rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
                  📄 {ref}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-400">暂无参考依据</p>
          )}
        </div>
      </div>
    </div>
  );
}
