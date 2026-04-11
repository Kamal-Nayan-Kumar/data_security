# 🛡️ vget: A Secure Cryptographic Package Registry

vget is a secure, end-to-end package repository and CLI system built with a hardcore focus on cryptographic verification and data integrity. It guarantees that every package downloaded is precisely what the author published—with zero tampering.

---

## 🌐 Deployed Links

- **Live Frontend (Registry Explorer):** `https://vget-teal.vercel.app/`
- **Official Documentation:** `[https://mintlify.wiki/Kamal-Nayan-Kumar/vget]`

---

## ⚙️ System Requirements

### Hardware Requirements
- **CPU:** 2 Cores+ (x86_64 or ARM64)
- **RAM:** 4GB+ (8GB recommended for full local development with Docker)
- **Storage:** 10GB+ free space (for Docker images, PostgreSQL volume, and package uploads)

### Software Requirements
- **Python:** `3.10+` (Backend & CLI)
- **Node.js:** `18+` (Frontend)
- **Database:** PostgreSQL 15+ (if running without Docker)
- **Containers:** Docker & Docker Compose (for seamless local infrastructure setup)
- **CLI Utility:** `curl` or `wget` (for testing API endpoints)

---

## 🔐 Core Security Features

vget implements a dual-layer security model to ensure 100% trust and integrity:

- **SHA-256 Checksums:** Every package version is hashed upon publication. The client recalculates this hash upon download to detect any corruption or network tampering.
- **Ed25519 Signatures:** Developers sign the package checksum using their private key. The client mathematically verifies this signature against the developer's public key before extracting the files.
- **JWT Authentication:** User sessions and developer uploads are strictly protected using JSON Web Tokens.
- **Local Verification:** Cryptographic verification happens entirely on your local machine—meaning you don't even have to trust the central server to guarantee package safety.
- **Auto-Compression:** Directories are safely and uniformly compressed into `.tar.gz` archives prior to cryptographic signing.

---

## 🏗️ Architecture

The system consists of three primary components:
1. **Backend (`/backend`)**: Built with FastAPI, using PostgreSQL (via SQLAlchemy and asyncpg). It handles package metadata, JWT authentication, and file storage.
2. **Frontend (`/frontend`)**: A React/Vite web application providing a beautiful UI to search, discover, and copy install commands for live packages.
3. **CLI (`/cli`)**: A Typer-powered command-line interface that performs the heavy lifting for client-side cryptographic operations (key generation, payload signing, and extraction).

---

## 🚀 Quick Start (Local Development)

### 1. Start the Infrastructure
Spin up the database and storage volumes using Docker:
```bash
docker compose up -d
```

### 2. Setup the Backend & CLI
Create and activate a Python virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate   # On Windows use: .venv\Scripts\activate
```

Install the required Python dependencies:
```bash
pip install -r backend/requirements.txt
pip install -r cli/requirements.txt
```

### 3. Start the Services
**Run the Backend:**
```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

**Run the Frontend:**
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Guide for End-to-End Testing

We have built a dedicated testing script and sample apps (`data-security-quiz` and `vget-assistant`) to verify the end-to-end pipeline.

### Step 1: Configure the CLI
Ensure your virtual environment is active, then tell the CLI where your backend is:
```bash
export VGET_API_URL="http://localhost:8000"  # Or your Live Render URL
```

### Step 2: Register as a Developer & Publish
```bash
# 1. Generate cryptographic keys
python -m cli.main keygen

# 2. Register your developer identity
python -m cli.main dev-register --username tester_dev

# 3. Publish the sample package
python -m cli.main publish --path data-security-quiz --version 1.0.0
```
*Note: You can check the Frontend UI to see your package instantly appear!*

### Step 3: Act as a User & Install
```bash
# 1. Register a standard user account
python -m cli.main register --username standard_user --password supersecret

# 2. Login
python -m cli.main login --username standard_user --password supersecret

# 3. Securely install the package
python -m cli.main install data-security-quiz
```
The CLI will automatically download, verify the SHA-256 hash, check the Ed25519 developer signature, and extract the package into the `./installed/` folder!

> For deeper developer testing scenarios (like Windows executable tests), check out the [dev_testing.md](test/dev_testing.md) file.
