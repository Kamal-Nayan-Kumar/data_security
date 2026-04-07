# Developer Testing Guide

This guide is for the **Developer** laptop. You will act as the creator of a software package and publish it to the remote secure repository.

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

## 2. Setup Identity
As a developer, your first step is to generate the cryptographic keys used to sign your packages.

```bash
# Generate Ed25519 keypair
$VGET keygen

# Register a standard account on the deployed backend
$VGET register --username "my_dev_account" --password "secure123"

# Log in to get your JWT
$VGET login --username "my_dev_account" --password "secure123"

# Upgrade to Developer (This uploads your public key to the remote database)
$VGET dev-register --username "my_dev_account"
```

## 3. Create a Package
Create some software you want to distribute.

```bash
mkdir -p my-awesome-app
echo 'console.log("Hello World!");' > my-awesome-app/index.js
```

## 4. Publish
Publishing will automatically compress the folder, generate a SHA256 checksum, sign the checksum with your local private key, and upload the payload to the remote server.

```bash
$VGET publish --path my-awesome-app --version 1.0.0
```

If the backend ML scanner detects no threats, your package is now live! Give your package name to the "User" laptop to test the installation.
