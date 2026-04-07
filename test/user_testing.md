# User Testing Guide

This guide is for the **User** laptop. You will act as the consumer of a software package published by the Developer laptop. The system will cryptographically guarantee you are installing exactly what the developer created.

## 1. Install the CLI & Connect to Cloud

Download the pre-compiled binary for your operating system from the GitHub Releases page:
[https://github.com/Kamal-Nayan-Kumar/data_security/releases/latest](https://github.com/Kamal-Nayan-Kumar/data_security/releases/latest)

Extract the downloaded file and open your terminal in that folder.

### 🍎 Mac / 🐧 Linux (Terminal)
```bash
# Make the binary executable (replace with your downloaded file name)
chmod +x vget-linux-amd64   # or vget-macos-amd64 / vget-macos-arm64

# Set up aliases and point to the cloud backend
export VGET="./vget-linux-amd64" 
export VGET_API_URL="https://data-security-backend.onrender.com"
```

### 🪟 Windows (PowerShell)
```powershell
# Set up aliases and point to the cloud backend
$env:VGET=".\vget-windows-amd64.exe"
$env:VGET_API_URL="https://data-security-backend.onrender.com"
```

## 2. Browse the Package Repository

Open your deployed **Vercel** Frontend URL in your browser:
**https://data-security-frontend-git-main-kamal-nayan-kumars-projects.vercel.app**
*(or whatever custom domain you configured).*

Search for the package the developer just published (e.g., `my-awesome-app-177...`). You should see it listed there with its version `1.0.0`!

## 3. Securely Install the Package

Grab the exact package name from the Vercel dashboard and run this command.

### 🍎 Mac / 🐧 Linux (Terminal)
```bash
export PACKAGE_TO_INSTALL="<paste-package-name-here>"
$VGET install "$PACKAGE_TO_INSTALL"

# Check the extracted package contents
ls -la "./installed/$PACKAGE_TO_INSTALL/1.0.0"
cat "./installed/$PACKAGE_TO_INSTALL/1.0.0/index.js"
```

### 🪟 Windows (PowerShell)
```powershell
$PACKAGE_TO_INSTALL="<paste-package-name-here>"
& $env:VGET install "$PACKAGE_TO_INSTALL"

# Check the extracted package contents
Get-ChildItem ".\installed\$PACKAGE_TO_INSTALL\1.0.0"
Get-Content ".\installed\$PACKAGE_TO_INSTALL\1.0.0\index.js"
```

## 🔐 Security Checks (What Happens Automatically)

1. The CLI downloads the package file strictly **into memory**.
2. It calculates the `SHA256` checksum of the downloaded file.
3. It fetches the developer's public key from the server.
4. It compares the checksum to the expected checksum and verifies the `Ed25519` signature with the public key.
5. If **either check fails**, the CLI will panic and refuse to extract the package.

The file exists exactly as the developer published it, guaranteeing no man-in-the-middle tampering occurred during download!

> **Note on Windows (.exe):** 
> Do **not** double-click the `vget-windows-amd64.exe` file! It is a Command-Line Interface (CLI) tool. If you double-click it, a black window will flash for a split second and close immediately because it expects terminal arguments. You must run it from inside your PowerShell terminal using the `.\` or `&` syntax shown above.
