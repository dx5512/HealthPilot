"use client";

import type { CommunityStats } from "@/types";

interface StatsBarProps {
  stats: CommunityStats;
}

export default function StatsBar({ stats }: StatsBarProps) {
  const cards = [
    { label: "监测总人数", value: stats.total, color: "text-gray-900", bg: "bg-gray-50" },
    { label: "高危人数", value: stats.high_risk, color: "text-red-600", bg: "bg-red-50" },
    { label: "关注人数", value: stats.medium_risk, color: "text-yellow-600", bg: "bg-yellow-50" },
    { label: "健康人数", value: stats.low_risk, color: "text-green-600", bg: "bg-green-50" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`rounded-xl ${card.bg} border border-gray-100 p-4 text-center`}
        >
          <p className="text-sm text-gray-500">{card.label}</p>
          <p className={`mt-1 text-2xl font-bold ${card.color}`}>{card.value}</p>
        </div>
      ))}
    </div>
  );
}
