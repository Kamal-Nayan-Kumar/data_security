# Developer Testing Guide

This guide is for the **Developer** laptop. You will act as the creator of a software package and publish it to the remote secure repository.

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

## 3. Setup Identity

To avoid conflicts with previous tests, we will clear old local keys and use a unique username.

```bash
# Clear any old test data from your machine
rm -rf ~/.vget

# Generate new Ed25519 keypair
$VGET keygen

# Set a unique username for this test
export DEV_USER="dev_$(date +%s)"

# Register a standard account on the deployed backend
$VGET register --username "$DEV_USER" --password "secure123"

# Log in to get your JWT
$VGET login --username "$DEV_USER" --password "secure123"

# Upgrade to Developer (This uploads your public key to the remote database)
$VGET dev-register --username "$DEV_USER"
```

## 4. Create a Package
Create some software you want to distribute:

```bash
export PKG_NAME="my-awesome-app-$(date +%s)"

mkdir -p "$PKG_NAME"
echo 'console.log("Hello World!");' > "$PKG_NAME/index.js"
```

## 5. Publish
Publishing will automatically compress the folder, generate a SHA256 checksum, sign the checksum with your local private key, and upload the payload to the remote server.

```bash
$VGET publish --path "$PKG_NAME" --version 1.0.0
```

If the backend ML scanner detects no threats, your package is now live! Give your `$PKG_NAME` to the "User" laptop to test the installation.
