"""
智域卫康 — 社区慢病风险智能治理支撑系统
FastAPI 后端入口
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.config import CORS_ORIGINS
from core.paths import ensure_runtime_dirs, MODEL_PATH

# ─── 日志配置 ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── 生命周期事件 ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化，关闭时清理。"""
    logger.info("系统启动中...")
    ensure_runtime_dirs()

    if not MODEL_PATH.exists():
        logger.warning("模型文件不存在: %s — 风险预测将不可用", MODEL_PATH)
    else:
        logger.info("模型文件就绪: %s", MODEL_PATH)

    logger.info("系统启动完成")
    yield
    logger.info("系统关闭")


# ─── FastAPI 实例 ───
app = FastAPI(
    title="智域卫康 — 社区慢病风险智能治理支撑系统",
    description="基于 XGBoost + RAG + LLM 的社区健康监护 API",
    version="2.0.0",
    lifespan=lifespan,
)

# ─── CORS ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── 统一异常处理 ───
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未捕获的异常: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务内部错误，请稍后重试"},
    )


# ─── 健康检查 ───
@app.get("/")
async def root():
    return {"status": "online", "system": "智域卫康", "version": "2.0.0"}


# ─── 注册路由 ───
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.community import router as community_router
from app.api.reports import router as reports_router
from app.api.chat import router as chat_router
from app.api.alerts import router as alerts_router
from app.api.contacts import router as contacts_router

app.include_router(auth_router, prefix="/api/v1", tags=["认证"])
app.include_router(health_router, prefix="/api/v1", tags=["健康分析"])
app.include_router(community_router, prefix="/api/v1", tags=["社区数据"])
app.include_router(reports_router, prefix="/api/v1", tags=["历史报告"])
app.include_router(chat_router, prefix="/api/v1", tags=["健康问答"])
app.include_router(alerts_router, prefix="/api/v1", tags=["预警管理"])
app.include_router(contacts_router, prefix="/api/v1", tags=["关联人管理"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
