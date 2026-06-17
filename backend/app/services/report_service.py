"""
LLM 健康报告生成服务。
使用 openai 原生 SDK 调用 DeepSeek-V3.2（via SiliconFlow）。
"""
import json
import logging
from datetime import datetime
from openai import OpenAI
from core.config import OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL_NAME
from core.paths import REPORTS_DIR

logger = logging.getLogger(__name__)

REPORT_PROMPT = """你是由国家卫健委指导开发的[社区智能健康助手]。
当前时间: {time}

【居民档案】
用户ID: {user_id}
体征数据: {vitals}

【AI风险评估结果】
{risk_result}

【参考的国家卫生规范】
{guidelines}

【任务】
请生成一份专业的《居民健康管理建议书》（Markdown格式）。
要求：
1. 必须包含：健康综述、风险预警、基于指南的行动建议、复诊计划。
2. 语气专业、严谨但亲切。
3. 如果是高危，请在开头用醒目的符号提示。"""


class HealthReportGenerator:
    def __init__(self):
        REPORTS_DIR.mkdir(exist_ok=True)
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
        return self._client

    def _save_to_disk(self, user_id: str, report_content: str, raw_data: dict) -> str:
        """保存报告到磁盘（.md + .json）。"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"{user_id}_{timestamp}"

        md_path = REPORTS_DIR / f"{filename_base}.md"
        md_path.write_text(report_content, encoding="utf-8")

        json_path = REPORTS_DIR / f"{filename_base}.json"
        json_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=4), encoding="utf-8")

        logger.info("报告已归档: %s", filename_base)
        return filename_base

    def generate_report(
        self,
        user_id: str,
        vitals_dict: dict,
        risk_level: str,
        risk_score: float,
        guidelines: list[str],
    ) -> str:
        """生成健康报告并保存，返回报告 Markdown 文本。"""
        vitals_str = ", ".join(f"{k}: {v}" for k, v in vitals_dict.items())
        risk_str = f"风险等级：{risk_level} (风险概率: {risk_score:.2f})"
        guidelines_str = "\n".join(f"- {g}" for g in guidelines)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        prompt = REPORT_PROMPT.format(
            user_id=user_id,
            vitals=vitals_str,
            risk_result=risk_str,
            guidelines=guidelines_str,
            time=current_time,
        )

        logger.info("正在生成 LLM 报告: user_id=%s", user_id)

        client = self._get_client()
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )
        report_content = response.choices[0].message.content

        raw_data = {
            "user_id": user_id,
            "timestamp": current_time,
            "vitals": vitals_dict,
            "risk_assessment": {"level": risk_level, "score": risk_score},
            "rag_references": guidelines,
            "ai_report": report_content,
        }
        self._save_to_disk(user_id, report_content, raw_data)

        return report_content
