# OpenBeavs Deployment & Contribution Guide
**Team #043 | CS Capstone**

This document outlines the standard development lifecycle for the OpenBeavs platform. To ensure code stability and maintain a reliable production environment on Google Cloud Run, all developers must adhere to this workflow.

## 1. Publish a New Git Branch
Direct commits to the `main` branch are restricted. All new features, bug fixes, or documentation updates must be done on a dedicated branch.

* **Naming Convention:** Use descriptive prefixes like `feature/`, `bugfix/`, or `hotfix/` (e.g., `feature/a2a-protocol-update`).
* **Command:**
  ```bash
  git checkout main
  git pull origin main
  git checkout -b feature/your-feature-name
  ```

## 2. Make Changes & Test Locally
Develop your changes using the local environment setup. Ensure both the backend and frontend function correctly before committing.

* **Production backend (`front/backend/`):** Run `bash backend/dev.sh` from `front/` (port 8080). This is where all new feature work goes.
* **Prototype backend (`back/`):** Navigate to `back/`, ensure `ruff check .` passes, and run `uvicorn main:app --reload`. Use only for quick prototyping — see [CLAUDE.md](../CLAUDE.md) for the distinction.
* **Frontend:** Navigate to `front/` and run `npm run dev` (port 5173).

## 3. Commit and Push Branch
Keep your commits granular and ensure your commit messages clearly describe the changes made.

* **Stage & Commit:**
  ```bash
  git add .
  git commit -m "Brief, clear description of the changes"
  ```
* **Push to GitHub:**
  ```bash
  git push -u origin feature/your-feature-name
  ```

## 4. Open a Pull Request (PR)
Navigate to the GitHub repository and open a Pull Request to merge your feature branch into `main`.

* **Description:** Clearly summarize what the PR accomplishes, why the changes were made, and list any specific testing instructions for the reviewer.
* **Reviewers:** Assign at least one other team member to review and approve your code.

## 5. Merge to Main
Once the PR has been reviewed and approved:

1. Select **"Create a merge commit"** (default — preserves individual commit history). Use squash only for very small/noisy PRs where the granular history adds no value.
2. Delete your feature branch to keep the repository tidy.

---

## 6. Automatic Deployment via Google Cloud Build
Merging code into the `main` branch automatically triggers the CI/CD pipeline defined in our `cloudbuild.yaml`. **No manual execution of `deploy.sh` is required for standard updates.** The pipeline executes on a high-powered Google Cloud build machine (`E2_HIGHCPU_8`) within the `osu-genesis-hub` project and follows these exact steps:

### Phase A: Cache & Build
* **Pull Cache:** The pipeline pulls the previous Docker image (`openbeavs-frontend:latest`) from Google Artifact Registry (`us-west1`) to use as a layer cache, significantly speeding up the build process.
* **Unified Build:** The pipeline executes a build from the root directory. It compiles the SvelteKit frontend and bundles it alongside the Python/FastAPI backend into a single, unified Docker container.

### Phase B: Push & Deploy
* **Artifact Registry:** The newly built image is tagged with both the specific GitHub commit SHA (`$COMMIT_SHA`) and `latest`, then pushed securely to Artifact Registry.
* **Cloud Run Deployment:** The pipeline deploys the new image to the Cloud Run service named `openbeavs-deploy-test`.

### Cloud Run Service Specifications
Developers should be aware that the automated deployment enforces the following infrastructure specs:

* **Region:** `us-west1`
* **Compute:** 4 CPUs with 8Gi Memory (CPU Boost enabled)
* **Environment:** Gen2 Execution Environment
* **Port:** `8080`
* **Key Environment Variables Injected:**
  * `ENV=prod`
  * `OFFLINE_MODE=true`
  * `RAG_EMBEDDING_MODEL_AUTO_UPDATE=false`
  * `BYPASS_EMBEDDING_AND_RETRIEVAL=true`
  * *(Note: `WEBUI_SECRET_KEY` is currently set to a placeholder and must be managed in the GCP console for production security).*

> **Troubleshooting:** If the automatic deployment fails, the DevOps Lead or a team member with GCP access should check the **Cloud Build Logs** in the Google Cloud Console to identify the failure point (e.g., linting error, build failure, or deployment timeout).
