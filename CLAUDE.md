# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

智域卫康 (HealthPilot) — A community health monitoring platform for elderly residents. Core pipeline: **vitals monitoring → health Q&A → risk alerts → notify family contacts**. Built with FastAPI (backend) + Next.js 14 (frontend).

## Common Commands

### Backend

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Run server (port 8000)
python -m uvicorn app.main:app --reload --port 8000

# First-time setup: build ML model + knowledge base + mock data
python scripts/train_risk_model.py
PYTHONIOENCODING=utf-8 python scripts/build_knowledge.py   # needs SiliconFlow API key
python scripts/generate_map_data.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # dev server on port 3000
npm run build  # production build
npm run lint   # ESLint
```

### Environment Variables

Create `backend/.env` from the template in README.md. Required: `OPENAI_API_KEY` (SiliconFlow), `JWT_SECRET`. All config loaded in `backend/core/config.py`.

## Architecture

### Data Flow

```
Frontend (Next.js) ──REST + JWT──► FastAPI Backend
                                      │
                                      ├─ XGBoost risk prediction (ml_service)
                                      ├─ RAG guideline retrieval (rag_service → numpy cosine similarity)
                                      ├─ LLM report/Q&A generation (via SiliconFlow OpenAI-compatible API)
                                      ├─ Alert engine (alert_service → notifies family contacts)
                                      └─ JSON file storage (no database)
```

### Backend (`backend/`)

- **`core/paths.py`** — Centralized path constants. All file I/O references these. `DATA_DIR` is the single source of truth for data locations.
- **`core/config.py`** — Loads `.env` once, exports all config constants (LLM, JWT, alert thresholds, emergency keywords).
- **`app/main.py`** — FastAPI app with lifespan hook, CORS, global exception handler. Registers 7 routers under `/api/v1`.
- **`app/dependencies.py`** — Auth dependency injection: `get_current_user` (JWT decode) and `require_admin` (role check).
- **`app/api/`** — 7 route modules: auth, health, community, reports, chat, alerts, contacts.
- **`app/services/`** — Business logic layer. Each service is a module-level singleton (e.g. `auth_service = AuthService()`).
- **`app/schemas/health.py`** — Pydantic models for request/response validation.
- **`data/`** — JSON file storage: `users.json`, `contacts/`, `alerts/`, `chat_logs/`, `vector_db/`, `risk_model.json`, `community_mock_data.json`. No SQL database.
- **`scripts/`** — Offline setup scripts (train model, build vector DB, generate mock data).

### Frontend (`frontend/`)

- **Next.js 14 App Router** — Pages in `src/app/` (alerts, analysis, chat, community, contacts, login, records, users).
- **`src/middleware.ts`** — Route guard: all pages require `auth_token` cookie except `/login`.
- **`src/contexts/AuthContext.tsx`** — Client-side auth state. Stores JWT in cookie, validates via `/auth/me` on mount.
- **`src/lib/api.ts`** — Typed API client. Auto-attaches JWT, handles 401 → redirect to login. All backend calls go through this module.
- **`src/types/index.ts`** — Shared TypeScript interfaces matching backend Pydantic schemas.
- **`src/components/`** — Reusable UI: layout (Sidebar), analysis (VitalsForm, RiskResult), community (HealthMap with Leaflet), ui (RiskBadge).
- **Styling**: Tailwind CSS with `@tailwindcss/typography` plugin. Custom colors defined in `tailwind.config.ts` (primary blue `#0078FF`).

### Key Patterns

- **No database** — All persistence is JSON files on disk. Services load data lazily with `_ensure_loaded()` pattern.
- **Auth flow**: Frontend stores JWT in cookie → middleware checks cookie → API calls attach `Authorization: Bearer` header → backend `get_current_user` dependency decodes JWT.
- **Two roles**: `admin` (full access: community map, alert management, user CRUD) and `user` (self-only: analysis, Q&A, contacts, reports).
- **LLM integration**: Uses SiliconFlow's OpenAI-compatible API (not direct OpenAI). Model: `deepseek-ai/DeepSeek-V3.2`. Embedding: `Qwen/Qwen3-Embedding-8B`.
- **RAG**: Custom numpy-based vector search (no chromadb/langchain). Vectors stored in `data/vector_db/embeddings.json`.
- **Alert triggers**: Automatic on abnormal vitals (BP, SpO2, HR thresholds) or frequent health questions. Notifies bound family contacts.

### Default Accounts

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin` | admin |
| `user01` | `user01` | user |

Auto-created on first backend start, stored in `backend/data/users.json`.
