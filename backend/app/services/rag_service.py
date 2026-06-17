"""
RAG 指南检索服务 — 使用 numpy 余弦相似度 + JSON 向量存储。
不依赖 chromadb 或 langchain。
"""
import json
import logging
import numpy as np
from openai import OpenAI
from core.config import EMBEDDING_API_KEY, EMBEDDING_API_BASE, EMBEDDING_MODEL_NAME
from core.paths import VECTOR_DB_PATH

logger = logging.getLogger(__name__)

# 向量存储文件路径
EMBEDDINGS_FILE = VECTOR_DB_PATH / "embeddings.json"


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """计算两个向量的余弦相似度。"""
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    return dot / norm if norm > 0 else 0.0


class GuidelineRetriever:
    def __init__(self):
        self._client: OpenAI | None = None
        self._chunks: list[str] = []
        self._vectors: np.ndarray | None = None
        self._loaded = False

    def _ensure_loaded(self):
        """延迟加载向量库。"""
        if self._loaded:
            return

        if not EMBEDDINGS_FILE.exists():
            logger.warning("向量库文件不存在: %s — 请先运行 build_knowledge.py", EMBEDDINGS_FILE)
            self._loaded = True
            return

        try:
            with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._chunks = [item["text"] for item in data]
            vectors = [item["embedding"] for item in data]
            self._vectors = np.array(vectors, dtype=np.float32)

            logger.info("向量库已加载: %d 个片段, 维度 %d", len(self._chunks), self._vectors.shape[1])
        except Exception as e:
            logger.error("加载向量库失败: %s", e)

        self._loaded = True

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=EMBEDDING_API_KEY, base_url=EMBEDDING_API_BASE)
        return self._client

    def _embed(self, text: str) -> list[float]:
        """调用 Embedding API 获取向量。"""
        client = self._get_client()
        response = client.embeddings.create(input=text, model=EMBEDDING_MODEL_NAME)
        return response.data[0].embedding

    def retrieve_guidelines(self, risk_level: str, keywords: str = "高血压") -> list[str]:
        """
        根据风险等级检索最相关的国家指南条目（top-3）。
        使用 numpy 余弦相似度计算。
        """
        self._ensure_loaded()

        if not self._chunks or self._vectors is None:
            logger.warning("向量库为空，返回空结果")
            return []

        # 构造查询文本
        query = f"国家基本公共卫生服务规范 {keywords} {risk_level} 干预措施 管理要求"
        logger.info("RAG 检索: %s", query)

        # 获取查询向量
        query_vec = np.array(self._embed(query), dtype=np.float32)

        # 计算与所有片段的余弦相似度
        similarities = np.array([cosine_similarity(query_vec, v) for v in self._vectors])

        # 取 top-3
        top_indices = np.argsort(similarities)[::-1][:3]
        results = [self._chunks[i] for i in top_indices]

        logger.info("检索到 %d 条指南 (最高相似度: %.3f)", len(results), similarities[top_indices[0]])
        return results
