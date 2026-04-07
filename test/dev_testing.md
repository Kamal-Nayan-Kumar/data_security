# Developer Testing Guide

This guide is for the **Developer** laptop. You will act as the creator of a software package and publish it to the remote secure repository.

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

## 3. Setup Identity
Generate your cryptographic keys and register an account on the live server:

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

## 4. Create a Package
Create some software you want to distribute:

```bash
mkdir -p my-awesome-app
echo 'console.log("Hello World!");' > my-awesome-app/index.js
```

## 5. Publish
Publishing will automatically compress the folder, generate a SHA256 checksum, sign the checksum with your local private key, and upload the payload to the remote server.

```bash
$VGET publish --path my-awesome-app --version 1.0.0
```

If the backend ML scanner detects no threats, your package is now live! Give your package name to the "User" laptop to test the installation.
