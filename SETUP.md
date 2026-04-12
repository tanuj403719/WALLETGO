# WALLETGO Setup Guide

This guide covers setup for:
- macOS
- Linux
- Windows

It also includes two run modes:
1. Start full application at once
2. Start services one by one in separate terminals

---

## 1. Prerequisites

- Python 3.10+
- Node.js 18+
- npm

Optional but recommended:
- A virtual environment tool (venv is used below)

---

## 2. Clone and basic project setup

Run this once on any OS:

```bash
git clone <your-repo-url>
cd WALLETGO
```

Copy env file:

```bash
cp .env.example .env
```

If you are on Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

---

## 3. Method A: Start full application at once

### macOS and Linux (recommended)

The project already includes an all-in-one startup script:

```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

This script installs dependencies and starts:
- data-service (8003)
- forecast-service (8001)
- ai-service (8002)
- backend gateway (8080)
- frontend (3000)

### Windows PowerShell (single command flow)

Run these commands in PowerShell from project root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
cd src\frontend
npm install
cd ..\..

Start-Process powershell -ArgumentList '-NoExit','-Command','.\.venv\Scripts\Activate.ps1; python -m uvicorn main:app --host 0.0.0.0 --port 8003 --app-dir src/data-service'
Start-Process powershell -ArgumentList '-NoExit','-Command','.\.venv\Scripts\Activate.ps1; python -m uvicorn main:app --host 0.0.0.0 --port 8001 --app-dir src/forecast-service'
Start-Process powershell -ArgumentList '-NoExit','-Command','.\.venv\Scripts\Activate.ps1; python -m uvicorn main:app --host 0.0.0.0 --port 8002 --app-dir src/ai-service'
Start-Process powershell -ArgumentList '-NoExit','-Command','.\.venv\Scripts\Activate.ps1; python -m uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir src/backend'
Start-Process powershell -ArgumentList '-NoExit','-Command','cd src/frontend; npm run dev'
```

---

## 4. Method B: Start services one by one (manual)

Open 5 terminals.

### macOS/Linux Terminal 1: Data service

```bash
source .venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8003 --app-dir src/data-service
```

### macOS/Linux Terminal 2: Forecast service

```bash
source .venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --app-dir src/forecast-service
```

### macOS/Linux Terminal 3: AI service

```bash
source .venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8002 --app-dir src/ai-service
```

### macOS/Linux Terminal 4: Backend gateway

```bash
source .venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir src/backend
```

### macOS/Linux Terminal 5: Frontend

```bash
cd src/frontend
npm install
npm run dev
```

---

### Windows PowerShell Terminal 1: Data service

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8003 --app-dir src/data-service
```

### Windows PowerShell Terminal 2: Forecast service

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --app-dir src/forecast-service
```

### Windows PowerShell Terminal 3: AI service

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8002 --app-dir src/ai-service
```

### Windows PowerShell Terminal 4: Backend gateway

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir src/backend
```

### Windows PowerShell Terminal 5: Frontend

```powershell
cd src\frontend
npm install
npm run dev
```

---

## 5. Open the app

- Frontend: http://localhost:3000
- Gateway API docs: http://localhost:8080/docs
- Service health via gateway: http://localhost:8080/api/health/services

---

## 6. Stop services

- If running manually: stop each terminal with Ctrl+C
- If running via start.sh: Ctrl+C in that script terminal stops all child processes
- If running from Windows Start-Process: close each spawned PowerShell window
