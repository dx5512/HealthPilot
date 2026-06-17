"""
集中配置管理 — 统一加载 .env，导出所有配置常量。
在项目中只需 from core.config import xxx，无需再 load_dotenv。
"""
import os
from dotenv import load_dotenv
from core.paths import ENV_PATH

# === 一次性加载 .env ===
load_dotenv(ENV_PATH)


# ────────────────────────────────────────
# LLM 配置
# ────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.siliconflow.cn/v1")
OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "deepseek-ai/DeepSeek-V3.2")

# ────────────────────────────────────────
# Embedding 配置
# ────────────────────────────────────────
EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "Qwen/Qwen3-Embedding-8B")
EMBEDDING_API_BASE: str = os.getenv("EMBEDDING_API_BASE", "https://api.siliconflow.cn/v1")
EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY", "")

# ────────────────────────────────────────
# JWT 认证配置
# ────────────────────────────────────────
JWT_SECRET: str = os.getenv("JWT_SECRET", "healthpilot-secret-key-change-in-production")
JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# ────────────────────────────────────────
# CORS 配置
# ────────────────────────────────────────
CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ────────────────────────────────────────
# 体征异常预警阈值
# ────────────────────────────────────────
SYSTOLIC_CRITICAL: float = 180   # 收缩压紧急阈值
SYSTOLIC_WARNING: float = 140    # 收缩压关注阈值
DIASTOLIC_CRITICAL: float = 110  # 舒张压紧急阈值
DIASTOLIC_WARNING: float = 90    # 舒张压关注阈值
SPO2_CRITICAL: float = 90        # 血氧紧急阈值
SPO2_WARNING: float = 95         # 血氧关注阈值
HR_HIGH: int = 120               # 心率过高阈值
HR_LOW: int = 50                 # 心率过低阈值

# ────────────────────────────────────────
# 提问频率预警阈值
# ────────────────────────────────────────
CHAT_FREQ_WARNING: int = 5         # 24h 内提问 >= 5 次 → 关注
CHAT_SAME_TOPIC_CRITICAL: int = 3  # 同类别不适提问 >= 3 次 → 紧急

# ────────────────────────────────────────
# 急症关键词（触发紧急预警）
# ────────────────────────────────────────
EMERGENCY_KEYWORDS: list[str] = [
    "剧烈胸痛", "胸痛", "呼吸困难", "突然晕倒", "晕倒",
    "大量出血", "意识模糊", "严重头痛", "剧烈头痛",
    "心脏骤停", "中风", "抽搐", "昏迷",
]
