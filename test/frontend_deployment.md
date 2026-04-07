# Frontend Deployment Guide (Vercel)

The frontend is a React + Vite application. The easiest and free way to deploy it is using Vercel. Vercel connects directly to your GitHub repository and automatically deploys whenever you push changes.

## Prerequisites
1. Your code **must be pushed** to GitHub.
2. A free account on [Vercel.com](https://vercel.com) linked to your GitHub.

## Deployment Steps

1. Log in to Vercel and go to your dashboard.
2. Click the **"Add New..."** button and select **"Project"**.
3. Under "Import Git Repository", find `Kamal-Nayan-Kumar/data_security` and click **Import**.
4. **Configure Project Settings (CRITICAL):**
   * **Project Name**: `vget-frontend` (or whatever you prefer)
   * **Framework Preset**: Select **`Vite`** from the dropdown menu.
   * **Root Directory**: Click "Edit" and select the **`frontend`** folder.
5. Click **Deploy**.

Vercel will install the dependencies (using bun/npm), build the React app, and provide you with a live URL (e.g., `https://vget-frontend.vercel.app`).

Users will visit this URL to browse packages!