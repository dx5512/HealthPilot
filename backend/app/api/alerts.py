"""
预警 API — 预警列表 + 详情 + 确认处理
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.health import AlertItem, TokenData
from app.services.alert_service import AlertService
from app.dependencies import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter()

alert_service = AlertService()


@router.get("/alerts", response_model=list[AlertItem])
async def get_alerts(
    level: str | None = Query(None, description="按级别筛选: 紧急/关注"),
    status: str | None = Query(None, description="按状态筛选: 待处理/已确认"),
    current_user: TokenData = Depends(get_current_user),
):
    """获取预警列表，支持按级别和状态筛选。"""
    try:
        alerts = alert_service.get_alerts(level=level, status=status)
        return alerts
    except Exception as e:
        logger.error("获取预警列表失败: %s", e)
        raise HTTPException(status_code=500, detail="获取预警列表失败")


@router.get("/alerts/{alert_id}", response_model=AlertItem)
async def get_alert_detail(alert_id: str):
    """获取单条预警详情。"""
    try:
        alert = alert_service.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="预警不存在")
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取预警详情失败: %s", e)
        raise HTTPException(status_code=500, detail="获取预警详情失败")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, admin: TokenData = Depends(require_admin)):
    """确认/处理预警（仅管理员）。"""
    try:
        success = alert_service.acknowledge_alert(alert_id, acknowledged_by=admin.username)
        if not success:
            raise HTTPException(status_code=404, detail="预警不存在或已处理")
        return {"status": "ok", "message": "预警已确认"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("确认预警失败: %s", e)
        raise HTTPException(status_code=500, detail="确认预警失败")
