# Prism — Personalized Liquidity Radar

## Architecture Overview

Prism uses a **microservices architecture** with a React frontend and four independent Python FastAPI backend services, all coordinated through a central API gateway.

```
┌──────────────────────────────────────────────────────┐
│                    React Frontend                    │
│                  (Vite + Tailwind)                   │
└──────────────────────┬───────────────────────────────┘
                       │ HTTP (all /api/* calls)
                       ▼
┌──────────────────────────────────────────────────────┐
│                 Backend API Gateway                  │
│            (FastAPI + httpx routing)                 │
└───────┬──────────────┬───────────────┬───────────────┘
        │              │               │
        ▼              ▼               ▼
 ┌─────────────┐ ┌───────────┐ ┌─────────────────┐
 │  Forecast   │ │    AI     │ │     Data        │
 │  Service    │ │  Service  │ │    Service       │
 │  (Prophet)  │ │ (OpenAI)  │ │ (SQLite/SQLAlch)│
 └─────────────┘ └───────────┘ └─────────────────┘
```

### Services

| Service | Path | Stack | Responsibility |
|---------|------|-------|----------------|
| Frontend | `src/frontend/` | React, Vite, Tailwind, Recharts | User interface |
| Backend Gateway | `src/backend/` | FastAPI, httpx | API routing, zero domain logic |
| Forecast Service | `src/forecast-service/` | FastAPI, Prophet, Pandas | Time-series financial forecasting |
| AI Service | `src/ai-service/` | FastAPI, OpenAI SDK | NLP explanations, intent extraction |
| Data Service | `src/data-service/` | FastAPI, SQLAlchemy, SQLite | Auth, transactions, persistence |

### Key Design Decisions

1. **Zero-friction setup** — SQLite fallback removes any need for external PostgreSQL or Supabase.
2. **Graceful AI fallback** — Template responses when `OPENAI_API_KEY` is absent.
3. **Multi-language** — English, Hinglish, and Hindi support throughout.
4. **Gateway orchestration** — Complex endpoints like scenario analysis coordinate calls across forecast + AI services.
