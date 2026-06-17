"""
认证服务 — 用户管理 + JWT 生成/验证。
数据存储在 data/users.json，与项目 JSON 文件风格一致。
"""
import json
import uuid
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import bcrypt

from core.config import JWT_SECRET, JWT_EXPIRE_HOURS
from core.paths import DATA_DIR

logger = logging.getLogger(__name__)

USERS_FILE = DATA_DIR / "users.json"

# ── 默认账号 ──
DEFAULT_USERS = [
    {"user_id": "admin_001", "username": "admin", "name": "系统管理员",
     "hashed_password": "", "role": "admin", "is_active": True,
     "created_at": datetime.now(timezone.utc).isoformat()},
    {"user_id": "user_001", "username": "user01", "name": "普通用户",
     "hashed_password": "", "role": "user", "is_active": True,
     "created_at": datetime.now(timezone.utc).isoformat()},
]
DEFAULT_PASSWORDS = {"admin": "admin", "user01": "user01"}


class AuthService:
    def __init__(self):
        self._users: list[dict] = []
        self._loaded = False

    # ── 数据读写 ──

    def _ensure_loaded(self):
        if self._loaded:
            return
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if USERS_FILE.exists():
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                self._users = json.load(f)
        else:
            self._users = []
        self._loaded = True

        # 首次启动：写入默认账号
        if not self._users:
            self._seed_defaults()

    def _save(self):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._users, f, ensure_ascii=False, indent=2)

    def _seed_defaults(self):
        for u in DEFAULT_USERS:
            pwd = DEFAULT_PASSWORDS.get(u["username"], "123456")
            u["hashed_password"] = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            self._users.append(u)
        self._save()
        logger.info("已创建默认账号: admin/admin, user01/user01")

    # ── 用户 CRUD ──

    def get_user_by_username(self, username: str) -> dict | None:
        self._ensure_loaded()
        for u in self._users:
            if u["username"] == username:
                return u
        return None

    def get_user_by_id(self, user_id: str) -> dict | None:
        self._ensure_loaded()
        for u in self._users:
            if u["user_id"] == user_id:
                return u
        return None

    def list_users(self) -> list[dict]:
        self._ensure_loaded()
        return [{k: v for k, v in u.items() if k != "hashed_password"} for u in self._users]

    def create_user(self, username: str, password: str, name: str, role: str = "user") -> dict:
        self._ensure_loaded()
        if self.get_user_by_username(username):
            raise ValueError(f"用户名 '{username}' 已存在")
        user = {
            "user_id": f"{'admin' if role == 'admin' else 'user'}_{uuid.uuid4().hex[:8]}",
            "username": username,
            "name": name,
            "hashed_password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            "role": role,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._users.append(user)
        self._save()
        logger.info("新用户创建: %s (role=%s)", username, role)
        return {k: v for k, v in user.items() if k != "hashed_password"}

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    # ── JWT ──

    @staticmethod
    def create_token(user_id: str, username: str, role: str) -> str:
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    @staticmethod
    def decode_token(token: str) -> dict | None:
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.warning("Token 已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Token 无效: %s", e)
            return None


# 模块级单例
auth_service = AuthService()
