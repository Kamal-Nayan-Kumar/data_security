# User Testing Guide

This guide is for the **User** laptop. You will act as the consumer of a software package published by the Developer laptop. The system will cryptographically guarantee you are installing exactly what the developer created.

## 1. Install the CLI

If you haven't triggered a GitHub Release yet, you can build the CLI directly from source:

```bash
# Clone your repository
git clone https://github.com/Kamal-Nayan-Kumar/data_security.git
cd data_security

# Build the CLI
cargo build --release -p cli
export VGET="./target/release/vget"
```

*(Alternatively, if you pushed a `v1.0.0` tag to GitHub, download the binary from the [Releases page](https://github.com/Kamal-Nayan-Kumar/data_security/releases), extract it, and use `export VGET="./vget"`).*

## 2. Connect to the Cloud Backend

You must tell the CLI to talk to your live deployed backend instead of `localhost`:

```bash
export VGET_API_URL="https://data-security-backend.onrender.com"
```

## 3. Browse the Package Repository

Open your deployed **Vercel** Frontend URL in your browser:
**https://data-security-frontend-git-main-kamal-nayan-kumars-projects.vercel.app**
*(or whatever custom domain you configured).*

Search for the package the developer just published (e.g., `my-awesome-app`). You should see it listed with version `1.0.0`!

## 4. Securely Install the Package

The user needs to run the `install` command using the CLI.

```bash
$VGET install my-awesome-app
```

**Security Checks that happen automatically on your laptop:**
1. The CLI downloads the package file strictly **into memory**.
2. It calculates the `SHA256` checksum of the downloaded file.
3. It fetches the developer's public key from the server.
4. It compares the checksum to the expected checksum and verifies the `Ed25519` signature with the public key.
5. If **either check fails**, the CLI will panic and refuse to extract the package.

## 5. Verify Installation

```bash
ls -la ./installed/my-awesome-app/1.0.0
cat ./installed/my-awesome-app/1.0.0/index.js
```

The file should exist exactly as the developer published it, guaranteeing no man-in-the-middle tampering occurred during download!
