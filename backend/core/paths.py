"""
集中路径管理 — 消除项目中所有 os.path.dirname 链。
所有路径基于 pathlib.Path，以 backend/ 目录为根。
"""
from pathlib import Path

# === 项目根目录 ===
# backend/ 目录（本文件所在目录的上一级）
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# === 数据目录 ===
DATA_DIR: Path = PROJECT_ROOT / "data"
MODEL_PATH: Path = DATA_DIR / "risk_model.json"
VECTOR_DB_PATH: Path = DATA_DIR / "vector_db"
COMMUNITY_DATA_PATH: Path = DATA_DIR / "community_mock_data.json"
GUIDELINES_PATH: Path = DATA_DIR / "guidelines.txt"

# === 报告目录 ===
REPORTS_DIR: Path = PROJECT_ROOT / "reports"

# === 运行时数据目录（由系统自动创建）===
CHAT_LOGS_DIR: Path = DATA_DIR / "chat_logs"
CONTACTS_PATH: Path = DATA_DIR / "contacts" / "contacts.json"
ALERTS_DIR: Path = DATA_DIR / "alerts"
ALERT_HISTORY_PATH: Path = ALERTS_DIR / "alert_history.json"

# === 环境配置文件 ===
ENV_PATH: Path = PROJECT_ROOT / ".env"


def ensure_runtime_dirs():
    """确保所有运行时目录存在（启动时调用一次）。"""
    REPORTS_DIR.mkdir(exist_ok=True)
    CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    CONTACTS_PATH.parent.mkdir(parents=True, exist_ok=True)
