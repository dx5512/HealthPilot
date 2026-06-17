"""
Pydantic v2 Schema 定义 — 请求/响应模型。
所有模型使用 Pydantic v2 语法（model_config、ConfigDict）。
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ────────────────────────────────────────
# 1. 健康分析
# ────────────────────────────────────────

class VitalsInput(BaseModel):
    """体征数据输入（来自前端表单或 ESP32 设备）。"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "user_id": "u_007",
            "systolic": 145,
            "diastolic": 95,
            "heart_rate": 88,
            "spo2": 96.5,
            "height": 170.0,
            "weight": 80.0,
            "age": 68,
        }
    })

    user_id: str = Field(..., description="用户ID或设备ID")
    systolic: float = Field(..., ge=0, le=300, description="收缩压 (mmHg)")
    diastolic: float = Field(..., ge=0, le=200, description="舒张压 (mmHg)")
    heart_rate: int = Field(..., ge=0, le=300, description="心率 (bpm)")
    spo2: float = Field(..., ge=0, le=100, description="血氧饱和度 (%)")
    height: float = Field(..., ge=0, le=300, description="身高 (cm)")
    weight: float = Field(..., ge=0, le=500, description="体重 (kg)")
    age: int = Field(..., ge=0, le=150, description="年龄")


class AnalysisResult(BaseModel):
    """健康分析结果响应。"""
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.now, description="分析时间")
    risk_level: str = Field(..., description="风险等级：低风险/中风险/高危")
    risk_score: float = Field(..., description="风险概率值 (0-1)")
    health_advice: str = Field(..., description="AI生成的健康建议")
    guideline_refs: list[str] = Field(default_factory=list, description="参考的国家指南条款")
    alerts_triggered: list[str] = Field(default_factory=list, description="触发的预警ID列表")


# ────────────────────────────────────────
# 2. 社区数据
# ────────────────────────────────────────

class Resident(BaseModel):
    """社区居民数据点（地图展示用）。"""
    user_id: str
    name: str
    lat: float
    lng: float
    status: str  # 低风险/中风险/高危
    last_update: str
    systolic: float = 0
    diastolic: float = 0
    is_current_user: bool = False


class CommunityStats(BaseModel):
    """社区统计汇总。"""
    total: int
    high_risk: int
    medium_risk: int
    low_risk: int


# ────────────────────────────────────────
# 3. 报告
# ────────────────────────────────────────

class ReportSummary(BaseModel):
    """报告列表项（摘要）。"""
    id: str = Field(..., description="报告ID（文件名去掉扩展名）")
    user_id: str
    timestamp: str
    risk_level: str


class ReportDetail(ReportSummary):
    """报告详情（完整内容）。"""
    ai_report: str = ""
    rag_references: list[str] = Field(default_factory=list)
    vitals: dict = Field(default_factory=dict)
    risk_score: float = 0.0


# ────────────────────────────────────────
# 4. 健康问答
# ────────────────────────────────────────

class ChatRequest(BaseModel):
    """用户健康问题。"""
    user_id: str = Field(..., description="提问用户ID")
    question: str = Field(..., min_length=1, max_length=500, description="健康问题")


class ChatMessage(BaseModel):
    """单条聊天记录。"""
    timestamp: str
    question: str
    answer: str
    topic_tags: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """AI 回答响应。"""
    answer: str
    timestamp: str
    topic_tags: list[str] = Field(default_factory=list)
    alert_triggered: bool = False
    alert_ids: list[str] = Field(default_factory=list)


# ────────────────────────────────────────
# 5. 预警
# ────────────────────────────────────────

class AlertNotification(BaseModel):
    """预警通知记录。"""
    contact_name: str
    relation: str
    method: str
    phone_mask: str
    sent_at: str
    status: str


class AlertItem(BaseModel):
    """预警消息。"""
    id: str
    user_id: str
    resident_name: str
    alert_type: str  # vitals_abnormal / frequent_chat / emergency_keyword
    level: str       # 紧急 / 关注
    title: str
    message: str
    details: dict = Field(default_factory=dict)
    timestamp: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    notifications: list[AlertNotification] = Field(default_factory=list)


# ────────────────────────────────────────
# 6. 关联人管理
# ────────────────────────────────────────

class ContactInfo(BaseModel):
    """关联人信息。"""
    id: str = Field(..., description="关联人ID")
    name: str = Field(..., description="姓名")
    relation: str = Field(..., description="与老人的关系")
    phone: str = Field(..., description="手机号")
    notify_method: str = Field(default="sms", description="通知方式: sms/wechat/inapp")
    quiet_hours_start: Optional[str] = Field(default=None, description="免打扰开始时间 HH:MM")
    quiet_hours_end: Optional[str] = Field(default=None, description="免打扰结束时间 HH:MM")


class ContactCreate(BaseModel):
    """创建关联人请求。"""
    name: str
    relation: str
    phone: str
    notify_method: str = "sms"
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class ResidentContacts(BaseModel):
    """某居民的关联人列表。"""
    user_id: str
    resident_name: str
    contacts: list[ContactInfo] = Field(default_factory=list)


# ────────────────────────────────────────
# 7. 认证 & 用户
# ────────────────────────────────────────

class LoginRequest(BaseModel):
    """登录请求。"""
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class LoginResponse(BaseModel):
    """登录成功响应。"""
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    """用户信息（不含密码）。"""
    user_id: str
    username: str
    name: str
    role: str  # user / admin
    is_active: bool
    created_at: str


class UserCreate(BaseModel):
    """新增用户请求（管理员）。"""
    username: str = Field(..., min_length=2, max_length=20)
    password: str = Field(..., min_length=4)
    name: str = Field(..., min_length=1)
    role: str = Field(default="user", pattern="^(user|admin)$")


class TokenData(BaseModel):
    """JWT Token 解码数据。"""
    user_id: str
    username: str
    role: str
