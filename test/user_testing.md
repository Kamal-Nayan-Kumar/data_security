# User Testing Guide

This guide is for the **User** laptop. You will act as the consumer of a software package published by the Developer laptop. The system will cryptographically guarantee you are installing exactly what the developer created.

## 1. Install the CLI (Binary Release)

Download the pre-compiled binary for your operating system from the GitHub Releases page:
[https://github.com/Kamal-Nayan-Kumar/data_security/releases/latest](https://github.com/Kamal-Nayan-Kumar/data_security/releases/latest)

Extract the downloaded file, open your terminal in that folder, and make it executable:

```bash
# On Mac/Linux (Replace with your actual downloaded file name)
chmod +x vget-linux-amd64
export VGET="./vget-linux-amd64"
```

## 2. Connect to the Cloud Backend

You must tell the CLI to talk to your live deployed backend instead of `localhost`:

```bash
export VGET_API_URL="https://data-security-backend.onrender.com"
```

## 3. Browse the Package Repository

Open your deployed **Vercel** Frontend URL in your browser:
**https://data-security-frontend-git-main-kamal-nayan-kumars-projects.vercel.app**
*(or whatever custom domain you configured).*

Search for the package the developer just published (e.g., `my-awesome-app-177...`). You should see it listed there with its version `1.0.0`!

## 4. Securely Install the Package

The user needs to run the `install` command using the CLI. Grab the exact package name from the Vercel dashboard and run this command:

```bash
export PACKAGE_TO_INSTALL="<paste-package-name-here>"

$VGET install "$PACKAGE_TO_INSTALL"
```

**Security Checks that happen automatically on your laptop:**
1. The CLI downloads the package file strictly **into memory**.
2. It calculates the `SHA256` checksum of the downloaded file.
3. It fetches the developer's public key from the server.
4. It compares the checksum to the expected checksum and verifies the `Ed25519` signature with the public key.
5. If **either check fails**, the CLI will panic and refuse to extract the package.

## 5. Verify Installation

```bash
ls -la "./installed/$PACKAGE_TO_INSTALL/1.0.0"
cat "./installed/$PACKAGE_TO_INSTALL/1.0.0/index.js"
```

The file should exist exactly as the developer published it, guaranteeing no man-in-the-middle tampering occurred during download!
