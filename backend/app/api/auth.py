"""
认证 API — 登录 / 获取当前用户 / 管理员用户管理
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.health import (
    LoginRequest, LoginResponse, UserOut, UserCreate, TokenData,
)
from app.services.auth_service import auth_service
from app.dependencies import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    """用户名密码登录，返回 JWT Token。"""
    user = auth_service.get_user_by_username(data.username)
    if user is None or not auth_service.verify_password(data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="账号已被禁用")

    token = auth_service.create_token(user["user_id"], user["username"], user["role"])
    logger.info("登录成功: %s", data.username)
    return LoginResponse(
        access_token=token,
        user=UserOut(
            user_id=user["user_id"],
            username=user["username"],
            name=user["name"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"],
        ),
    )


@router.get("/auth/me", response_model=UserOut)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """获取当前登录用户信息。"""
    user = auth_service.get_user_by_id(current_user.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserOut(
        user_id=user["user_id"],
        username=user["username"],
        name=user["name"],
        role=user["role"],
        is_active=user["is_active"],
        created_at=user["created_at"],
    )


@router.get("/auth/users", response_model=list[UserOut])
async def list_users(admin: TokenData = Depends(require_admin)):
    """[管理员] 获取所有用户列表。"""
    return auth_service.list_users()


@router.post("/auth/users", response_model=UserOut)
async def create_user(data: UserCreate, admin: TokenData = Depends(require_admin)):
    """[管理员] 新增用户。"""
    try:
        user = auth_service.create_user(data.username, data.password, data.name, data.role)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
