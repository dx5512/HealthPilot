"use client";

import { useEffect, useState, useCallback } from "react";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import RiskBadge from "@/components/ui/RiskBadge";
import { getAlerts, acknowledgeAlert } from "@/lib/api";
import type { AlertItem } from "@/types";

const levelFilters = ["全部", "紧急", "关注"];
const statusFilters = ["全部", "待处理", "已确认"];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [level, setLevel] = useState("全部");
  const [status, setStatus] = useState("全部");
  const [expanded, setExpanded] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const l = level === "全部" ? undefined : level;
      const s = status === "全部" ? undefined : status;
      setAlerts(await getAlerts(l, s));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [level, status]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleAck = async (id: string) => {
    try {
      await acknowledgeAlert(id);
      fetchAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">🔔 预警中心</h1>
        <p className="mt-1 text-sm text-gray-500">
          体征异常或频繁不适提问时自动触发预警
        </p>
      </div>

      {/* 筛选 */}
      <div className="flex flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">级别：</span>
          {levelFilters.map((f) => (
            <button
              key={f}
              onClick={() => setLevel(f)}
              className={`rounded-full px-3 py-1 text-sm transition-colors ${
                level === f ? "bg-primary text-white" : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">状态：</span>
          {statusFilters.map((f) => (
            <button
              key={f}
              onClick={() => setStatus(f)}
              className={`rounded-full px-3 py-1 text-sm transition-colors ${
                status === f ? "bg-primary text-white" : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : alerts.length === 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-12 text-center text-gray-400">
          <p className="text-4xl mb-2">✅</p>
          <p>暂无预警消息</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`rounded-xl border bg-white p-4 shadow-sm transition-all ${
                alert.level === "紧急" && !alert.acknowledged
                  ? "border-l-4 border-l-red-500"
                  : alert.acknowledged
                  ? "border-l-4 border-l-gray-300 opacity-60"
                  : "border-l-4 border-l-yellow-400"
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <RiskBadge level={alert.level === "紧急" ? "高危" : "中风险"} size="sm" />
                    <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                    {alert.acknowledged && (
                      <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">已处理</span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-gray-600">{alert.message}</p>
                  <p className="mt-1 text-xs text-gray-400">
                    {alert.resident_name} · {alert.timestamp}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setExpanded(expanded === alert.id ? null : alert.id)}
                    className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50"
                  >
                    详情
                  </button>
                  {!alert.acknowledged && (
                    <button
                      onClick={() => handleAck(alert.id)}
                      className="rounded-lg bg-primary px-3 py-1.5 text-xs text-white hover:bg-primary-dark"
                    >
                      确认处理
                    </button>
                  )}
                </div>
              </div>

              {/* 展开详情 */}
              {expanded === alert.id && (
                <div className="mt-3 rounded-lg bg-gray-50 p-3 text-sm">
                  {alert.notifications.length > 0 && (
                    <div>
                      <p className="mb-2 font-medium text-gray-700">通知记录：</p>
                      {alert.notifications.map((n, i) => (
                        <p key={i} className="text-gray-600">
                          📱 {n.contact_name}（{n.relation}）- {n.phone_mask} - {n.status}
                        </p>
                      ))}
                    </div>
                  )}
                  {alert.notifications.length === 0 && (
                    <p className="text-gray-400">暂无关联人通知</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
