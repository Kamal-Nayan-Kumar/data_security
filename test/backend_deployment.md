# Backend Deployment Guide (Render)

The backend is a combined Rust Axum server and a Python ML scanner. It requires a managed PostgreSQL database. Render.com provides an excellent free tier for both web services and databases.

## Prerequisites
1. Your code **must be pushed** to GitHub.
2. A free account on [Render.com](https://render.com) linked to your GitHub.

## Deployment Steps

### Phase 1: Set up the Database
1. Go to the Render Dashboard, click **New +**, and select **PostgreSQL**.
2. Give it a name (e.g., `vget-db`), leave the rest as default, and select the **Free** instance type.
3. Click **Create Database**.
4. Once created, scroll down to the **Connections** section and copy the **"Internal Database URL"**. You will need this for the backend.

### Phase 2: Deploy the Web Service
1. Go back to the Render Dashboard, click **New +**, and select **Web Service**.
2. Connect the `Kamal-Nayan-Kumar/data_security` GitHub repository.
3. **Configure the Service (CRITICAL):**
   * **Name**: `vget-backend`
   * **Language**: `Docker`
   * **Branch**: `main`
   * **Root Directory**: `.` (leave empty or set to root so Docker can access both `backend/` and `other memeber work/`)
   * **Docker Command**: Leave default
   * **Dockerfile Path**: `backend/Dockerfile`
4. **Environment Variables:**
   * Click "Advanced" or "Environment Variables".
   * Add `DATABASE_URL` as the key.
   * Paste the **"Internal Database URL"** from Phase 1 as the value.
5. Select the **Free** instance type.
6. Click **Create Web Service**.

Render will now pull your repository, build the Rust binary, install the Python ML dependencies, and start the Axum server!

Your live backend URL will look something like: `https://vget-backend.onrender.com`.

**CRITICAL NEXT STEP**: You MUST give this URL to your users. They need to run `export VGET_API_URL="https://vget-backend.onrender.com"` before using the CLI, as explained in the testing guides!