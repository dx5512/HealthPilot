"""
健康分析 API — POST /analyze/risk
核心分析流程：ML 预测 → RAG 检索 → LLM 报告生成 → 预警检测
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.health import VitalsInput, AnalysisResult, TokenData
from app.services.ml_service import RiskPredictor
from app.services.rag_service import GuidelineRetriever
from app.services.report_service import HealthReportGenerator
from app.services.alert_service import AlertService
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# 服务实例（模块级单例）
ml_service = RiskPredictor()
rag_service = GuidelineRetriever()
report_service = HealthReportGenerator()
alert_service = AlertService()


@router.post("/analyze/risk", response_model=AnalysisResult)
async def analyze_health_risk(data: VitalsInput, current_user: TokenData = Depends(get_current_user)):
    """
    接收居民体征数据，执行完整的健康风险分析流水线。
    1. XGBoost 风险预测
    2. RAG 国家指南检索
    3. LLM 健康报告生成
    4. 异常预警检测
    """
    try:
        logger.info("收到健康分析请求: user_id=%s", data.user_id)

        # 1. 机器学习预测
        risk_level, risk_score = ml_service.predict(data)

        # 2. RAG 检索
        guidelines = rag_service.retrieve_guidelines(risk_level, keywords="高血压")

        # 3. LLM 生成报告
        report_text = report_service.generate_report(
            user_id=data.user_id,
            vitals_dict=data.model_dump(exclude={"user_id"}),
            risk_level=risk_level,
            risk_score=risk_score,
            guidelines=guidelines,
        )

        # 4. 预警检测
        alert_ids = alert_service.check_vitals_alert(data, data.user_id)

        if alert_ids:
            logger.info("触发 %d 条预警: user_id=%s", len(alert_ids), data.user_id)

        return AnalysisResult(
            risk_level=risk_level,
            risk_score=risk_score,
            health_advice=report_text,
            guideline_refs=guidelines,
            alerts_triggered=alert_ids,
        )

    except RuntimeError as e:
        logger.error("服务运行时错误: %s", e)
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        logger.error("数据校验错误: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("健康分析异常")
        raise HTTPException(status_code=500, detail="分析服务暂时不可用，请稍后重试")
