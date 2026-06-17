/** 健康分析 */
export interface VitalsInput {
  user_id: string;
  systolic: number;
  diastolic: number;
  heart_rate: number;
  spo2: number;
  height: number;
  weight: number;
  age: number;
}

export interface AnalysisResult {
  status: string;
  timestamp: string;
  risk_level: string;
  risk_score: number;
  health_advice: string;
  guideline_refs: string[];
  alerts_triggered: string[];
}

/** 社区数据 */
export interface Resident {
  user_id: string;
  name: string;
  lat: number;
  lng: number;
  status: string;
  last_update: string;
  systolic: number;
  diastolic: number;
  is_current_user: boolean;
}

export interface CommunityStats {
  total: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
}

/** 报告 */
export interface ReportSummary {
  id: string;
  user_id: string;
  timestamp: string;
  risk_level: string;
}

export interface ReportDetail extends ReportSummary {
  ai_report: string;
  rag_references: string[];
  vitals: Record<string, number>;
  risk_score: number;
}

/** 问答 */
export interface ChatMessage {
  timestamp: string;
  question: string;
  answer: string;
  topic_tags: string[];
}

export interface ChatResponse {
  answer: string;
  timestamp: string;
  topic_tags: string[];
  alert_triggered: boolean;
  alert_ids: string[];
}

/** 预警 */
export interface AlertNotification {
  contact_name: string;
  relation: string;
  method: string;
  phone_mask: string;
  sent_at: string;
  status: string;
}

export interface AlertItem {
  id: string;
  user_id: string;
  resident_name: string;
  alert_type: string;
  level: string;
  title: string;
  message: string;
  details: Record<string, unknown>;
  timestamp: string;
  acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  notifications: AlertNotification[];
}

/** 关联人 */
export interface ContactInfo {
  id: string;
  name: string;
  relation: string;
  phone: string;
  notify_method: string;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
}

export interface ResidentContacts {
  user_id: string;
  resident_name: string;
  contacts: ContactInfo[];
}

/** 认证 */
export interface User {
  user_id: string;
  username: string;
  name: string;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}
