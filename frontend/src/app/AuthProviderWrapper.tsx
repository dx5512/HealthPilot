"use client";

import { usePathname } from "next/navigation";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import Sidebar from "@/components/layout/Sidebar";
import UserMenu from "@/components/layout/UserMenu";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

function LayoutInner({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner text="加载中..." />
      </div>
    );
  }

  // 登录页：不渲染侧边栏
  if (isLoginPage || !user) {
    return <>{children}</>;
  }

  // 已登录：渲染侧边栏 + 顶栏用户信息
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="ml-60 flex-1">
        <header className="sticky top-0 z-30 flex items-center justify-end border-b border-gray-200 bg-white/80 px-6 py-3 backdrop-blur">
          <UserMenu />
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}

export function AuthProviderWrapper({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <LayoutInner>{children}</LayoutInner>
    </AuthProvider>
  );
}
