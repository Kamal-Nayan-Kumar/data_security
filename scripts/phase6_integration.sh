#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

export PYTHONPATH="${PYTHONPATH:-.}"
export VGET_API_URL="${VGET_API_URL:-http://127.0.0.1:8000}"

echo "Starting FastAPI server on 127.0.0.1:8000"
python3 -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 >/tmp/phase6_uvicorn.log 2>&1 &
UVICORN_PID=$!

cleanup() {
  if kill -0 "$UVICORN_PID" >/dev/null 2>&1; then
    kill "$UVICORN_PID"
    wait "$UVICORN_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

python3 - <<'PY'
import time
import httpx

for _ in range(30):
    try:
        r = httpx.get("http://127.0.0.1:8000/health", timeout=1.0)
        if r.status_code == 200:
            print("Backend health check passed")
            break
    except Exception:
        pass
    time.sleep(1)
else:
    raise SystemExit("Backend did not become healthy within 30s")
PY

echo "Running CLI keygen"
python3 cli/main.py keygen

echo "Running CLI search"
python3 cli/main.py search secure

echo "Phase 6 integration script completed"
