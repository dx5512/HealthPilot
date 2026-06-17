"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import StatsBar from "@/components/community/StatsBar";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { getCommunityResidents, getCommunityStats } from "@/lib/api";
import type { Resident, CommunityStats } from "@/types";

const HealthMap = dynamic(() => import("@/components/community/HealthMap"), {
  ssr: false,
  loading: () => <LoadingSpinner text="加载地图中..." />,
});

const filters = ["全部", "高危", "中风险", "低风险"];

export default function CommunityPage() {
  const [residents, setResidents] = useState<Resident[]>([]);
  const [stats, setStats] = useState<CommunityStats | null>(null);
  const [filter, setFilter] = useState("全部");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCommunityResidents(), getCommunityStats()])
      .then(([r, s]) => {
        setResidents(r);
        setStats(s);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner text="加载社区数据..." />;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">🗺️ 社区慢病风险态势感知</h1>
        <p className="mt-1 text-sm text-gray-500">
          青岛市西海岸新区三沙路街道 · 实时健康风险分布
        </p>
      </div>

      {stats && <StatsBar stats={stats} />}

      {/* 筛选按钮 */}
      <div className="flex gap-2">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              filter === f
                ? "bg-primary text-white"
                : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <HealthMap residents={residents} filter={filter} />

      <p className="text-xs text-gray-400">
        💡 点击地图标记查看居民详情 · 热力图颜色越红代表风险越密集
      </p>
    </div>
  );
}
