#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Prism — Quick Start Script
# ─────────────────────────────────────────────────────────────────────
# Usage:  chmod +x scripts/start.sh && ./scripts/start.sh
# ─────────────────────────────────────────────────────────────────────

set -euo pipefail

echo "Starting Prism — Personalized Liquidity Radar"
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
    if command -v uv &>/dev/null; then
        uv pip install -r requirements.txt -q
    else
        python3 -m pip install -r requirements.txt -q
    fi
fi

# ── 2. Install frontend dependencies ───────────────────────────────
if [ -f "src/frontend/package.json" ]; then
    echo "Installing frontend dependencies..."
    (cd src/frontend && npm install --silent)
fi

echo ""
echo "Starting backend services..."

# ── 3. Start data-service first (gateway depends on it) ────────────
uvicorn main:app --host 0.0.0.0 --port 8003 --app-dir src/data-service &
wait_for_service "Data Service" "http://localhost:8003"

# ── 4. Start forecast-service ─────────────────────────────────────
uvicorn main:app --host 0.0.0.0 --port 8001 --app-dir src/forecast-service &
wait_for_service "Forecast Service" "http://localhost:8001"

# ── 5. Start ai-service ───────────────────────────────────────────
uvicorn main:app --host 0.0.0.0 --port 8002 --app-dir src/ai-service &
wait_for_service "AI Service" "http://localhost:8002"

# ── 6. Start backend gateway (needs all three downstream services) ──
uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir src/backend &
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
