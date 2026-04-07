# vget

vget is a secure package repository and CLI system built with a focus on cryptographic verification and data integrity. It ensures that every package you download is exactly what the author intended to publish.

## Architecture

The system consists of two primary components:
- **Backend**: Built with Axum, using PostgreSQL (via SQLx) for persistence. It handles package metadata, user authentication (JWT), and storage.
- **CLI**: A command-line interface built with Clap that performs client-side cryptographic operations, including key generation, package signing, and verification.

## Security Features

vget implements several layers of security to ensure trust and integrity:
- **SHA256 Checksums**: Every package version is hashed during publication. The client re-calculates this hash upon download to detect any corruption or tampering.
- **Ed25519 Signatures**: Developers sign the package checksum using their private key. The client verifies this signature using the developer's public key before extraction.
- **JWT Authentication**: User sessions are protected using JSON Web Tokens.
- **Local Verification**: Cryptographic checks happen on your local machine, not just the server.

## Developer Guide

### Prerequisites
- Rust (latest stable)
- Docker and Docker Compose
- `sqlx-cli` (optional, for migrations)

### Setup
1. Start the database and storage infrastructure:
   ```bash
   docker compose up -d
   ```
2. Run migrations:
   ```bash
   cd backend && sqlx migrate run
   ```
3. Start the backend server:
   ```bash
   cargo run -p backend
   ```

### Build CLI Binary

Build the `vget` binary:

```bash
cargo build --release -p cli
```

The binary will be available at:

```bash
target/release/vget
```

### Publishing Packages
1. **Generate Keys**: Create your unique Ed25519 identity keys.
   ```bash
   target/release/vget keygen
   ```
2. **Register as a Developer**: Link your public key to a username.
   ```bash
   target/release/vget dev-register --username <your_name>
   ```
3. **Publish**: Sign and upload your package.
   ```bash
   target/release/vget publish --path <directory_or_file> --version <version>
   ```

## User Guide

### Authentication
Users can register and log in through the CLI:
```bash
# Register a user via CLI
target/release/vget register --username alice

# Log in via CLI
target/release/vget login --username alice
```

### Finding and Installing Packages
1. **Search**: Find packages by name or description.
   ```bash
   target/release/vget search <query>
   ```
2. **Install**: Download, verify, and extract a package.
   ```bash
   target/release/vget install <package_name>
   ```
   The CLI automatically verifies the SHA256 checksum and Ed25519 signature. If verification fails, the package will not be installed.
