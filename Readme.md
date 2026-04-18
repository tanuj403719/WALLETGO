# WALLETGO — Personalized Liquidity Radar

AI-powered financial forecasting tool that predicts your bank balance for the next 6 weeks, runs intelligent "what-if" scenario analysis, and now provides **goal-based savings planning** with AI-recommended spending cuts.

Built for the **NatWest Code for Purpose Hackathon**.

---

## Features

- **6-Week Balance Forecast** — Prophet time-series model with confidence intervals
- **What-If Scenario Analysis** — "What happens if I spend £500 on a flight this week?"
- **Goal-Based Forecaster** — Set a target balance and date; Gemini recommends the exact spending cuts (pause / trim / swap) needed to get there
- **Multilingual Support** — English, Hinglish, and Hindi across all AI-generated text
- **Early Warning Alerts** — Overdraft risk and tight-cash-buffer notifications
- **Zero External Config** — Runs fully offline with SQLite and deterministic fallbacks
- **Demo Mode** — One-click access with pre-seeded realistic transaction data

---

## Architecture

```
Browser (React/Vite)  :3000
         │
         ▼  REST  /api/*
 ┌───────────────────┐
 │   API Gateway     │  :8080
 │   src/backend/    │  JWT auth, CORS, retry logic
 └──┬────────┬───────┘
    │        │        │
    ▼        ▼        ▼
:8003     :8001     :8002
Data      Forecast   AI
Service   Service    Service
SQLite    Prophet    Gemini
                     (deterministic fallback)
```

| Service | Port | Responsibility |
|---|---|---|
| API Gateway | 8080 | Auth, routing, orchestration |
| Data Service | 8003 | SQLite persistence, bcrypt auth, JWT issuance |
| Forecast Service | 8001 | Prophet time-series forecasting |
| AI Service | 8002 | NL explanations + goal-cut recommendations (Gemini / fallback) |
| Frontend | 3000 | React + Vite + Tailwind |

---

## Project Structure

```
WALLETGO/
├── scripts/
│   └── start.sh                 # One-command startup (Mac/Linux)
├── src/
│   ├── backend/                 # API Gateway  :8080
│   │   ├── main.py
│   │   ├── deps.py              # JWT verify_token dependency
│   │   ├── client.py            # httpx client + retry logic
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── forecast.py      # includes /api/forecast/goal
│   │       ├── scenarios.py
│   │       └── transactions.py
│   ├── data-service/            # SQLite persistence  :8003
│   │   ├── main.py
│   │   ├── models/db.py
│   │   ├── schemas/requests.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   └── transaction_service.py
│   │   └── routes/
│   │       ├── auth.py
│   │       └── transactions.py
│   ├── forecast-service/        # Prophet forecasting  :8001
│   │   ├── main.py
│   │   ├── schemas/requests.py
│   │   ├── services/forecast_service.py
│   │   └── routes/forecast.py
│   ├── ai-service/              # LLM explanations + goal cuts  :8002
│   │   ├── main.py
│   │   ├── schemas/requests.py  # includes GoalCutsRequest
│   │   ├── services/ai_service.py
│   │   └── routes/ai.py         # includes /api/ai/goal-cuts
│   └── frontend/                # React + Vite  :3000
│       ├── src/
│       │   ├── pages/
│       │   │   └── DashboardPage.jsx   # overview, forecast, sandbox, goal tabs
│       │   ├── components/
│       │   │   ├── GoalForecaster.jsx  # goal-based planning UI
│       │   │   └── StatementUploader.jsx
│       │   ├── context/
│       │   └── utils/
│       │       └── api.js              # includes forecastAPI.goal()
│       ├── package.json
│       └── vite.config.js
├── tests/
├── docs/architecture.md
├── requirements.txt             # Unified Python deps
└── .env.example
```

---

## Quick Start

### Prerequisites

| Tool | Version | Mac install | Windows install |
|---|---|---|---|
| Python | 3.10+ | `brew install python` | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | `brew install node` | [nodejs.org](https://nodejs.org/) |
| Git | any | `brew install git` | [git-scm.com](https://git-scm.com/) |

---

### Mac / Linux

```bash
# 1. Clone
git clone <repo-url>
cd WALLETGO

# 2. Copy environment file
cp .env.example .env
# Optionally add your GEMINI_API_KEY in .env (the app works without it)

# 3. Run everything with one command
chmod +x scripts/start.sh
./scripts/start.sh
```

The script will:
- Install all Python and Node dependencies automatically
- Start each service in the correct order, polling `/health` before proceeding
- Print URLs when everything is ready

---

### Windows

**Option A — Docker (recommended, no Python setup needed)**

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bat
copy .env.example .env
docker compose up --build
```

Then open http://localhost:3000.

**Option B — PowerShell (manual)**

> Requires [Miniconda](https://docs.conda.io/en/latest/miniconda.html) — standard `pip install` fails on Windows for `prophet`.

```powershell
# 1. Copy environment file
Copy-Item .env.example .env

# 2. Create conda env and install dependencies
conda create -n walletgo python=3.11 -y
conda activate walletgo
conda install -c conda-forge prophet pandas numpy -y
pip install fastapi uvicorn pydantic python-dotenv httpx sqlalchemy google-generativeai email-validator PyJWT bcrypt python-dateutil

# 3. Install frontend dependencies
cd src\frontend; npm install; cd ..\..

# 4. Start each service in a new window
start cmd /k "conda activate walletgo && uvicorn main:app --host 0.0.0.0 --port 8003 --app-dir src/data-service"
start cmd /k "conda activate walletgo && uvicorn main:app --host 0.0.0.0 --port 8001 --app-dir src/forecast-service"
start cmd /k "conda activate walletgo && uvicorn main:app --host 0.0.0.0 --port 8002 --app-dir src/ai-service"
start cmd /k "conda activate walletgo && uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir src/backend"

# 5. Start frontend
cd src\frontend; npm run dev
```

---

### Access the app

| URL | Description |
|---|---|
| http://localhost:3000 | Frontend (main app) |
| http://localhost:8080/docs | Gateway API docs (Swagger) |
| http://localhost:8080/api/health/services | Check all services are healthy |

---

## Environment Variables

Copy `.env.example` to `.env`. The app runs fully offline without any variables set.

```env
# ── Optional: enables real Gemini explanations and goal-cut recommendations ──
# Without this, the app falls back to deterministic template-based responses
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# ── JWT signing secret (change this before any real deployment) ───────
JWT_SECRET=walletgo-hackathon-demo-secret-2024

# ── Internal service URLs (change only if you modify the ports) ───────
FORECAST_SERVICE_URL=http://localhost:8001
AI_SERVICE_URL=http://localhost:8002
DATA_SERVICE_URL=http://localhost:8003

# ── Database path (SQLite file location) ─────────────────────────────
DATABASE_PATH=walletgo.db
```

---

## Goal-Based Forecaster

The **Goal Forecaster** tab (`/dashboard/goal`) lets you set a savings target and receive a prioritised AI spending plan.

### How it works

1. Enter a **Target Balance** and **Target Date**.
2. The gateway fetches your transaction history, runs a forecast to project your balance at the target date, and calculates the monthly savings gap.
3. A **feasibility check** runs before calling Gemini: if the required monthly savings exceed 50% of your total discretionary spend, the goal is flagged as ambitious and the prompt is adjusted accordingly.
4. Gemini analyses your spending by category and returns up to 5 recommendations, each tagged with a **strategy type**:

| Strategy | Meaning | Example |
|---|---|---|
| `pause` | Completely eliminate the expense temporarily | Pause Netflix for 2 months |
| `trim` | Reduce spend in a variable category by a realistic % | Limit dining out to twice a week |
| `swap` | Replace an existing habit with a cheaper alternative | Brew coffee at home instead of buying it |

5. If no transaction data exists (demo mode), spending is estimated from typical household proportions so recommendations are always generated.

### API endpoint

```
POST /api/forecast/goal
```

**Request body:**
```json
{
  "target_amount": 10000,
  "target_date": "2026-07-01",
  "language": "en"
}
```

**Response:**
```json
{
  "goal": {
    "target_amount": 10000,
    "target_date": "2026-07-01",
    "days_remaining": 73,
    "current_projected_balance": 7800,
    "delta": 2200,
    "required_monthly_savings": 919.18,
    "required_daily_savings": 30.14,
    "is_achievable": true,
    "category_spending": { "food & dining": 875, "shopping": 625 }
  },
  "suggested_cuts": [
    {
      "category": "food & dining",
      "current_monthly_spend": 875,
      "recommended_monthly_spend": 568.75,
      "monthly_savings": 306.25,
      "cut_percentage": 35.0,
      "strategy_type": "trim",
      "action": "Limit dining out to twice a week and batch-cook meals at home."
    }
  ],
  "language": "en"
}
```

### Language support

Pass `"language": "en"`, `"hi"`, or `"hinglish"` — all `action` strings in the response are generated in the requested language.

---

## API Reference

### Gateway endpoints (port 8080)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/signup` | Register a new user |
| `POST` | `/api/auth/signin` | Sign in, receive JWT |
| `POST` | `/api/forecast/generate` | Generate 6-week balance forecast |
| `GET` | `/api/forecast/current` | Fetch current forecast |
| `POST` | **`/api/forecast/goal`** | **Goal-based savings plan with AI spending cuts** |
| `POST` | `/api/scenarios/analyze` | Run a what-if scenario |
| `POST` | `/api/scenarios/target-balance` | Plan cuts to reach a target balance |
| `GET` | `/api/transactions/list` | List transactions |
| `POST` | `/api/transactions/upload` | Upload bank statement (CSV/PDF) |

### AI Service endpoints (port 8002)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/ai/explain` | Generate forecast explanation |
| `POST` | `/api/ai/extract-intent` | Parse what-if text into scenario events |
| `POST` | `/api/ai/scenario-explanation` | Narrate scenario outcome |
| `POST` | `/api/ai/target-balance-advice` | Advice for target-balance plans |
| `POST` | **`/api/ai/goal-cuts`** | **Tri-strategy spending cut recommendations** |

---

## Gemini API — Rate Limit Handling

`google-generativeai >= 0.8` silently retries `ResourceExhausted` (HTTP 429) errors up to 4 times at the SDK transport layer before surfacing an exception. Without mitigation, a single button click could fan out into 4–8 rapid Gemini requests.

WALLETGO disables SDK-level retries on every `generate_content` call by passing a no-op retry predicate:

```python
from google.api_core import retry as _api_retry
_GEMINI_REQUEST_OPTIONS = {
    "retry": _api_retry.Retry(predicate=_api_retry.if_exception_type())
}
```

`ResourceExhausted` is also caught explicitly (before the generic `Exception` handler) and immediately falls back to the deterministic template response — no delay, no wasted quota.

---

## Demo Mode

No account needed. Click **"Try Demo Account"** on the sign-in page.

The demo user is pre-loaded with realistic transactions (rent, salary, subscriptions, groceries, dining, transport) and generates a full 6-week forecast instantly. The Goal Forecaster also works in demo mode — if no categorised transaction data is present, spending is estimated from typical household proportions so AI recommendations are always generated.

**Demo credentials** (if signing in manually):
```
Email:    demo@radar.com
Password: demo123
Token:    demo-token  (use directly in API calls via Authorization: Bearer demo-token)
```

---

## Running Tests

```bash
# Mac / Linux
python -m pytest tests/ -v

# Windows (PowerShell)
python -m pytest tests/ -v
```

Tests are smoke tests that verify each service's core logic works in isolation without running the servers.

---

## Troubleshooting

### Port already in use

**Mac / Linux:**
```bash
# Find and kill the process on a port (e.g. 8080)
lsof -ti :8080 | xargs kill -9
```

**Windows (PowerShell):**
```powershell
# Find the process
netstat -ano | findstr :8080
# Kill it (replace <PID> with the number from the last column)
taskkill /PID <PID> /F
```

### Services don't pick up code changes

The services run without `--reload`. After editing any Python file, restart the affected service:

```bash
# Kill and restart only the two AI-related services
kill $(lsof -ti:8080) $(lsof -ti:8002)
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8002 --app-dir src/ai-service &
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir src/backend &
```

### `uvicorn` not found

```bash
# Mac / Linux
pip3 install uvicorn

# Windows
pip install uvicorn
# or
python -m uvicorn ...
```

### Prophet installation fails

Prophet requires C build tools. If `pip install prophet` fails:

**Mac:**
```bash
brew install gcc
pip install prophet
```

**Windows:**
1. Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Select **"Desktop development with C++"** during install
3. Re-run `pip install prophet`

> If Prophet still fails, the app falls back to a heuristic forecaster automatically — you won't lose any functionality.

### Frontend not loading

```bash
# Make sure Node 18+ is installed
node --version

# Clear node_modules and reinstall
cd src/frontend
rm -rf node_modules   # Windows: Remove-Item -Recurse node_modules
npm install
npm run dev
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Recharts, Framer Motion, React Icons |
| API Gateway | Python FastAPI, httpx (async, retry logic), PyJWT |
| Data Service | FastAPI, SQLAlchemy, SQLite, bcrypt |
| Forecast Service | FastAPI, Facebook Prophet, pandas, numpy |
| AI Service | FastAPI, Gemini SDK (`google-generativeai >= 0.8`), deterministic fallback |

---

## Team

Built for NatWest Code for Purpose Hackathon 2026.
