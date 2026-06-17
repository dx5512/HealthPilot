"""
关联人管理服务 — CRUD 操作，数据存储在 JSON 文件。
"""
import json
import logging
from core.paths import CONTACTS_PATH
from app.schemas.health import ContactInfo, ContactCreate, ResidentContacts

logger = logging.getLogger(__name__)


class ContactService:
    def __init__(self):
        CONTACTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not CONTACTS_PATH.exists():
            CONTACTS_PATH.write_text("{}", encoding="utf-8")

    def _load_data(self) -> dict:
        with open(CONTACTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_data(self, data: dict):
        tmp_path = CONTACTS_PATH.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_path.replace(CONTACTS_PATH)

    def _generate_contact_id(self, existing_contacts: list[dict]) -> str:
        """生成递增的关联人 ID。"""
        max_num = 0
        for c in existing_contacts:
            try:
                num = int(c["id"].lstrip("c"))
                max_num = max(max_num, num)
            except (ValueError, KeyError):
                pass
        return f"c{max_num + 1:03d}"

    def get_contacts(self, user_id: str) -> ResidentContacts:
        """获取指定居民的关联人列表。"""
        data = self._load_data()
        user_data = data.get(user_id, {})
        contacts = [
            ContactInfo(**c) for c in user_data.get("contacts", [])
        ]
        return ResidentContacts(
            user_id=user_id,
            resident_name=user_data.get("resident_name", user_id),
            contacts=contacts,
        )

    def add_contact(self, user_id: str, contact_in: ContactCreate) -> ContactInfo:
        """为居民添加关联人。"""
        data = self._load_data()

        if user_id not in data:
            # 从社区数据获取居民姓名
            resident_name = self._get_resident_name(user_id)
            data[user_id] = {"resident_name": resident_name, "contacts": []}

        contact_id = self._generate_contact_id(data[user_id]["contacts"])
        new_contact = ContactInfo(
            id=contact_id,
            name=contact_in.name,
            relation=contact_in.relation,
            phone=contact_in.phone,
            notify_method=contact_in.notify_method,
            quiet_hours_start=contact_in.quiet_hours_start,
            quiet_hours_end=contact_in.quiet_hours_end,
        )

        data[user_id]["contacts"].append(new_contact.model_dump())
        self._save_data(data)

        logger.info("添加关联人: user=%s, contact=%s (%s)", user_id, contact_id, contact_in.name)
        return new_contact

    def update_contact(self, user_id: str, contact_id: str, contact_in: ContactCreate) -> ContactInfo | None:
        """更新关联人信息。"""
        data = self._load_data()
        user_data = data.get(user_id, {})
        contacts = user_data.get("contacts", [])

        for i, c in enumerate(contacts):
            if c.get("id") == contact_id:
                updated = ContactInfo(
                    id=contact_id,
                    name=contact_in.name,
                    relation=contact_in.relation,
                    phone=contact_in.phone,
                    notify_method=contact_in.notify_method,
                    quiet_hours_start=contact_in.quiet_hours_start,
                    quiet_hours_end=contact_in.quiet_hours_end,
                )
                contacts[i] = updated.model_dump()
                self._save_data(data)
                logger.info("更新关联人: user=%s, contact=%s", user_id, contact_id)
                return updated

        return None

    def delete_contact(self, user_id: str, contact_id: str) -> bool:
        """删除关联人。"""
        data = self._load_data()
        user_data = data.get(user_id, {})
        contacts = user_data.get("contacts", [])
        original_len = len(contacts)

        contacts = [c for c in contacts if c.get("id") != contact_id]
        if len(contacts) == original_len:
            return False

        data[user_id]["contacts"] = contacts
        self._save_data(data)
        logger.info("删除关联人: user=%s, contact=%s", user_id, contact_id)
        return True

    def _get_resident_name(self, user_id: str) -> str:
        """从社区数据中获取居民姓名。"""
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
