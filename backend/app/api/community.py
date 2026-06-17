"""
社区数据 API — 居民列表 + 统计汇总
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from core.paths import COMMUNITY_DATA_PATH
from app.schemas.health import Resident, CommunityStats, TokenData
from app.dependencies import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


def _load_residents() -> list[dict]:
    """从 JSON 文件加载社区居民数据。"""
    if not COMMUNITY_DATA_PATH.exists():
        return []
    with open(COMMUNITY_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/community/residents", response_model=list[Resident])
async def get_community_residents(
    risk_level: str | None = Query(None, description="按风险等级筛选: 低风险/中风险/高危"),
    admin: TokenData = Depends(require_admin),
):
    """获取社区居民列表，支持按风险等级筛选（仅管理员）。"""
    try:
        residents = _load_residents()
        if risk_level:
            residents = [r for r in residents if r.get("status") == risk_level]
        return residents
    except Exception as e:
        logger.error("读取社区数据失败: %s", e)
        raise HTTPException(status_code=500, detail="读取社区数据失败")


@router.get("/community/stats", response_model=CommunityStats)
async def get_community_stats(admin: TokenData = Depends(require_admin)):
    """获取社区统计汇总（仅管理员）。"""
    try:
        residents = _load_residents()
        total = len(residents)
        high_risk = len([r for r in residents if r.get("status") == "高危"])
        medium_risk = len([r for r in residents if r.get("status") == "中风险"])
        low_risk = total - high_risk - medium_risk
        return CommunityStats(
            total=total,
            high_risk=high_risk,
            medium_risk=medium_risk,
            low_risk=low_risk,
        )
    except Exception as e:
        logger.error("统计社区数据失败: %s", e)
        raise HTTPException(status_code=500, detail="统计社区数据失败")
