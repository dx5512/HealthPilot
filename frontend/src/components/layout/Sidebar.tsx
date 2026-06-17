"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Map,
  MessageCircle,
  Bell,
  FileText,
  Users,
  UserCog,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

const navGroups = [
  {
    label: "监护中心",
    items: [
      { href: "/analysis", label: "健康分析", icon: Activity, adminOnly: false },
      { href: "/community", label: "社区态势", icon: Map, adminOnly: true },
      { href: "/chat", label: "健康问答", icon: MessageCircle, adminOnly: false },
    ],
  },
  {
    label: "管理中心",
    items: [
      { href: "/alerts", label: "预警中心", icon: Bell, adminOnly: true },
      { href: "/records", label: "历史档案", icon: FileText, adminOnly: false },
      { href: "/contacts", label: "关联人管理", icon: Users, adminOnly: false },
      { href: "/users", label: "用户管理", icon: UserCog, adminOnly: true },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r border-gray-200 bg-white">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b border-gray-100 px-5">
        <span className="text-2xl">🏥</span>
        <div>
          <h1 className="text-base font-bold text-gray-900">智域卫康</h1>
          <p className="text-[11px] text-gray-400">社区慢病智能监护</p>
        </div>
      </div>

      {/* 导航 */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {navGroups.map((group) => {
          const visibleItems = group.items.filter(
            (item) => !item.adminOnly || isAdmin
          );
          if (visibleItems.length === 0) return null;
          return (
            <div key={group.label} className="mb-6">
              <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
                {group.label}
              </p>
              <ul className="space-y-1">
                {visibleItems.map((item) => {
                  const isActive = pathname === item.href;
                  const Icon = item.icon;
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                          isActive
                            ? "bg-primary/10 text-primary"
                            : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                        }`}
                      >
                        <Icon size={18} />
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>

      {/* 版本号 */}
      <div className="border-t border-gray-100 px-5 py-3">
        <p className="text-xs text-gray-400">v2.0.0 · 演示版</p>
      </div>
    </aside>
  );
}
