# PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-07
**Project:** vget

## OVERVIEW
vget is a secure package repository and CLI system built with a focus on cryptographic verification and data integrity (SHA256 checksums, Ed25519 signatures, JWT authentication). It is a Rust workspace consisting of an Axum backend with PostgreSQL and a Clap-based CLI client.

## STRUCTURE
```
.
├── backend/          # Axum server, package metadata, auth, PostgreSQL (SQLx)
│   ├── migrations/   # SQLx database migrations
│   └── src/          # Backend source code (including handlers/)
├── cli/              # Client-side CLI using Clap
│   └── src/          # CLI source code (cryptographic ops, client interactions)
├── target/           # Build artifacts (Note: not git ignored by default in this tree)
├── .env              # Currently present in backend/.env (deviation from standard)
├── docker-compose.yml# Database and storage infrastructure
├── Cargo.toml        # Workspace root config
└── README.md         # Project documentation and guide
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Backend API Logic | `backend/src/handlers/` | Axum route handlers |
| Client Commands | `cli/src/` | Clap commands (publish, install, keygen) |
| Database Schemas | `backend/migrations/` | SQLx migrations for PostgreSQL |
| Dependencies | `Cargo.toml` (root, backend, cli) | Workspace configuration |

## CONVENTIONS
- **Workspace Layout:** Uses `backend` and `cli` as explicit workspace members. `cli/Cargo.toml` explicitly defines `[[bin]]` to `src/main.rs`.
- **Database Access:** Uses `sqlx` with compile-time checked queries.
- **Workflow:** Strictly follows "Oh My OpenAgents" global-project-workflow. Code deletions MUST use `mv` to `.trash/` instead of `rm`.
- **QA:** All major milestones MUST use `/review-work` (5-agent parallel QA) before Git commits.

## ANTI-PATTERNS (THIS PROJECT)
- **DO NOT** use `rm` or `rm -rf` in scripts or autonomous loops; always move to `.trash/` to bypass permission prompts.
- **DO NOT** commit changes autonomously unless explicitly requested.
- **DO NOT** place `.env` files in crates directly if avoidable; prefer workspace root or `.env.example`, though `backend/.env` currently exists.

## COMMANDS
```bash
# Infrastructure
docker compose up -d

# Migrations
cd backend && sqlx migrate run

# Build/Run Backend
cargo run -p backend

# Build CLI
cargo build --release -p cli
```

## NOTES
- The project is fully untracked in Git currently.
- Cryptographic checks (SHA256 & Ed25519) happen locally on the client via the CLI.
- Ensure to `use` global `.sisyphus` execution plans based on user-provided spec.
