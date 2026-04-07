# User Testing Guide

This guide is for the **User** laptop. You will act as the consumer of a software package published by the Developer laptop. The system will cryptographically guarantee you are installing exactly what the developer created.

## 1. Install the CLI
Download the latest `vget` CLI binary for your operating system from the [Releases page](https://github.com/Kamal-Nayan-Kumar/data_security/releases) (once the GitHub Action is finished).

Extract it and make it executable:
```bash
# On Mac/Linux
chmod +x vget
export VGET="./vget"

# Tell the CLI where the production backend is hosted:
export VGET_API_URL="https://your-backend-url.onrender.com"
```

## 2. Browse the Package Repository
Open the **Vercel** or **Netlify** URL where your Frontend React app is hosted. Search for the package the developer just published.

You should see a UI showing `my-awesome-app` and its version `1.0.0`.

## 3. Securely Install the Package
The user needs to run the `install` command.

```bash
$VGET install my-awesome-app
```

**Security Checks that happen automatically on your laptop:**
1. The CLI downloads the package file strictly **into memory**.
2. It calculates the `SHA256` checksum of the downloaded file.
3. It fetches the developer's public key from the server.
4. It compares the checksum to the expected checksum and verifies the `Ed25519` signature with the public key.
5. If **either check fails**, the CLI will panic and refuse to extract the package.

## 4. Verify Installation
```bash
ls -la ./installed/my-awesome-app/1.0.0
cat ./installed/my-awesome-app/1.0.0/index.js
```
The file should exist exactly as the developer published it.
