"""
关联人管理 API — CRUD 操作
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.health import ContactInfo, ContactCreate, ResidentContacts, TokenData
from app.services.contact_service import ContactService
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

contact_service = ContactService()


@router.get("/contacts/{user_id}", response_model=ResidentContacts)
async def get_contacts(user_id: str, current_user: TokenData = Depends(get_current_user)):
    """获取指定居民的关联人列表。"""
    try:
        result = contact_service.get_contacts(user_id)
        return result
    except Exception as e:
        logger.error("获取关联人失败: %s", e)
        raise HTTPException(status_code=500, detail="获取关联人失败")


@router.post("/contacts/{user_id}", response_model=ContactInfo)
async def add_contact(user_id: str, contact: ContactCreate, current_user: TokenData = Depends(get_current_user)):
    """为居民添加关联人。"""
    try:
        result = contact_service.add_contact(user_id, contact)
        return result
    except Exception as e:
        logger.error("添加关联人失败: %s", e)
        raise HTTPException(status_code=500, detail="添加关联人失败")


@router.put("/contacts/{user_id}/{contact_id}", response_model=ContactInfo)
async def update_contact(user_id: str, contact_id: str, contact: ContactCreate, current_user: TokenData = Depends(get_current_user)):
    """更新关联人信息。"""
    try:
        result = contact_service.update_contact(user_id, contact_id, contact)
        if not result:
            raise HTTPException(status_code=404, detail="关联人不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("更新关联人失败: %s", e)
        raise HTTPException(status_code=500, detail="更新关联人失败")


@router.delete("/contacts/{user_id}/{contact_id}")
async def delete_contact(user_id: str, contact_id: str, current_user: TokenData = Depends(get_current_user)):
    """删除关联人。"""
    try:
        success = contact_service.delete_contact(user_id, contact_id)
        if not success:
            raise HTTPException(status_code=404, detail="关联人不存在")
        return {"status": "ok", "message": "关联人已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除关联人失败: %s", e)
        raise HTTPException(status_code=500, detail="删除关联人失败")
