# PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-10
**Project:** vget

## OVERVIEW
vget is a secure package repository and CLI system built with a focus on cryptographic verification and data integrity (SHA256 checksums, Ed25519 signatures, JWT authentication). It was recently rewritten from Rust to Python, consisting of a FastAPI backend with PostgreSQL and a Typer-based CLI client.

## STRUCTURE
```
.
├── backend/   # FastAPI server, package metadata, auth, PostgreSQL (SQLAlchemy/asyncpg)
│   ├── api/          # FastAPI route handlers
│   ├── core/         # Core business logic and security components
│   └── db/           # Database models and interactions
├── cli/       # Client-side CLI using Typer
│   ├── core/         # Cryptographic ops, client interactions
│   └── main.py       # Typer CLI entrypoint
├── .venv/            # Python virtual environment
├── .env              # Environment variables
├── docker-compose.yml# Database and storage infrastructure
├── requirements.txt  # Dependency definitions (in respective folders)
└── README.md         # Project documentation and guide
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Backend API Logic | `backend/api/` | FastAPI route handlers |
| Client Commands | `cli/main.py` | Typer commands (publish, install, keygen) |
| Database Schemas | `backend/db/` | SQLAlchemy models and setup |
| Dependencies | `backend/requirements.txt` & `cli/requirements.txt` | Python dependencies |

## CONVENTIONS
- **Workspace Layout:** Uses `backend` and `cli` as distinct modules.
- **Database Access:** Uses `SQLAlchemy` and `asyncpg` for asynchronous database queries.
- **Workflow:** Strictly follows "Oh My OpenAgents" global-project-workflow. Code deletions MUST use `mv` to `.trash/` instead of `rm`.
- **QA:** All major milestones MUST use `/review-work` (5-agent parallel QA) before Git commits.

## ANTI-PATTERNS (THIS PROJECT)
- **DO NOT** use `rm` or `rm -rf` in scripts or autonomous loops; always move to `.trash/` to bypass permission prompts.
- **DO NOT** commit changes autonomously unless explicitly requested.
- **DO NOT** place `.env` files in submodules directly if avoidable; prefer workspace root or `.env.example`.

## COMMANDS
```bash
# Infrastructure
docker compose up -d

# Virtual Environment Setup
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r cli/requirements.txt

# Build/Run Backend
cd backend && uvicorn api.main:app --reload

# Run CLI
python -m cli.main --help
```

## NOTES
- Cryptographic checks (SHA256 & Ed25519) happen locally on the client via the CLI.
- Dual-layer security model ensures both JWT authentication and Ed25519 payload signatures.
- Ensure to `use` global `.sisyphus` execution plans based on user-provided spec.