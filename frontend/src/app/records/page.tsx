"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import RiskBadge from "@/components/ui/RiskBadge";
import { getReports, getReportDetail } from "@/lib/api";
import type { ReportSummary, ReportDetail } from "@/types";

export default function RecordsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<ReportDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    getReports()
      .then(setReports)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = async (id: string) => {
    setDetailLoading(true);
    try {
      const detail = await getReportDetail(id);
      setSelected(detail);
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">📚 历史病例档案库</h1>
        <p className="mt-1 text-sm text-gray-500">所有 AI 生成的诊断记录均可追溯</p>
      </div>

      {reports.length === 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-12 text-center text-gray-400">
          <p className="text-4xl mb-2">📭</p>
          <p>暂无历史记录，请先进行健康分析</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
          {/* 报告列表 */}
          <div className="lg:col-span-2 space-y-2">
            <p className="text-sm text-gray-500">共 {reports.length} 份记录</p>
            {reports.map((r) => (
              <button
                key={r.id}
                onClick={() => handleSelect(r.id)}
                className={`w-full rounded-lg border p-3 text-left transition-colors ${
                  selected?.id === r.id
                    ? "border-primary bg-primary/5"
                    : "border-gray-200 bg-white hover:bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">{r.user_id}</span>
                  <RiskBadge level={r.risk_level} size="sm" />
                </div>
                <p className="mt-1 text-xs text-gray-400">{r.timestamp}</p>
              </button>
            ))}
          </div>

          {/* 报告详情 */}
          <div className="lg:col-span-3">
            {detailLoading ? (
              <LoadingSpinner text="加载报告..." />
            ) : selected ? (
              <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">
                    📄 {selected.user_id} 的健康报告
                  </h2>
                  <RiskBadge level={selected.risk_level} />
                </div>
                <p className="mb-4 text-sm text-gray-400">{selected.timestamp}</p>
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {selected.ai_report}
                  </ReactMarkdown>
                </div>
                {selected.rag_references.length > 0 && (
                  <div className="mt-4 border-t pt-4">
                    <p className="mb-2 text-sm font-medium text-gray-700">参考指南：</p>
                    {selected.rag_references.map((ref, i) => (
                      <p key={i} className="text-xs text-gray-500">📄 {ref}</p>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-gray-300 text-gray-400">
                ← 选择一份报告查看详情
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
