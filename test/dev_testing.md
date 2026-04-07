# Developer Testing Guide

This guide is for the **Developer** laptop. You will act as the creator of a software package and publish it to the remote secure repository.

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

## 2. Setup Identity

To avoid conflicts with previous tests, we will clear old local keys and use a unique username.

### 🍎 Mac / 🐧 Linux (Terminal)
```bash
# Clear old keys and generate new Ed25519 keypair
rm -rf ~/.vget
$VGET keygen

# Register a unique account and upgrade to Developer
export DEV_USER="dev_$(date +%s)"
$VGET register --username "$DEV_USER" --password "secure123"
$VGET login --username "$DEV_USER" --password "secure123"
$VGET dev-register --username "$DEV_USER"
```

### 🪟 Windows (PowerShell)
```powershell
# Clear old keys and generate new Ed25519 keypair
if (Test-Path ~/.vget) { Remove-Item -Recurse -Force ~/.vget }
& $env:VGET keygen

# Register a unique account and upgrade to Developer
$DEV_USER="dev_$([math]::Floor([datetimeOffset]::UtcNow.ToUnixTimeSeconds()))"
& $env:VGET register --username "$DEV_USER" --password "secure123"
& $env:VGET login --username "$DEV_USER" --password "secure123"
& $env:VGET dev-register --username "$DEV_USER"
```

## 3. Create a Package & Publish

Create some software you want to distribute, then publish it. Publishing will automatically compress the folder, generate a SHA256 checksum, sign the checksum with your private key, and upload the payload to the server.

### 🍎 Mac / 🐧 Linux (Terminal)
```bash
export PKG_NAME="my-awesome-app-$(date +%s)"

# Create a dummy script
mkdir -p "$PKG_NAME"
echo 'console.log("Hello World!");' > "$PKG_NAME/index.js"

# Publish to the live backend
$VGET publish --path "$PKG_NAME" --version 1.0.0
```

### 🪟 Windows (PowerShell)
```powershell
$PKG_NAME="my-awesome-app-$([math]::Floor([datetimeOffset]::UtcNow.ToUnixTimeSeconds()))"

# Create a dummy script
New-Item -ItemType Directory -Force -Path $PKG_NAME
Set-Content -Path "$PKG_NAME\index.js" -Value 'console.log("Hello World!");'

# Publish to the live backend
& $env:VGET publish --path "$PKG_NAME" --version 1.0.0
```

---

**Success!** If the backend ML scanner detects no threats, your package is now live. Give your `$PKG_NAME` to the "User" laptop to test the installation.

> **Note on Windows (.exe):** 
> Do **not** double-click the `vget-windows-amd64.exe` file! It is a Command-Line Interface (CLI) tool. If you double-click it, a black window will flash for a split second and close immediately because it expects terminal arguments. You must run it from inside your PowerShell terminal using the `.\` or `&` syntax shown above.
