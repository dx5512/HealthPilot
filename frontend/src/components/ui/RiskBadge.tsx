"use client";

interface RiskBadgeProps {
  level: string;
  size?: "sm" | "md" | "lg";
}

export default function RiskBadge({ level, size = "md" }: RiskBadgeProps) {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-3 py-1 text-sm",
    lg: "px-4 py-1.5 text-base",
  };

  let colorClass = "bg-green-100 text-green-700 border-green-300";
  let icon = "🟢";
  if (level === "高危") {
    colorClass = "bg-red-100 text-red-700 border-red-300";
    icon = "🔴";
  } else if (level === "中风险") {
    colorClass = "bg-yellow-100 text-yellow-700 border-yellow-300";
    icon = "🟡";
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-medium ${colorClass} ${sizeClasses[size]}`}
    >
      <span>{icon}</span>
      {level}
    </span>
  );
}
