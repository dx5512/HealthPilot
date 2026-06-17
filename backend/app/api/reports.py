"""
报告 API — 报告列表 + 报告详情
"""
import json
import logging
from fastapi import APIRouter, HTTPException
from core.paths import REPORTS_DIR
from app.schemas.health import ReportSummary, ReportDetail

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_report_filename(filename: str) -> tuple[str, str]:
    """从文件名解析 user_id 和时间戳。格式: user_id_YYYYMMDD_HHMMSS.json"""
    name = filename.rsplit(".", 1)[0]
    parts = name.split("_", 1)
    user_id = parts[0] if len(parts) > 0 else "unknown"
    timestamp = parts[1] if len(parts) > 1 else ""
    return user_id, timestamp


@router.get("/reports", response_model=list[ReportSummary])
async def get_reports():
    """获取所有报告列表（按时间倒序）。"""
    try:
        if not REPORTS_DIR.exists():
            return []

        reports = []
        for f in REPORTS_DIR.iterdir():
            if f.suffix == ".json":
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                    user_id, timestamp = _parse_report_filename(f.name)
                    reports.append(ReportSummary(
                        id=f.stem,
                        user_id=data.get("user_id", user_id),
                        timestamp=data.get("timestamp", timestamp),
                        risk_level=data.get("risk_assessment", {}).get("level", "未知"),
                    ))
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("跳过损坏的报告文件 %s: %s", f.name, e)

        # 按时间倒序排列
        reports.sort(key=lambda r: r.timestamp, reverse=True)
        return reports

    except Exception as e:
        logger.error("获取报告列表失败: %s", e)
        raise HTTPException(status_code=500, detail="获取报告列表失败")


@router.get("/reports/{report_id}", response_model=ReportDetail)
async def get_report_detail(report_id: str):
    """获取单份报告的完整详情。"""
    try:
        report_path = REPORTS_DIR / f"{report_id}.json"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="报告不存在")

        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        user_id, timestamp = _parse_report_filename(report_path.name)
        risk_assessment = data.get("risk_assessment", {})

        return ReportDetail(
            id=report_id,
            user_id=data.get("user_id", user_id),
            timestamp=data.get("timestamp", timestamp),
            risk_level=risk_assessment.get("level", "未知"),
            risk_score=risk_assessment.get("score", 0.0),
            ai_report=data.get("ai_report", ""),
            rag_references=data.get("rag_references", []),
            vitals=data.get("vitals", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取报告详情失败: %s", e)
        raise HTTPException(status_code=500, detail="获取报告详情失败")
