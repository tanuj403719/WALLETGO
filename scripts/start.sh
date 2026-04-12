#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# WALLETGO — Quick Start Script
# ─────────────────────────────────────────────────────────────────────
# Usage:  chmod +x scripts/start.sh && ./scripts/start.sh
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR=".venv"
if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python"

echo "Starting WALLETGO — Personalized Liquidity Radar"
echo ""

# ── Helper: wait until a service /health endpoint returns 200 ────────
wait_for_service() {
    local name="$1"
    local url="$2"
    local max_attempts=30
    local attempt=1

    echo "  Waiting for $name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url/health" >/dev/null 2>&1; then
            echo "  $name is ready."
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    echo "ERROR: $name did not become healthy after ${max_attempts}s. Check logs above."
    exit 1
}

# ── 1. Install Python dependencies ──────────────────────────────────
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    "$PYTHON_BIN" -m pip install --upgrade pip -q
    "$PYTHON_BIN" -m pip install -r requirements.txt -q
fi

# ── 2. Install frontend dependencies ───────────────────────────────
if [ -f "src/frontend/package.json" ]; then
    echo "Installing frontend dependencies..."
    (cd src/frontend && npm install --silent)
fi

echo ""
echo "Starting backend services..."

# ── 3. Start data-service first (gateway depends on it) ────────────
"$PYTHON_BIN" -m uvicorn main:app --host 0.0.0.0 --port 8003 --app-dir src/data-service &
wait_for_service "Data Service" "http://localhost:8003"

# ── 4. Start forecast-service ─────────────────────────────────────
"$PYTHON_BIN" -m uvicorn main:app --host 0.0.0.0 --port 8001 --app-dir src/forecast-service &
wait_for_service "Forecast Service" "http://localhost:8001"

# ── 5. Start ai-service ───────────────────────────────────────────
"$PYTHON_BIN" -m uvicorn main:app --host 0.0.0.0 --port 8002 --app-dir src/ai-service &
wait_for_service "AI Service" "http://localhost:8002"

# ── 6. Start backend gateway (needs all three downstream services) ──
"$PYTHON_BIN" -m uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir src/backend &
wait_for_service "API Gateway" "http://localhost:8080"

# ── 7. Start frontend ─────────────────────────────────────────────
echo "Starting Frontend on :3000..."
(cd src/frontend && npm run dev) &

echo ""
echo "All services running!"
echo "   Frontend:  http://localhost:3000"
echo "   Gateway:   http://localhost:8080"
echo ""

wait
