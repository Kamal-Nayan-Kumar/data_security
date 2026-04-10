# Phase 6 Integration (FastAPI + Python CLI)

This project now uses the Python backend and Python CLI for end-to-end testing.

## 1) Start dependencies

```bash
docker compose up -d db
```

## 2) Configure environment

```bash
cp .env.example .env
source .env
```

## 3) Install Python dependencies

```bash
python3 -m pip install -r backend/requirements.txt -r cli/requirements.txt
```

## 4) Run FastAPI via Uvicorn

```bash
PYTHONPATH=. uvicorn backend.api.app:app --host 127.0.0.1 --port 8000
```

## 5) In a second terminal, run minimal CLI checks

```bash
python3 cli/main.py keygen
python3 cli/main.py search secure
```

Expected result:
- `keygen` creates `~/.vget/id_ed25519` and `~/.vget/id_ed25519.pub`
- `search` returns JSON (often `[]` on a fresh DB)

## Optional single-command runner

Use the helper script below to start Uvicorn and run the same CLI checks automatically:

```bash
bash scripts/phase6_integration.sh
```

## Known limitation in current codebase

`cli/main.py` uses `/api/v1/register` and `/api/v1/login`, while the FastAPI backend currently exposes `/api/v1/user/register` and `/api/v1/user/login`.
So `register`/`login` via CLI will fail until endpoint paths are aligned in a later phase.
