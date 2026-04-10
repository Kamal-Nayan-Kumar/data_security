# 🎓 College Project: Team GitHub Contribution Setup Guide

This guide outlines the exact step-by-step workflow for you and your team to push your code to a **new GitHub repository** (e.g., `vget`), merge it, deploy it, and test it. This ensures the professor sees a realistic, distributed team effort.

---

## 📌 Phase 1: Code Distribution
You currently have 4 ZIP files on your machine. Send the correct ZIP file to each team member directly:
1. `1_kamal_backend_cli.zip` -> **For You (Ubuntu)**
2. `2_frontend.zip` -> **For Frontend Dev (Ubuntu)**
3. `3_cicd.zip` -> **For CI/CD Dev (Ubuntu)**
4. `4_ml_scanner.zip` -> **For ML Scanner Dev (Windows)**

---

## 🚀 Phase 2: Instructions to Send to Your Teammates
*Copy and paste this section to your team members.*

**Step 1: Extract the Code**
1. Create a new folder on your laptop and name it `vget`.
2. Extract the contents of the ZIP file I sent you *directly* inside that `vget` folder.

**Step 2: Initialize Git and Connect to the Repo**
Open your terminal (or Command Prompt) inside the `vget` folder and run:
```bash
git init
git remote add origin https://github.com/Kamal-Nayan-Kumar/vget.git  # (Replace with the actual new repo link)
```

**Step 3: Create Your Feature Branch**
Run the command that corresponds to your role:
- **Frontend Member:** `git checkout -b feature/frontend-dashboard`
- **CI/CD Member:** `git checkout -b feature/cicd-pipeline`
- **ML Scanner Member:** `git checkout -b feature/ml-vulnerability-scanner`

**Step 4: Commit and Push Your Code**
```bash
git add .
git commit -m "feat: implemented initial structure for my component"
git push -u origin <your-branch-name>
```

---

## 👨‍💻 Phase 3: Kamal's Workflow (Your Tasks)

**1. Push Your Code**
You will do the exact same thing as your teammates. Extract your `1_kamal_backend_cli.zip` into your own `vget` folder and push it to your own branch:
```bash
git checkout -b feature/backend-and-cli
git add .
git commit -m "feat: core backend and developer cli"
git push -u origin feature/backend-and-cli
```

**2. Merge Everything**
Once everyone has pushed their branches:
1. Go to the new GitHub repository.
2. You will see 4 Pull Requests.
3. Review and **Merge all 4 branches into `main`**.
*This creates the perfect GitHub contribution graph for the professor to evaluate.*

---

## 🌐 Phase 4: Deployment & CI/CD
Once all the code is merged into the `main` branch, you (or your CI/CD member) will:
1. **Render:** Connect Render to the GitHub `main` branch to automatically deploy the FastAPI backend and provision the PostgreSQL database.
2. **Vercel:** Connect Vercel to deploy the React frontend.
3. **GitHub Actions:** The CI/CD member's code includes the `.github/workflows/ci.yml` file, which will automatically run testing and prepare release builds whenever code is merged into `main`.

---

## 🧪 Phase 5: Real End-to-End Testing on Laptops
Now that the system is live and the code is unified, the team should test it locally to prepare for the demo:

### Setting Up Local Environments
Each member has an automated setup script in their folder. Have them run it in their terminal:
- **Ubuntu Members (Kamal, Frontend, CI/CD):** 
  ```bash
  chmod +x setup.sh
  ./setup.sh
  source venv/bin/activate  # (For Python components)
  ```
- **Windows Member (ML Scanner):** 
  Double-click the `setup.bat` file to automatically install `torch` and `transformers`.

### The Final Demo Test
1. Connect the CLI to the live Render Backend URL.
2. Have the ML Scanner member try to publish a malicious package (it should get blocked locally on their Windows machine).
3. Have someone publish a clean package (keys generated, signed, and uploaded).
4. Have the Frontend member verify it appears on the live Vercel dashboard.
