"""
健康问答 API — POST /chat + GET /chat/history/{user_id}
"""
import logging
from fastapi import APIRouter, HTTPException
from app.schemas.health import ChatRequest, ChatResponse, ChatMessage
from app.services.chat_service import HealthChatService

logger = logging.getLogger(__name__)
router = APIRouter()

chat_service = HealthChatService()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    接收老年人的健康问题，返回 AI 回答。
    同时记录提问日志并检测是否触发预警。
    """
    try:
        logger.info("收到健康问答: user_id=%s, question=%s", request.user_id, request.question[:30])
        result = await chat_service.chat(request.user_id, request.question)
        return result
    except RuntimeError as e:
        logger.error("问答服务错误: %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("健康问答异常")
        raise HTTPException(status_code=500, detail="问答服务暂时不可用，请稍后重试")


@router.get("/chat/history/{user_id}", response_model=list[ChatMessage])
async def get_chat_history(user_id: str):
    """获取指定用户的聊天历史。"""
    try:
        history = chat_service.get_history(user_id)
        return history
    except Exception as e:
        logger.error("获取聊天历史失败: %s", e)
        raise HTTPException(status_code=500, detail="获取聊天历史失败")
