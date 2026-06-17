"""
健康问答服务 — 为老年居民提供口语化健康咨询。
使用 openai 原生 SDK 调用 LLM。
"""
import json
import logging
from datetime import datetime
from openai import OpenAI
from core.config import OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL_NAME, EMERGENCY_KEYWORDS
from core.paths import CHAT_LOGS_DIR, REPORTS_DIR
from app.schemas.health import ChatMessage, ChatResponse

logger = logging.getLogger(__name__)

# 话题分类关键词
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "消化系统": ["肚子", "胃", "消化", "腹泻", "便秘", "恶心", "呕吐", "腹痛", "胀气"],
    "心血管": ["心脏", "胸闷", "心慌", "头晕", "血压", "心悸", "心跳"],
    "呼吸系统": ["咳嗽", "呼吸", "气喘", "痰", "喘"],
    "疼痛类": ["头疼", "头痛", "腰疼", "关节疼", "全身疼", "背痛", "腿疼", "肩膀疼"],
    "睡眠": ["失眠", "睡不着", "多梦", "嗜睡"],
}


def classify_topic(question: str) -> list[str]:
    """基于关键词匹配对问题进行话题分类。"""
    tags = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in question:
                tags.append(topic)
                break
    return tags if tags else ["其他"]


def has_emergency_keyword(question: str) -> bool:
    """检查问题中是否包含急症关键词。"""
    return any(kw in question for kw in EMERGENCY_KEYWORDS)


SYSTEM_PROMPT = """你是[智域卫康]社区健康助手，专门为老年居民提供健康咨询。

回答要求：
1. 用简洁口语化的中文，像和老人聊天一样
2. 避免专业术语，用老人能听懂的话解释
3. 每次回答末尾加一句关怀语（如：记得按时吃药哦）
4. 如果问题涉及急症（剧烈胸痛、呼吸困难、突然晕倒、大量出血、意识模糊），必须在开头用醒目标记并建议立即就医
5. 回答控制在 200 字以内"""


class HealthChatService:
    def __init__(self):
        CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
        return self._client

    def _get_user_vitals(self, user_id: str) -> dict | None:
        """从最近的报告中读取用户体征数据。"""
        try:
            if not REPORTS_DIR.exists():
                return None
            user_reports = sorted(
                [f for f in REPORTS_DIR.iterdir() if f.suffix == ".json" and f.stem.startswith(user_id)],
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            if not user_reports:
                return None
            with open(user_reports[0], "r", encoding="utf-8") as f:
                return json.load(f).get("vitals")
        except Exception:
            return None

    def _load_chat_log(self, user_id: str) -> list[dict]:
        log_path = CHAT_LOGS_DIR / f"{user_id}.json"
        if not log_path.exists():
            return []
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_chat_log(self, user_id: str, log: list[dict]):
        log_path = CHAT_LOGS_DIR / f"{user_id}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    async def chat(self, user_id: str, question: str) -> ChatResponse:
        """处理用户健康问题：LLM 回答 + 记录日志 + 预警检测。"""
        topic_tags = classify_topic(question)
        is_emergency = has_emergency_keyword(question)

        # 构建用户消息（注入体征数据）
        vitals = self._get_user_vitals(user_id)
        user_msg = question
        if vitals:
            user_msg = (
                f"[用户最近体征：收缩压{vitals.get('systolic', '?')}mmHg, "
                f"舒张压{vitals.get('diastolic', '?')}mmHg, "
                f"血氧{vitals.get('spo2', '?')}%, 心率{vitals.get('heart_rate', '?')}bpm]\n\n"
                f"{question}"
            )

        logger.info("健康问答: user=%s, topic=%s, emergency=%s", user_id, topic_tags, is_emergency)

        client = self._get_client()
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        answer = response.choices[0].message.content

        # 记录聊天日志
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat_log = self._load_chat_log(user_id)
        chat_log.append({
            "timestamp": now_str,
            "question": question,
            "answer": answer,
            "topic_tags": topic_tags,
        })
        self._save_chat_log(user_id, chat_log)

        # 预警检测
        from app.services.alert_service import AlertService
        alert_service = AlertService()
        alert_ids = alert_service.check_chat_alert(user_id)

        return ChatResponse(
            answer=answer,
            timestamp=now_str,
            topic_tags=topic_tags,
            alert_triggered=len(alert_ids) > 0,
            alert_ids=alert_ids,
        )

    def get_history(self, user_id: str) -> list[ChatMessage]:
        """获取用户聊天历史。"""
        log = self._load_chat_log(user_id)
        return [
            ChatMessage(
                timestamp=entry["timestamp"],
                question=entry["question"],
                answer=entry["answer"],
                topic_tags=entry.get("topic_tags", []),
            )
            for entry in log
        ]
