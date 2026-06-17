"""
构建知识库向量索引 — 读取 guidelines.txt，切分文本，调用 Embedding API，
输出 embeddings.json 供 rag_service.py 检索使用。
"""
import os
import json
import requests
from dotenv import load_dotenv

# ===================== 文本分割 =====================
def split_text(text, chunk_size=300, chunk_overlap=50,
               separators=None):
    if separators is None:
        separators = ["\n\n", "\n", "。", "！", "？", "；", " "]

    def _split(current, seps):
        if len(current) <= chunk_size:
            return [current]
        for sep in seps:
            if sep in current:
                parts = current.split(sep)
                result, buf = [], ""
                for part in parts:
                    combined = buf + part + sep if buf else part
                    if len(combined) > chunk_size:
                        if buf:
                            result.extend(_split(buf, seps[1:]))
                        buf = part
                    else:
                        buf = combined
                if buf:
                    result.extend(_split(buf, seps[1:]))
                return result
        return [current[i:i + chunk_size]
                for i in range(0, len(current), chunk_size - chunk_overlap)]

    raw = _split(text, separators)
    seen = set()
    chunks = []
    for c in raw:
        c = c.strip()
        if c and c not in seen:
            seen.add(c)
            chunks.append(c)
    return chunks

# ===================== Embedding 调用 =====================
def get_embedding(text, api_key, api_base, model):
    url = f"{api_base}/embeddings"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    resp = requests.post(url, headers=headers, json={"input": text, "model": model}, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]

# ===================== 主逻辑 =====================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("EMBEDDING_API_KEY")
API_BASE = os.getenv("EMBEDDING_API_BASE")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL_NAME")

DATA_PATH = os.path.join(BASE_DIR, "data", "guidelines.txt")
EMBEDDINGS_FILE = os.path.join(BASE_DIR, "data", "vector_db", "embeddings.json")


def build_db():
    print(f"🔧 配置: api_base={API_BASE}, model={EMBEDDING_MODEL}")

    if not API_KEY or not API_BASE:
        print("❌ 未找到 EMBEDDING_API_KEY 或 EMBEDDING_API_BASE")
        return

    if not os.path.exists(DATA_PATH):
        print(f"❌ 知识库文件不存在: {DATA_PATH}")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        raw_text = f.read()

    chunks = split_text(raw_text, chunk_size=300, chunk_overlap=50)
    print(f"✂️  文档切分为 {len(chunks)} 个片段")

    # 测试 API
    try:
        test = get_embedding("测试", API_KEY, API_BASE, EMBEDDING_MODEL)
        print(f"✅ Embedding API 连通，维度: {len(test)}")
    except Exception as e:
        print(f"❌ Embedding API 连接失败: {e}")
        return

    # 逐条生成向量
    data = []
    for i, chunk in enumerate(chunks):
        emb = get_embedding(chunk, API_KEY, API_BASE, EMBEDDING_MODEL)
        data.append({"text": chunk, "embedding": emb})
        if (i + 1) % 10 == 0:
            print(f"   已处理 {i + 1}/{len(chunks)}")

    # 写入 embeddings.json
    os.makedirs(os.path.dirname(EMBEDDINGS_FILE), exist_ok=True)
    with open(EMBEDDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"✅ 知识库构建完成: {EMBEDDINGS_FILE}")
    print(f"   总片段数: {len(data)}")


if __name__ == "__main__":
    build_db()