# Prism — Personalized Liquidity Radar

AI-powered financial forecasting tool that predicts your bank balance for the next 6 weeks with intelligent "what-if" scenario analysis.

Built for the **NatWest Code for Purpose Hackathon**.

---

## Features

- **6-Week Balance Forecast** — Prophet time-series model with confidence intervals
- **What-If Scenario Analysis** — "What happens if I spend £500 on a flight this week?"
- **Multilingual Explanations** — English, Hinglish, and Hindi via GPT-4o-mini
- **Early Warning Alerts** — Overdraft risk and tight-cash-buffer notifications
- **Zero External Config** — Runs fully offline with SQLite and template fallbacks
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
SQLite    Prophet    GPT-4o-mini
                     (template fallback)
```

| Service | Port | Responsibility |
|---|---|---|
| API Gateway | 8080 | Auth, routing, orchestration |
| Data Service | 8003 | SQLite persistence, bcrypt auth, JWT issuance |
| Forecast Service | 8001 | Prophet time-series forecasting |
| AI Service | 8002 | NL explanations (OpenAI / template fallback) |
| Frontend | 3000 | React + Vite + Tailwind |

---

## Project Structure

```
Prism/
├── scripts/
│   └── start.sh                 # One-command startup (Mac/Linux)
├── src/
│   ├── backend/                 # API Gateway  :8080
│   │   ├── main.py
│   │   ├── deps.py              # JWT verify_token dependency
│   │   ├── client.py            # httpx client + retry logic
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── forecast.py
│   │   │   ├── scenarios.py
│   │   │   └── transactions.py
│   │   └── requirements.txt
│   ├── data-service/            # SQLite persistence  :8003
│   │   ├── main.py
│   │   ├── models/db.py
│   │   ├── schemas/requests.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   └── transaction_service.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   └── transactions.py
│   │   └── requirements.txt
│   ├── forecast-service/        # Prophet forecasting  :8001
│   │   ├── main.py
│   │   ├── schemas/requests.py
│   │   ├── services/forecast_service.py
│   │   ├── routes/forecast.py
│   │   └── requirements.txt
│   ├── ai-service/              # LLM explanations  :8002
│   │   ├── main.py
│   │   ├── schemas/requests.py
│   │   ├── services/ai_service.py
│   │   ├── routes/ai.py
│   │   └── requirements.txt
│   └── frontend/                # React + Vite  :3000
│       ├── src/
│       │   ├── pages/
│       │   ├── components/
│       │   ├── context/
│       │   └── utils/
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
cd Prism

# 2. Copy environment file
cp .env.example .env
# Optionally add your OPENAI_API_KEY in .env (the app works without it)

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

> **Tip:** Use **PowerShell** or **Git Bash** (recommended). All commands below work in both.

**Option A — Git Bash (recommended, mirrors the Mac experience)**

```bash
cp .env.example .env
bash scripts/start.sh
```

**Option B — PowerShell (manual steps)**

```powershell
# 1. Copy environment file
Copy-Item .env.example .env

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install frontend dependencies
cd src\frontend
npm install
cd ..\..

# 4. Open 5 separate PowerShell terminals and run one command in each:

# Terminal 1 — Data Service
uvicorn main:app --host 0.0.0.0 --port 8003 --app-dir src/data-service

# Terminal 2 — Forecast Service
uvicorn main:app --host 0.0.0.0 --port 8001 --app-dir src/forecast-service

# Terminal 3 — AI Service
uvicorn main:app --host 0.0.0.0 --port 8002 --app-dir src/ai-service

# Terminal 4 — API Gateway
uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir src/backend

# Terminal 5 — Frontend
cd src\frontend
npm run dev
```

> **Note for Windows users:** If `uvicorn` is not found, use `python -m uvicorn ...` instead.

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
# ── Optional: enables real GPT-4o-mini explanations ──────────────────
# Without this, the app falls back to template-based responses (still works)
OPENAI_API_KEY=

# ── JWT signing secret (change this before any real deployment) ───────
JWT_SECRET=prism-hackathon-demo-secret-2024

# ── Internal service URLs (change only if you modify the ports) ───────
FORECAST_SERVICE_URL=http://localhost:8001
AI_SERVICE_URL=http://localhost:8002
DATA_SERVICE_URL=http://localhost:8003

# ── Database path (SQLite file location) ─────────────────────────────
DATABASE_PATH=prism.db
```

---

## Demo Mode

No account needed. Click **"Try Demo Account"** on the sign-in page.

The demo user is pre-loaded with 18 realistic transactions (rent, salary, subscriptions, groceries, dining, transport) and generates a full 6-week forecast instantly.

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
| Frontend | React 18, Vite, Tailwind CSS, Recharts, Framer Motion |
| API Gateway | Python FastAPI, httpx (async, retry logic), PyJWT |
| Data Service | FastAPI, SQLAlchemy, SQLite, bcrypt |
| Forecast Service | FastAPI, Facebook Prophet, pandas, numpy |
| AI Service | FastAPI, OpenAI SDK (gpt-4o-mini), template fallback |

---

## Team

Built for NatWest Code for Purpose Hackathon 2024.
