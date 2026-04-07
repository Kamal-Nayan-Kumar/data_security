# Vget Secure Package Repository - Development Plan

## Context
The user is building `vget`, a secure package repository and CLI tool similar to `apt`, focusing heavily on data security, privacy, and cryptographic verification. The system is split into four main divisions to accommodate group work:
1. **CLI (User's primary responsibility)**: Built in Rust using `clap`, `ed25519-dalek`, and `sha2`. Handles user/developer authentication (public/private keys), downloading, updating, deleting packages, and secure developer pushing (signing + uploading).
2. **Code Check**: Integrating malware/security static analysis (from "other member work") into the backend Axum route upon package upload.
3. **CI/CD Pipeline**: Automated testing and release pipeline via GitHub Actions.
4. **Frontend**: A React/Vite dashboard to view available software, descriptions, and installation commands.

The current backend is Rust (Axum + PostgreSQL/SQLx), and the CLI is Rust (Clap). We will stick strictly to Rust for the backend and CLI to maintain consistency and leverage its memory safety and crypto ecosystem.

## Task Dependency Graph

| Task | Depends On | Reason |
|------|------------|--------|
| Task 1 (CLI Core Auth & Keygen) | None | Foundation for all secure operations. Requires `ed25519-dalek` and `sha2`. |
| Task 2 (CLI Publish & Sign) | Task 1 | Needs identity (keys) and authentication to sign and upload packages. |
| Task 3 (CLI Install & Verify) | Task 2 | Needs published packages to download and verify signatures/checksums against. |
| Task 4 (CLI Update & Delete) | Task 2, Task 3 | Extends the package lifecycle management. |
| Task 5 (Backend Code Check Integration) | Task 2 | Requires the upload route to be functional to intercept and analyze uploaded files. |
| Task 6 (Frontend Dashboard) | None | Can be built in parallel using mock API data or the existing Axum backend schema. |
| Task 7 (CI/CD Pipeline) | Task 1, Task 2 | Needs core functionality to exist so tests can be automated and binaries can be released. |

## Parallel Execution Graph

Wave 1 (Start immediately):
├── Task 1: CLI Core Auth & Keygen (No dependencies)
└── Task 6: Frontend Dashboard Initialization (No dependencies)

Wave 2 (After Wave 1 completes):
├── Task 2: CLI Publish & Sign (Depends: Task 1)
└── Task 7: CI/CD Pipeline (Depends: Task 1 - basic tests can be set up)

Wave 3 (After Wave 2 completes):
├── Task 3: CLI Install & Verify (Depends: Task 2)
└── Task 5: Backend Code Check Integration (Depends: Task 2)

Wave 4 (After Wave 3 completes):
└── Task 4: CLI Update & Delete (Depends: Task 2, Task 3)

Critical Path: Task 1 → Task 2 → Task 3 → Task 4
Estimated Parallel Speedup: ~35% faster than sequential execution.

## Tasks

### Task 1: CLI Core Auth & Keygen
**Description**: Implement `keygen`, `register`, and `login` commands in the Rust CLI. Generate Ed25519 keypairs locally, store them securely (e.g., in `~/.vget/credentials`), and authenticate with the Axum backend to retrieve JWTs.
**Delegation Recommendation**:
- Category: `deep` - Core cryptographic logic requires careful implementation and error handling.
- Skills: `git-master` - For atomic commits.
**Skills Evaluation**:
- ✅ INCLUDED `git-master`: Essential for clean commit history.
- ❌ OMITTED `frontend-ui-ux`: Not a UI task.
**Depends On**: None
**Acceptance Criteria**: 
- `vget keygen` creates valid Ed25519 keypairs. 
- `vget register` and `vget login` successfully interact with the backend and store a JWT locally.
- Comprehensive unit tests for crypto utilities.

### Task 2: CLI Publish & Sign
**Description**: Implement the `publish` command. The CLI must compress the target directory/file, calculate a SHA256 checksum, sign the checksum with the developer's Ed25519 private key, and push the payload + signature to the Axum backend.
**Delegation Recommendation**:
- Category: `ultrabrain` - High-stakes logic involving file I/O, hashing, signing, and multipart HTTP requests.
- Skills: `git-master`
**Skills Evaluation**:
- ✅ INCLUDED `git-master`: Crucial for tracking changes atomically.
- ❌ OMITTED `playwright`: No browser interaction needed.
**Depends On**: Task 1
**Acceptance Criteria**:
- `vget publish` successfully compresses, hashes, signs, and uploads a package.
- Backend database registers the new package version, checksum, and signature.
- Test coverage for the hashing and signing process.

### Task 3: CLI Install & Verify
**Description**: Implement the `install` command. Download the package from the backend, fetch the developer's public key (or use a local keyring), calculate the SHA256 of the downloaded payload, and verify the Ed25519 signature BEFORE extracting.
**Delegation Recommendation**:
- Category: `deep` - Requires careful streaming of downloads and strict cryptographic verification logic.
- Skills: `git-master`
**Skills Evaluation**:
- ✅ INCLUDED `git-master`: Standard for version control.
- ❌ OMITTED `ai-slop-remover`: Not refactoring at this stage.
**Depends On**: Task 2
**Acceptance Criteria**:
- CLI downloads package payload and metadata.
- Rejects package with strict error if SHA256 mismatch or Signature verification fails.
- Extracts package successfully to the designated directory if verified.

### Task 4: CLI Update & Delete
**Description**: Add `update` (check for newer versions, verify, and replace) and `delete` (remove local package and optionally unpublish from backend if authorized) commands.
**Delegation Recommendation**:
- Category: `quick` - Extends existing CLI logic with straightforward file and API operations.
- Skills: `git-master`
**Skills Evaluation**:
- ✅ INCLUDED `git-master`: For clean commits.
- ❌ OMITTED `dev-browser`: CLI only.
**Depends On**: Task 2, Task 3
**Acceptance Criteria**:
- `vget update <pkg>` fetches the latest version and verifies it.
- `vget delete <pkg>` removes local files securely.

### Task 5: Backend Code Check Integration (Malware/Security)
**Description**: Integrate the security check scripts/logic from the "other member work" folder into the Axum backend's publish route. The upload must be rejected if the static analysis fails.
**Delegation Recommendation**:
- Category: `deep` - Requires integrating external scripts/processes into an async Rust web server context safely.
- Skills: `git-master`
**Skills Evaluation**:
- ✅ INCLUDED `git-master`: For version control.
- ❌ OMITTED `frontend-ui-ux`: Backend task.
**Depends On**: Task 2
**Acceptance Criteria**:
- Upload route runs the malicious code checker on the temporary uploaded file.
- Returns `400 Bad Request` or `406 Not Acceptable` if malware is detected.
- Logs the security event.

### Task 6: Frontend Dashboard Initialization
**Description**: Initialize a React + Vite (TypeScript) project. Create a dashboard that lists packages from the Axum API, displays their descriptions, versions, and the `vget install <pkg>` commands.
**Delegation Recommendation**:
- Category: `visual-engineering` - Specialized for UI/UX, React, and layout.
- Skills: `frontend-ui-ux`, `git-master`
**Skills Evaluation**:
- ✅ INCLUDED `frontend-ui-ux`: Ideal for building a presentable, clean dashboard without mockups.
- ✅ INCLUDED `git-master`: For version control.
**Depends On**: None
**Acceptance Criteria**:
- React/Vite app runs successfully.
- Fetches and displays package lists from the backend API.
- Responsive and modern design appropriate for a package registry (like crates.io or npmjs).

### Task 7: CI/CD Pipeline Setup
**Description**: Create GitHub Actions workflows (`.github/workflows/`) to automatically run `cargo clippy`, `cargo test`, and build release binaries for Linux/macOS/Windows on push/PR.
**Delegation Recommendation**:
- Category: `writing` - YAML configuration and pipeline setup.
- Skills: `git-master`
**Skills Evaluation**:
- ✅ INCLUDED `git-master`: For committing workflows.
- ❌ OMITTED `review-work`: Standard CI setup doesn't require complex multi-agent review.
**Depends On**: Task 1, Task 2
**Acceptance Criteria**:
- Commits trigger automated tests.
- Releases generate downloadable artifacts.

## Commit Strategy
- **Atomic Commits**: Every task will have its own isolated branch (e.g., `feat/cli-auth`, `feat/cli-publish`).
- **TDD Flow**: Commits will follow a `test: add cases` -> `feat: implement logic` -> `refactor: clean up` cadence.
- **Review**: Major milestones will utilize `/review-work` locally before merging to the `main` branch to ensure strict QA.

## Success Criteria
1. CLI can autonomously generate keys, sign, publish, and securely verify/install packages.
2. Backend successfully rejects bad packages via the integrated security check.
3. Frontend provides a clear, presentable catalog of packages.
4. CI/CD runs seamlessly on GitHub.
5. Codebase is clean, secure, and fully written in Rust for the core systems.