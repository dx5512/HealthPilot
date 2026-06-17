"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import type { User } from "@/types";

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  loading: true,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 从 cookie 恢复登录态
    const saved = document.cookie
      .split("; ")
      .find((c) => c.startsWith("auth_token="));
    if (saved) {
      const t = saved.split("=")[1];
      setToken(t);
      // 验证 token 并获取用户信息
      fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/auth/me`, {
        headers: { Authorization: `Bearer ${t}` },
      })
        .then((res) => {
          if (res.ok) return res.json();
          throw new Error("token invalid");
        })
        .then((u: User) => setUser(u))
        .catch(() => {
          document.cookie = "auth_token=; path=/; max-age=0";
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback((newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    document.cookie = `auth_token=${newToken}; path=/; max-age=${24 * 60 * 60}`;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    document.cookie = "auth_token=; path=/; max-age=0";
    window.location.href = "/login";
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
