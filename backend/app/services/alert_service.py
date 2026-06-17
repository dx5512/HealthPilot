"""
预警服务 — 体征异常检测 + 频繁提问检测 + 预警管理。
"""
import json
import logging
from datetime import datetime, timedelta
from core.config import (
    SYSTOLIC_CRITICAL, SYSTOLIC_WARNING,
    DIASTOLIC_CRITICAL, DIASTOLIC_WARNING,
    SPO2_CRITICAL, SPO2_WARNING,
    HR_HIGH, HR_LOW,
    CHAT_FREQ_WARNING, CHAT_SAME_TOPIC_CRITICAL,
    EMERGENCY_KEYWORDS,
)
from core.paths import ALERT_HISTORY_PATH, ALERTS_DIR, CHAT_LOGS_DIR
from app.schemas.health import VitalsInput, AlertItem, AlertNotification

logger = logging.getLogger(__name__)


def _mask_phone(phone: str) -> str:
    """手机号脱敏：13800001234 → 138****1234。"""
    if len(phone) >= 11:
        return phone[:3] + "****" + phone[-4:]
    return phone


class AlertService:
    def __init__(self):
        ALERTS_DIR.mkdir(parents=True, exist_ok=True)
        if not ALERT_HISTORY_PATH.exists():
            ALERT_HISTORY_PATH.write_text("[]", encoding="utf-8")

    # ─── 读写 ───

    def _load_alerts(self) -> list[dict]:
        with open(ALERT_HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_alerts(self, alerts: list[dict]):
        # 原子写入：先写临时文件再重命名
        tmp_path = ALERT_HISTORY_PATH.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(alerts, f, ensure_ascii=False, indent=2)
        tmp_path.replace(ALERT_HISTORY_PATH)

    def _generate_alert_id(self, user_id: str) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"alert_{ts}_{user_id}"

    # ─── 创建预警 ───

    def _create_alert(
        self,
        user_id: str,
        alert_type: str,
        level: str,
        title: str,
        message: str,
        details: dict | None = None,
    ) -> str:
        """创建预警记录并通知关联人，返回预警 ID。"""
        alert_id = self._generate_alert_id(user_id)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 获取居民姓名
        resident_name = self._get_resident_name(user_id)

        # 查找关联人并生成通知
        notifications = self._notify_contacts(user_id, resident_name, message, level)

        alert = {
            "id": alert_id,
            "user_id": user_id,
            "resident_name": resident_name,
            "alert_type": alert_type,
            "level": level,
            "title": title,
            "message": message,
            "details": details or {},
            "timestamp": now_str,
            "acknowledged": False,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "notifications": notifications,
        }

        alerts = self._load_alerts()
        alerts.append(alert)
        self._save_alerts(alerts)

        logger.warning("预警已创建: [%s] %s - %s", level, resident_name, title)
        return alert_id

    def _get_resident_name(self, user_id: str) -> str:
        """从社区数据或聊天记录中获取居民姓名。"""
        from core.paths import COMMUNITY_DATA_PATH
        try:
            if COMMUNITY_DATA_PATH.exists():
                with open(COMMUNITY_DATA_PATH, "r", encoding="utf-8") as f:
                    residents = json.load(f)
                for r in residents:
                    if r.get("user_id") == user_id:
                        return r.get("name", user_id)
        except Exception:
            pass
        return user_id

    def _notify_contacts(self, user_id: str, resident_name: str, message: str, level: str) -> list[dict]:
        """查找关联人并生成通知记录。"""
        from app.services.contact_service import ContactService
        contact_service = ContactService()

        contacts_data = contact_service.get_contacts(user_id)
        notifications = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for contact in contacts_data.contacts:
            # 检查免打扰时段
            if self._is_quiet_hours(contact.quiet_hours_start, contact.quiet_hours_end):
                status = "免打扰时段，已跳过"
            else:
                status = "已发送(模拟)"

            notifications.append(AlertNotification(
                contact_name=contact.name,
                relation=contact.relation,
                method=contact.notify_method,
                phone_mask=_mask_phone(contact.phone),
                sent_at=now_str,
                status=status,
            ))

        return notifications

    def _is_quiet_hours(self, start: str | None, end: str | None) -> bool:
        """检查当前时间是否在免打扰时段内。"""
        if not start or not end:
            return False
        try:
            now = datetime.now()
            start_h, start_m = map(int, start.split(":"))
            end_h, end_m = map(int, end.split(":"))
            start_time = now.replace(hour=start_h, minute=start_m, second=0)
            end_time = now.replace(hour=end_h, minute=end_m, second=0)
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:  # 跨午夜
                return now >= start_time or now <= end_time
        except (ValueError, AttributeError):
            return False

    # ─── 体征异常检测 ───

    def check_vitals_alert(self, vitals: VitalsInput, user_id: str) -> list[str]:
        """
        检测体征数据是否触发预警。
        返回触发的预警 ID 列表。
        """
        alert_ids = []

        # 收缩压
        if vitals.systolic >= SYSTOLIC_CRITICAL:
            aid = self._create_alert(
                user_id, "vitals_abnormal", "紧急",
                "收缩压紧急预警",
                f"收缩压达到 {vitals.systolic:.0f}mmHg，超过紧急阈值({SYSTOLIC_CRITICAL:.0f}mmHg)，建议立即关注。",
                {"systolic": vitals.systolic, "threshold": SYSTOLIC_CRITICAL},
            )
            alert_ids.append(aid)
        elif vitals.systolic >= SYSTOLIC_WARNING:
            aid = self._create_alert(
                user_id, "vitals_abnormal", "关注",
                "收缩压偏高预警",
                f"收缩压为 {vitals.systolic:.0f}mmHg，超过关注阈值({SYSTOLIC_WARNING:.0f}mmHg)，请注意监测。",
                {"systolic": vitals.systolic, "threshold": SYSTOLIC_WARNING},
            )
            alert_ids.append(aid)

        # 舒张压
        if vitals.diastolic >= DIASTOLIC_CRITICAL:
            aid = self._create_alert(
                user_id, "vitals_abnormal", "紧急",
                "舒张压紧急预警",
                f"舒张压达到 {vitals.diastolic:.0f}mmHg，超过紧急阈值({DIASTOLIC_CRITICAL:.0f}mmHg)。",
                {"diastolic": vitals.diastolic, "threshold": DIASTOLIC_CRITICAL},
            )
            alert_ids.append(aid)
        elif vitals.diastolic >= DIASTOLIC_WARNING:
            aid = self._create_alert(
                user_id, "vitals_abnormal", "关注",
                "舒张压偏高预警",
                f"舒张压为 {vitals.diastolic:.0f}mmHg，超过关注阈值({DIASTOLIC_WARNING:.0f}mmHg)。",
                {"diastolic": vitals.diastolic, "threshold": DIASTOLIC_WARNING},
            )
            alert_ids.append(aid)

        # 血氧
        if vitals.spo2 < SPO2_CRITICAL:
            aid = self._create_alert(
                user_id, "vitals_abnormal", "紧急",
                "血氧紧急预警",
                f"血氧饱和度降至 {vitals.spo2:.1f}%，低于紧急阈值({SPO2_CRITICAL}%)，建议立即就医。",
                {"spo2": vitals.spo2, "threshold": SPO2_CRITICAL},
            )
            alert_ids.append(aid)
        elif vitals.spo2 < SPO2_WARNING:
            aid = self._create_alert(
                user_id, "vitals_abnormal", "关注",
                "血氧偏低预警",
                f"血氧饱和度为 {vitals.spo2:.1f}%，低于关注阈值({SPO2_WARNING}%)。",
                {"spo2": vitals.spo2, "threshold": SPO2_WARNING},
            )
            alert_ids.append(aid)

        # 心率
        if vitals.heart_rate > HR_HIGH or vitals.heart_rate < HR_LOW:
            aid = self._create_alert(
                user_id, "vitals_abnormal", "关注",
                "心率异常预警",
                f"心率为 {vitals.heart_rate}bpm，超出正常范围({HR_LOW}-{HR_HIGH}bpm)。",
                {"heart_rate": vitals.heart_rate, "normal_range": f"{HR_LOW}-{HR_HIGH}"},
            )
            alert_ids.append(aid)

        return alert_ids

    # ─── 频繁提问检测 ───

    def check_chat_alert(self, user_id: str) -> list[str]:
        """
        检测用户 24 小时内提问频率是否触发预警。
        返回触发的预警 ID 列表。
        """
        alert_ids = []
        log_path = CHAT_LOGS_DIR / f"{user_id}.json"
        if not log_path.exists():
            return alert_ids

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return alert_ids

        now = datetime.now()
        cutoff = now - timedelta(hours=24)

        # 过滤 24h 内的记录
        recent_logs = []
        for entry in logs:
            try:
                ts = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
                if ts >= cutoff:
                    recent_logs.append(entry)
            except (KeyError, ValueError):
                continue

        # 检查总提问次数
        if len(recent_logs) >= CHAT_FREQ_WARNING:
            # 检查是否已存在相同预警（避免重复触发）
            existing = self._load_alerts()
            recent_alerts = [
                a for a in existing
                if a.get("user_id") == user_id
                and a.get("alert_type") == "frequent_chat"
                and not a.get("acknowledged")
                and (now - datetime.strptime(a["timestamp"], "%Y-%m-%d %H:%M:%S")).total_seconds() < 86400
            ]
            if not recent_alerts:
                aid = self._create_alert(
                    user_id, "frequent_chat", "关注",
                    "频繁健康咨询预警",
                    f"该用户 24 小时内咨询了 {len(recent_logs)} 次健康问题，建议关注其身体状况。",
                    {"question_count_24h": len(recent_logs), "threshold": CHAT_FREQ_WARNING},
                )
                alert_ids.append(aid)

        # 检查同类别提问
        topic_counts: dict[str, int] = {}
        for entry in recent_logs:
            for tag in entry.get("topic_tags", []):
                if tag != "其他":
                    topic_counts[tag] = topic_counts.get(tag, 0) + 1

        for topic, count in topic_counts.items():
            if count >= CHAT_SAME_TOPIC_CRITICAL:
                existing = self._load_alerts()
                recent_alerts = [
                    a for a in existing
                    if a.get("user_id") == user_id
                    and a.get("alert_type") == "frequent_chat"
                    and topic in a.get("details", {}).get("topic", "")
                    and not a.get("acknowledged")
                    and (now - datetime.strptime(a["timestamp"], "%Y-%m-%d %H:%M:%S")).total_seconds() < 86400
                ]
                if not recent_alerts:
                    aid = self._create_alert(
                        user_id, "frequent_chat", "紧急",
                        f"频繁{topic}不适预警",
                        f"该用户 24 小时内 {count} 次咨询{topic}相关问题，可能存在健康风险。",
                        {"topic": topic, "count": count, "threshold": CHAT_SAME_TOPIC_CRITICAL},
                    )
                    alert_ids.append(aid)

        return alert_ids

    # ─── 预警查询 ───

    def get_alerts(self, level: str | None = None, status: str | None = None) -> list[AlertItem]:
        """获取预警列表，支持筛选。"""
        alerts = self._load_alerts()

        if level:
            alerts = [a for a in alerts if a.get("level") == level]
        if status == "待处理":
            alerts = [a for a in alerts if not a.get("acknowledged")]
        elif status == "已确认":
            alerts = [a for a in alerts if a.get("acknowledged")]

        # 按时间倒序
        alerts.sort(key=lambda a: a.get("timestamp", ""), reverse=True)
        return [self._to_alert_item(a) for a in alerts]

    def get_alert_by_id(self, alert_id: str) -> AlertItem | None:
        """根据 ID 获取预警详情。"""
        alerts = self._load_alerts()
        for a in alerts:
            if a.get("id") == alert_id:
                return self._to_alert_item(a)
        return None

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "系统管理员") -> bool:
        """确认/处理预警。"""
        alerts = self._load_alerts()
        for a in alerts:
            if a.get("id") == alert_id and not a.get("acknowledged"):
                a["acknowledged"] = True
                a["acknowledged_by"] = acknowledged_by
                a["acknowledged_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save_alerts(alerts)
                logger.info("预警已确认: %s by %s", alert_id, acknowledged_by)
                return True
        return False

    def _to_alert_item(self, data: dict) -> AlertItem:
        """将 dict 转换为 AlertItem schema。"""
        return AlertItem(
            id=data["id"],
            user_id=data["user_id"],
            resident_name=data.get("resident_name", ""),
            alert_type=data["alert_type"],
            level=data["level"],
            title=data["title"],
            message=data["message"],
            details=data.get("details", {}),
            timestamp=data["timestamp"],
            acknowledged=data.get("acknowledged", False),
            acknowledged_by=data.get("acknowledged_by"),
            acknowledged_at=data.get("acknowledged_at"),
            notifications=[AlertNotification(**n) for n in data.get("notifications", [])],
        )
