import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 手动加载 .env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")
model_name = os.getenv("OPENAI_MODEL_NAME")

print(f"🔍 调试信息:")
print(f"   API Base:  {api_base}")
print(f"   Model:     {model_name}")
print(f"   Key的前5位: {api_key[:5] if api_key else 'None'}")

if not model_name:
    print("❌ 错误: LLM_MODEL_NAME 未读取到，请检查 .env 文件！")
    exit()

print("\n🚀 正在尝试连接模型...")

try:
    llm = ChatOpenAI(
        openai_api_key=api_key,
        openai_api_base=api_base,
        model_name=model_name,
        temperature=0.7
    )
    response = llm.invoke("你好，请回复“连接成功”四个字。")
    print(f"✅ 测试成功！模型回复: {response.content}")

except Exception as e:
    print(f"❌ 连接失败: {e}")