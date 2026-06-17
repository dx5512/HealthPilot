import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 公开页面直接放行
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    // 已登录访问 /login → 跳转首页
    const token = request.cookies.get("auth_token")?.value;
    if (token && pathname === "/login") {
      return NextResponse.redirect(new URL("/analysis", request.url));
    }
    return NextResponse.next();
  }

  // 未登录 → 跳转登录页
  const token = request.cookies.get("auth_token")?.value;
  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
