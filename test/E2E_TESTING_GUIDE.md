# End-to-End Testing Guide for `vget`

This guide walks you through the entire lifecycle of the `vget` secure package manager ecosystem. It covers standing up the infrastructure, acting as a developer to publish a cryptographically signed package, acting as a user to securely verify and install it, and checking the frontend dashboard.

---

## Phase 1: Infrastructure Setup

You need three terminal tabs to run the ecosystem locally.

### Tab 1: Database & Backend Server
The backend handles authentication, package metadata, storage, and runs the pre-save malware checks.

```bash
# 1. Start the PostgreSQL database
docker compose up -d

# 2. Run database migrations (if not already applied)
cd backend && sqlx migrate run

# 3. Start the Axum backend server
cargo run -p backend
```
*(Leave this running. It listens on `http://localhost:8080`)*

### Tab 2: Frontend Dashboard
The frontend is a React + Vite application for users to discover packages.

```bash
# 1. Enter the frontend directory
cd frontend

# 2. Start the Vite development server (using bun as per OMO guidelines)
bun run dev
```
*(Leave this running. Open `http://localhost:5173` in your browser. It might be empty right now.)*

### Tab 3: CLI Testing (Your Main Window)
We will use this tab to run all the `vget` commands. First, build the release binary:

```bash
# 1. Build the CLI
cargo build --release -p cli

# 2. Set an alias to make running commands easier
export VGET="./target/release/vget"

# 3. Create a unique test namespace to avoid DB collisions
export USERNAME="alice_$(date +%s)"
export PKG="my-secure-tool"
```

---

## Phase 2: Developer Perspective (Publishing)

As a developer, your goal is to generate cryptographic keys, authenticate with the backend, and publish a signed package.

### 1. Setup Identity
```bash
# Generate your Ed25519 keypair locally (~/.vget/id_ed25519 and .pub)
$VGET keygen

# Register a standard user account on the backend
$VGET register --username "$USERNAME" --password "securepassword"

# Log in (This retrieves a JWT and saves it to ~/.vget/token)
$VGET login --username "$USERNAME" --password "securepassword"

# Upgrade to a Developer account (Uploads your public key so others can verify your packages)
$VGET dev-register --username "$USERNAME"
```

### 2. Create a Dummy Package
```bash
# Create a temporary folder with a dummy script inside
mkdir -p "/tmp/$PKG"
echo "echo 'Hello from $PKG!'" > "/tmp/$PKG/run.sh"
```

### 3. Publish the Package
```bash
# Publish version 1.0.0
$VGET publish --path "/tmp/$PKG" --version "1.0.0"
```
**What happens under the hood:**
1. The CLI compresses `/tmp/$PKG` into a `.tar.gz` archive.
2. It calculates the **SHA256 checksum** of the archive.
3. It signs the checksum using your **Ed25519 private key**.
4. It uploads the file, checksum, and signature to the backend.
5. **Backend Security Check:** Look at your backend logs (Tab 1). You should see the backend executing the `ml_scanner/main.py` scanner on your upload *before* it saves it to the database!

---

## Phase 3: User Perspective (Consuming)

As a user, your goal is to find software, download it, and ensure it hasn't been tampered with.

### 1. Search for the Package
```bash
# Query the backend for the package
$VGET search "$PKG"
```

### 2. Securely Install the Package
```bash
# Download, verify, and extract the package
$VGET install "$PKG"
```
**What happens under the hood:**
1. The CLI downloads the `.tar.gz` payload strictly **into memory** (no disk writes yet).
2. It hashes the downloaded bytes and compares them to the expected SHA256 checksum. If they don't match, it aborts.
3. It fetches the developer's public key and verifies the Ed25519 signature against the checksum. If forged, it aborts.
4. Only if both checks pass does it extract the archive to `./installed/my-secure-tool/1.0.0/`.

```bash
# Verify it was installed correctly
ls -la "installed/$PKG/1.0.0"
```

### 3. Update & Delete
```bash
# Create and publish a newer version (2.0.0)
echo "echo 'Version 2!'" > "/tmp/$PKG/run.sh"
$VGET publish --path "/tmp/$PKG" --version "2.0.0"

# Run update (It will detect v2.0.0 and run the secure install flow again)
$VGET update "$PKG"

# Delete the local installation
$VGET delete "$PKG"

# Permanently delete the package from the backend database (requires developer JWT)
$VGET delete "$PKG" --remote
```

---

## Phase 4: Frontend Dashboard Check

1. Open your browser to the URL shown in **Tab 2** (usually `http://localhost:5173`).
2. If you haven't deleted the package yet (or if you publish a new one), you should see a grid/list of available packages.
3. Verify that **`my-secure-tool`** appears with its version (`1.0.0` or `2.0.0`) and the developer ID.
4. Test the **Search Bar** in the UI to filter packages.
5. You should see a copyable command: `vget install my-secure-tool` next to the package.