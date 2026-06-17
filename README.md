# 智域卫康 — 社区慢病风险智能治理支撑系统

面向社区老年居民的健康监护平台。核心链路：**监测 → 问答 → 预警 → 通知子女**。

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                    前端 (Next.js 14)                 │
│  登录认证 │ 健康分析 │ 社区地图 │ 健康问答 │ 预警中心  │
└──────────────────────┬──────────────────────────────┘
                       │ REST API + JWT
┌──────────────────────┴──────────────────────────────┐
│                后端 (FastAPI + Python)                │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐            │
│  │ JWT 认证  │ │ XGBoost  │ │ Embedding │            │
│  │ 角色鉴权  │ │ 风险预测  │ │ RAG 检索   │            │
│  └──────────┘ └──────────┘ └───────────┘            │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐            │
│  │    LLM   │ │ 预警引擎  │ │ 关联人管理 │            │
│  │ 报告/问答 │ │          │ │           │            │
│  └──────────┘ └──────────┘ └───────────┘            │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────┴────────┐
              │  JSON 文件存储    │
              │  numpy 向量检索   │
              └─────────────────┘
```

## 核心功能

| 功能 | 说明 |
|------|------|
| 登录认证 | JWT 认证，区分管理员和普通用户角色 |
| 健康风险分析 | 体征录入 → XGBoost 预测 → RAG 检索指南 → LLM 生成报告 |
| 社区态势地图 | 热力图 + 散点标记，实时展示社区健康风险分布（管理员） |
| 健康问答助手 | 老年友好对话界面，口语化回答，支持语音输入 |
| 异常预警系统 | 体征异常 / 频繁不适提问自动触发，通知关联人（子女） |
| 关联人管理 | 为居民绑定家属，设置通知方式和免打扰时段 |
| 历史档案 | 所有 AI 报告永久留存，可追溯审计 |
| 用户管理 | 管理员可查看、新增、禁用用户（管理员） |

## 角色与权限

| 功能 | 普通用户 | 管理员 |
|------|:--------:|:------:|
| 健康分析（仅自己） | ✅ | ✅ |
| 健康问答 | ✅ | ✅ |
| 关联人管理（仅自己） | ✅ | ✅ |
| 历史报告（仅自己） | ✅ | ✅ |
| 预警查看（仅自己） | ✅ | ✅ |
| 社区态势地图 | ❌ | ✅ |
| 预警确认/处理 | ❌ | ✅ |
| 用户管理 | ❌ | ✅ |

## 快速启动

### 1. 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env
# 编辑 .env 填入你的 SiliconFlow API Key
```

### 2. 构建知识库（首次必须）

```bash
cd backend

# 训练风险预测模型
python scripts/train_risk_model.py

# 构建 RAG 向量知识库（需要 SiliconFlow API Key）
# Windows 用户需加编码参数避免 emoji 报错：
PYTHONIOENCODING=utf-8 python scripts/build_knowledge.py

# 生成社区模拟数据（默认 45 条）
python scripts/generate_map_data.py
```

### 3. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 启动服务

```bash
# 终端 1 — 启动后端（端口 8000）
cd backend
python -m uvicorn app.main:app --reload --port 8000

# 终端 2 — 启动前端（端口 3000）
cd frontend
npm run dev
```

浏览器访问 http://localhost:3000，首次启动自动跳转登录页。

后端启动后访问 http://localhost:8000/docs 查看 API 文档。

### 5. 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `admin` | `admin` | 管理员 |
| `user01` | `user01` | 普通用户 |

首次启动后端时自动创建，账号存储在 `backend/data/users.json`。

## 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `OPENAI_API_KEY` | SiliconFlow API Key | `sk-xxx` |
| `OPENAI_API_BASE` | API Base URL | `https://api.siliconflow.cn/v1` |
| `OPENAI_MODEL_NAME` | LLM 模型 | `deepseek-ai/DeepSeek-V3.2` |
| `EMBEDDING_MODEL_NAME` | Embedding 模型 | `Qwen/Qwen3-Embedding-8B` |
| `EMBEDDING_API_BASE` | Embedding API Base | 同上 |
| `EMBEDDING_API_KEY` | Embedding API Key | 同上 |
| `JWT_SECRET` | JWT 签名密钥 | `your-secret-key` |
| `JWT_EXPIRE_HOURS` | Token 过期时间（小时） | `24` |

## API 端点

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/v1/auth/login` | 登录获取 Token | 公开 |
| GET | `/api/v1/auth/me` | 获取当前用户信息 | 登录用户 |
| GET | `/api/v1/auth/users` | 用户列表 | 管理员 |
| POST | `/api/v1/auth/users` | 新增用户 | 管理员 |
| POST | `/api/v1/analyze/risk` | 健康风险分析 | 登录用户 |
| GET | `/api/v1/community/residents` | 社区居民列表 | 管理员 |
| GET | `/api/v1/community/stats` | 社区统计数据 | 管理员 |
| POST | `/api/v1/chat` | 健康问答 | 登录用户 |
| GET | `/api/v1/chat/history/{user_id}` | 聊天历史 | 登录用户 |
| GET | `/api/v1/alerts` | 预警列表 | 登录用户 |
| POST | `/api/v1/alerts/{id}/acknowledge` | 确认预警 | 管理员 |
| GET | `/api/v1/reports` | 报告列表 | 登录用户 |
| GET | `/api/v1/reports/{id}` | 报告详情 | 登录用户 |
| GET | `/api/v1/contacts/{user_id}` | 关联人列表 | 登录用户 |
| POST | `/api/v1/contacts/{user_id}` | 添加关联人 | 登录用户 |
| PUT | `/api/v1/contacts/{user_id}/{cid}` | 更新关联人 | 登录用户 |
| DELETE | `/api/v1/contacts/{user_id}/{cid}` | 删除关联人 | 登录用户 |

## 项目结构

```
HealthPilot/
├── backend/          # FastAPI 后端
│   ├── core/         # 配置中心（paths + config）
│   ├── app/
│   │   ├── api/      # 7 个路由模块（含 auth）
│   │   ├── schemas/  # Pydantic 模型
│   │   ├── services/ # 7 个业务服务（含 auth_service）
│   │   └── dependencies.py  # 认证依赖注入
│   ├── data/         # 数据文件 + 向量库 + 用户数据
│   ├── reports/      # 生成的报告
│   └── scripts/      # 工具脚本
└── frontend/         # Next.js 14 前端
    └── src/
        ├── app/      # 7 个页面（含 login）
        ├── components/ # 组件库
        ├── contexts/ # AuthContext 认证上下文
        ├── lib/      # API 封装
        ├── middleware.ts  # 路由保护
        └── types/    # TypeScript 类型
```
