import type {
  VitalsInput,
  AnalysisResult,
  Resident,
  CommunityStats,
  ChatResponse,
  ChatMessage,
  AlertItem,
  ReportSummary,
  ReportDetail,
  ResidentContacts,
  ContactInfo,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

function getToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.split("; ").find((c) => c.startsWith("auth_token="));
  return match ? match.split("=")[1] : null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { headers, ...options });

  // 401 → 跳转登录
  if (res.status === 401) {
    document.cookie = "auth_token=; path=/; max-age=0";
    window.location.href = "/login";
    throw new ApiError(401, "登录已过期");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail || "请求失败");
  }
  return res.json();
}

// ─── 健康分析 ───

export async function analyzeRisk(data: VitalsInput): Promise<AnalysisResult> {
  return request<AnalysisResult>("/analyze/risk", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ─── 社区数据 ───

export async function getCommunityResidents(riskLevel?: string): Promise<Resident[]> {
  const params = riskLevel ? `?risk_level=${encodeURIComponent(riskLevel)}` : "";
  return request<Resident[]>(`/community/residents${params}`);
}

export async function getCommunityStats(): Promise<CommunityStats> {
  return request<CommunityStats>("/community/stats");
}

// ─── 健康问答 ───

export async function sendChat(userId: string, question: string): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, question }),
  });
}

export async function getChatHistory(userId: string): Promise<ChatMessage[]> {
  return request<ChatMessage[]>(`/chat/history/${encodeURIComponent(userId)}`);
}

// ─── 预警 ───

export async function getAlerts(level?: string, status?: string): Promise<AlertItem[]> {
  const params = new URLSearchParams();
  if (level) params.set("level", level);
  if (status) params.set("status", status);
  const qs = params.toString();
  return request<AlertItem[]>(`/alerts${qs ? `?${qs}` : ""}`);
}

export async function acknowledgeAlert(alertId: string): Promise<void> {
  await request(`/alerts/${encodeURIComponent(alertId)}/acknowledge`, { method: "POST" });
}

// ─── 报告 ───

export async function getReports(): Promise<ReportSummary[]> {
  return request<ReportSummary[]>("/reports");
}

export async function getReportDetail(reportId: string): Promise<ReportDetail> {
  return request<ReportDetail>(`/reports/${encodeURIComponent(reportId)}`);
}

// ─── 关联人 ───

export async function getContacts(userId: string): Promise<ResidentContacts> {
  return request<ResidentContacts>(`/contacts/${encodeURIComponent(userId)}`);
}

export async function addContact(userId: string, contact: Omit<ContactInfo, "id">): Promise<ContactInfo> {
  return request<ContactInfo>(`/contacts/${encodeURIComponent(userId)}`, {
    method: "POST",
    body: JSON.stringify(contact),
  });
}

export async function updateContact(userId: string, contactId: string, contact: Omit<ContactInfo, "id">): Promise<ContactInfo> {
  return request<ContactInfo>(`/contacts/${encodeURIComponent(userId)}/${encodeURIComponent(contactId)}`, {
    method: "PUT",
    body: JSON.stringify(contact),
  });
}

export async function deleteContact(userId: string, contactId: string): Promise<void> {
  await request(`/contacts/${encodeURIComponent(userId)}/${encodeURIComponent(contactId)}`, { method: "DELETE" });
}
