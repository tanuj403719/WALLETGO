# WALLETGO - Personalized Liquidity Radar

WALLETGO is a full-stack microservice app for proactive money planning. It turns bank statements into a 42-day liquidity forecast, allows natural-language what-if simulation, and explains outcomes in English, Hinglish, or Hindi.

## Why WALLETGO Stands Out To Hackathon Judges

- Real user pain solved: people usually react after cash crunch, WALLETGO predicts it first.
- End-to-end build: ingestion, modeling, AI reasoning, and interactive UX in one product.
- Demo-friendly: no-login flow plus real-account flow, both available during judging.
- Explainable output: low/likely/high scenario overlays and confidence score, not black-box numbers.

## Architecture

```text
React/Vite Frontend (:3000)
                |
                | REST /api/*
                v
FastAPI API Gateway (:8080)
    - token verification
    - request orchestration
    - downstream health checks
            |                |                |
            v                v                v
Data Service       Forecast Service   AI Service
(:8003)            (:8001)            (:8002)
Supabase storage   Prophet hybrid     Gemini + fallback templates
CSV/PDF parsing    scenario math      intent + explanation generation
```

## Services

| Service | Port | Purpose |
|---|---|---|
| Frontend | 3000 | Landing, demo, sign-in, dashboard UX |
| API Gateway | 8080 | Single entry point, auth, fan-out routing |
| Data Service | 8003 | Statement parsing, Supabase persistence, stats/recurring data |
| Forecast Service | 8001 | 42-day forecast generation and scenario transformations |
| AI Service | 8002 | Scenario intent extraction + multilingual narrative explanation |

## App Navigation Guide (Current UI)

This section is designed for judges and first-time users.

### Public routes (top nav)

- `/` - Landing page (product pitch + CTA).
- `/demo` - Interactive no-login showcase.
- `/signin` - Sign in / create account.
- `/privacy`, `/terms` - policy pages.

### Demo journey (no login)

1. Open `/demo` from landing.
2. Click `Upload Statement Demo` to go to `/bank-linking?mode=upload`.
3. Upload CSV/PDF statement (parse-only mode, no persistence required).
4. Auto-navigate to dashboard with generated forecast.
5. Use left menu tabs:
     - `Overview`
     - `Forecast`
     - `What-If Sandbox`
6. Use `Exit Demo` in sidebar to return home.

Alternative demo path:

- On `/demo`, choose `Continue with Sample Data` to jump directly to `/dashboard`.

### Signed-in journey

1. Open `/signin`.
2. Sign in or create account.
3. First-time account with no transactions sees `Upload your first statement` step.
4. After upload, dashboard unlocks full view.
5. Signed-in sidebar includes:
     - `Overview`
     - `Forecast`
     - `What-If Sandbox`
     - `Settings`

Notes on recent UI behavior:

- The old Alerts tab was intentionally removed.
- `/dashboard/alerts` now redirects to `/dashboard`.
- The mic button and default scenario chips were removed from sandbox; users type their own what-if prompt.

## Dashboard Walkthrough (What To Show Judges)

### Overview tab

- Liquidity score card.
- Minimum 30-day balance and date.
- Model confidence indicator.
- Radar gauge and health summary.

### Forecast tab

- 42-day projected balance chart.
- Confidence badge.
- Optional baseline toggle.
- Scenario overlay support (low/likely/high dotted lines when a scenario is run).

### What-If Sandbox tab

- Free-text what-if input.
- Language switch: English, Hinglish, Hindi.
- Run Scenario button.
- Built-in helper box explaining prompt style and interpretation.

### Settings tab (signed-in only)

- Currency selection.
- Theme toggle.
- Alert buffer slider used by dashboard risk framing.

## Hackathon Demo Playbook (5-7 Minutes)

### 1) Opening pitch (30-45 seconds)

- Problem: users discover cash flow risk too late.
- Solution: WALLETGO predicts 42 days ahead and simulates decisions before spending.

### 2) Instant traction (60-90 seconds)

- Open `/demo`.
- Show one-click entry and/or direct sample-data dashboard path.
- Highlight speed: insight in seconds, no onboarding friction.

### 3) Real-data credibility (90-120 seconds)

- Go to upload demo flow.
- Upload one PDF from `test_statements/`.
- Show forecast refresh and risk metrics update.

### 4) Decision intelligence (90-120 seconds)

- In sandbox, type a natural prompt like:
    - `What if my salary is 5 days late?`
    - `What if I spend $800 next week?`
- Show low/likely/high lines and explanation text.

### 5) Technical depth close (60-90 seconds)

- Mention architecture split:
    - gateway orchestration
    - Supabase persistence
    - forecast model with fallback
    - Gemini extraction/explanations with graceful fallback

### 6) Impact close (20-30 seconds)

- "We move users from reactive budgeting to proactive financial planning."

## Repository Layout

```text
WALLETGO/
    Readme.md
    SETUP.md
    requirements.txt
    scripts/
        start.sh
    src/
        backend/
        data-service/
        forecast-service/
        ai-service/
        frontend/
    configs/
        supabase_schema.sql
    test_statements/        # 10 sample PDF statements
    tests/
```

## Setup

Use full instructions in `SETUP.md`.

Quick start on macOS/Linux:

```bash
git clone <your-repo-url>
cd WALLETGO
cp .env.example .env
cp src/frontend/.env.example src/frontend/.env
# set your GEMINI_API_KEY in .env
chmod +x scripts/start.sh
./scripts/start.sh
```

## Environment Variables

Root `.env` (backend services):

- `GEMINI_API_KEY`, `GEMINI_MODEL`
- `FORECAST_SERVICE_URL`, `AI_SERVICE_URL`, `DATA_SERVICE_URL`
- `JWT_SECRET`
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_TRANSACTIONS_TABLE`, `SUPABASE_JWT_AUDIENCE`, `SUPABASE_ISSUER`

Frontend `src/frontend/.env`:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- optional `VITE_API_URL`

## API Surface (Gateway)

- `/api/auth/*`
- `/api/transactions/*`
- `/api/forecast/*`
- `/api/scenarios/*`
- `/api/health/services`

Gateway docs: http://localhost:8080/docs

## Forecast and Scenario Output

Forecast service returns:

- `forecast_data`
- `confidence`
- `min_balance`
- `min_balance_date`
- `model` (`prophet-hybrid` or `fallback-hybrid`)

Scenario analysis returns transformed curves:

- `low`
- `likely`
- `high`
- AI explanation text

## Statement Ingestion

- Supported formats: CSV and PDF.
- `test_statements/` includes 10 sample PDFs for quick demos/tests.
- Parse modes:
    - parse-only (demo / non-persistent)
    - upload (authenticated + persistent)
- Parser supports header normalization, encoding detection, PDF table extraction, regex fallback, category inference, and duplicate suppression via fingerprints.

## Running Tests

```bash
python -m pytest tests/ -v
```

## Tech Stack

Frontend:

- React 18
- Vite
- Tailwind CSS
- Recharts
- Framer Motion
- Axios
- Supabase JS SDK

Backend/services:

- Python + FastAPI
- httpx
- PyJWT
- Supabase Python SDK
- pandas + numpy + prophet
- google-generativeai
- pdfplumber + chardet

## Troubleshooting

### Services not starting

- Ensure ports `3000`, `8001`, `8002`, `8003`, and `8080` are free.
- Check health endpoints:
    - http://localhost:8001/health
    - http://localhost:8002/health
    - http://localhost:8003/health
    - http://localhost:8080/health

### Supabase errors

- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in root `.env`.
- Apply `configs/supabase_schema.sql` if transaction table is missing.

### AI sounds generic

- Set a valid `GEMINI_API_KEY` in root `.env`.
- Without key, AI service intentionally uses fallback templates.
