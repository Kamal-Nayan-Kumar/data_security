# vget

vget is a secure package repository and CLI system built with a focus on cryptographic verification and data integrity. It ensures that every package you download is exactly what the author intended to publish.

## Architecture

The system consists of two primary components:
- **Backend**: Built with FastAPI, using PostgreSQL (via SQLAlchemy and asyncpg) for persistence. It handles package metadata, user authentication (JWT), and storage.
- **CLI**: A command-line interface built with Typer that performs client-side cryptographic operations, including key generation, package signing, and verification.

## Security Features

vget implements a dual-layer security model to ensure trust and integrity:
- **SHA256 Checksums**: Every package version is hashed during publication. The client re-calculates this hash upon download to detect any corruption or tampering.
- **Ed25519 Signatures**: Developers sign the package checksum using their private key. The client verifies this signature using the developer's public key before extraction.
- **JWT Authentication**: User sessions are protected using JSON Web Tokens.
- **Local Verification**: Cryptographic checks happen on your local machine, not just the server.

## Developer Guide

### Prerequisites
- Python 3.10+
- Docker and Docker Compose

### Setup
1. Start the database and storage infrastructure:
   ```bash
   docker compose up -d
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   pip install -r cli/requirements.txt
   ```
4. Start the backend server:
   ```bash
   cd backend
   uvicorn api.main:app --reload
   ```

### Using the CLI

Run the `vget` Typer CLI (ensure your virtual environment is active):

```bash
python -m cli.main --help
```

### Publishing Packages
1. **Generate Keys**: Create your unique Ed25519 identity keys.
   ```bash
   python -m cli.main keygen
   ```
2. **Register as a Developer**: Link your public key to a username.
   ```bash
   python -m cli.main dev-register --username <your_name>
   ```
3. **Publish**: Sign and upload your package.
   ```bash
   python -m cli.main publish --path <directory_or_file> --version <version>
   ```

## User Guide

### Authentication
Users can register and log in through the CLI:
```bash
# Register a user via CLI
python -m cli.main register --username alice

# Log in via CLI
python -m cli.main login --username alice
```

### Finding and Installing Packages
1. **Search**: Find packages by name or description.
   ```bash
   python -m cli.main search <query>
   ```
2. **Install**: Download, verify, and extract a package.
   ```bash
   python -m cli.main install <package_name>
   ```
   The CLI automatically verifies the SHA256 checksum and Ed25519 signature. If verification fails, the package will not be installed.