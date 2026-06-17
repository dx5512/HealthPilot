"""
XGBoost 风险预测服务。
输入体征数据，输出三级风险（低风险/中风险/高危）+ 置信度。
"""
import logging
import numpy as np
import pandas as pd
import xgboost as xgb
from core.paths import MODEL_PATH
from app.schemas.health import VitalsInput

logger = logging.getLogger(__name__)


class RiskPredictor:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        """加载 XGBoost 模型。"""
        if MODEL_PATH.exists():
            self.model = xgb.Booster()
            self.model.load_model(str(MODEL_PATH))
            logger.info("XGBoost 模型已加载: %s", MODEL_PATH)
        else:
            logger.error("找不到模型文件: %s", MODEL_PATH)

    def predict(self, data: VitalsInput) -> tuple[str, float]:
        """
        接收体征数据，返回 (风险等级, 风险概率)。
        模型缺失时抛出 RuntimeError。
        """
        if not self.model:
            raise RuntimeError("风险预测模型未加载，服务不可用")

        # 特征工程：计算 BMI
        height_m = data.height / 100.0
        bmi = data.weight / (height_m ** 2) if height_m > 0 else 0

        # 构造特征 DataFrame（顺序必须匹配训练时：age, systolic, diastolic, heart_rate, spo2, bmi）
        input_data = pd.DataFrame([{
            "age": data.age,
            "systolic": data.systolic,
            "diastolic": data.diastolic,
            "heart_rate": data.heart_rate,
            "spo2": data.spo2,
            "bmi": bmi,
        }])

        # 执行预测
        dmatrix = xgb.DMatrix(input_data)
        probs = self.model.predict(dmatrix)[0]  # [低概率, 中概率, 高概率]

        pred_label = int(np.argmax(probs))
        risk_score = float(probs[pred_label])

        labels = {0: "低风险", 1: "中风险", 2: "高危"}
        risk_level = labels.get(pred_label, "未知")

        logger.info("预测完成: %s (score=%.3f)", risk_level, risk_score)
        return risk_level, risk_score
