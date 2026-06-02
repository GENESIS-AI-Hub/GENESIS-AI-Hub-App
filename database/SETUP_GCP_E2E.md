# OpenBeavs — Complete GCP Setup Guide (E2E)

This guide walks you through setting up OpenBeavs on Google Cloud from a clean slate through a fully running production deployment on Cloud Run with PostgreSQL, Google Cloud Storage, and Microsoft SSO.

**What you will have at the end:**
- Cloud SQL PostgreSQL instance (us-west1)
- Google Cloud Storage bucket for file uploads
- Application running locally connected to Cloud SQL
- Cloud Run service deployed with automatic CI/CD
- Microsoft SSO authentication working in production

**All commands are run from the project root (`OpenBeavs/`), not from inside `database/`.**

---

## Table of Contents

1. [Phase 0 — Prerequisites](#phase-0--prerequisites)
2. [Phase 1 — GCP Infrastructure Setup (~15 min)](#phase-1--gcp-infrastructure-setup-15-min)
3. [Phase 2 — Local Development with Cloud SQL (~5 min)](#phase-2--local-development-with-cloud-sql-5-min)
4. [Phase 3 — Data Migration: SQLite to PostgreSQL (~10 min)](#phase-3--data-migration-sqlite-to-postgresql-10-min)
5. [Phase 4 — Production Deployment to Cloud Run (~15 min)](#phase-4--production-deployment-to-cloud-run-15-min)
6. [Phase 5 — Verification (~5 min)](#phase-5--verification-5-min)
7. [Phase 6 — CI/CD via Cloud Build](#phase-6--cicd-via-cloud-build)
8. [Gotchas and Known Issues](#gotchas-and-known-issues)
9. [Rollback](#rollback)

---

## Phase 0 — Prerequisites

Complete every item on this checklist before running any script. Skipping these will cause hard-to-diagnose failures mid-setup.

### Required tools

```bash
# Verify gcloud is installed
gcloud version

# Verify psql is installed (PostgreSQL client)
psql --version

# Verify you are in the project root
ls CLAUDE.md   # should exist
```

If `gcloud` is missing: https://cloud.google.com/sdk/docs/install

If `psql` is missing:
- macOS: `brew install postgresql`
- Ubuntu/Debian: `sudo apt install postgresql-client`

### GCP authentication

```bash
gcloud auth login
gcloud auth application-default login
```

Both commands are required. `auth login` is for gcloud CLI commands; `application-default login` is for the application SDK calls (Cloud Storage, Secret Manager).

### GCP project

You need a GCP project with billing enabled. If you do not have one:

1. Go to https://console.cloud.google.com
2. Create a new project
3. Enable billing under Billing in the left nav

Note your **Project ID** (e.g. `osu-genesis-hub`). This is different from the project name.

### Microsoft Azure App Registration (for SSO)

You need an Azure App Registration to get the SSO credentials. If one already exists for OpenBeavs, find:

- **Client ID (Application ID):** Azure Portal → App Registrations → your app → Overview tab
- **Tenant ID:** Same Overview tab, under "Directory (tenant) ID"
- **Client Secret:** Azure Portal → your app → Certificates & Secrets → Client secrets

You will register the redirect URI later in Phase 4 once you have the Cloud Run URL. Write down the three values above before continuing.

---

## Phase 1 — GCP Infrastructure Setup (~15 min)

This script creates all required GCP resources and generates your local configuration files.

```bash
database/setup_google_cloud.sh
```

The script is interactive. Use this table for each prompt:

| Prompt | What to enter |
|--------|--------------|
| Google Cloud Project ID | Your GCP project ID |
| Region | **`us-west1`** — this must match the Cloud Run region; entering us-central1 will require a painful migration later |
| Database instance name | Press Enter to accept default: `genesis-ai-hub-db` |
| PostgreSQL password | Choose a strong password and save it somewhere secure |
| Storage bucket name | **GCS bucket names are globally unique across all of GCP.** The default `genesis-ai-hub-uploads` is already claimed by the `osu-genesis-hub` project. If you are setting up a different GCP project, enter a unique name (e.g. `your-project-id-uploads`). |
| Service account name | Press Enter to accept default: `genesis-ai-hub-sa` |
| Confirmation (yes/no) | `yes` |

> **Already using `osu-genesis-hub`?** If the Cloud SQL instance, GCS bucket, or service account already exist from a previous run, the script will stop with an error (`set -e`). That is expected — those resources only need to be created once. Run `database/verify_cloud_status.sh` to check what already exists before re-running any setup.

The script will take 5–10 minutes while Cloud SQL provisions. When it finishes, these resources exist in your GCP project:

- Cloud SQL PostgreSQL 15 instance (`db-f1-micro` tier)
- GCS bucket with versioning enabled
- Service account `{SA_NAME}@{PROJECT_ID}.iam.gserviceaccount.com` with roles:
  - `roles/cloudsql.client`
  - `roles/storage.objectAdmin`
  - `roles/secretmanager.secretAccessor`

These local files are created:

- `~/{SA_NAME}-key.json` — service account key. **Never commit this file to git.**
- `front/.env.cloud.generated` — pre-filled environment configuration
- `database/start_cloud_sql_proxy.sh` — proxy start script with your actual connection string

### Enable PgVector extension

PgVector is required for vector/embedding search. Enable it now:

```bash
gcloud sql connect INSTANCE_NAME --user=postgres --database=webui --project=PROJECT_ID
```

Replace `INSTANCE_NAME` with what you entered (default: `genesis-ai-hub-db`) and `PROJECT_ID` with your project ID.

In the psql prompt:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

---

## Phase 2 — Local Development with Cloud SQL (~5 min)

After Phase 1, you can run the application locally while the database lives in Cloud SQL.

### Start the Cloud SQL Proxy

Open a dedicated terminal and keep it running throughout your local dev session:

```bash
database/start_cloud_sql_proxy.sh
```

This was auto-generated by the setup script with your actual project and instance values. The proxy runs on port **5432** and creates an encrypted tunnel to Cloud SQL.

If the script was not generated (e.g. the setup script failed partway through), create it from the example:

```bash
cp database/start_cloud_sql_proxy.sh.example database/start_cloud_sql_proxy.sh
# Edit the three variables at the top:
#   PROXY_PATH   = full path to the downloaded cloud_sql_proxy binary
#   PORT         = 5432
#   CONNECTION_STRING = PROJECT_ID:us-west1:INSTANCE_NAME
chmod +x database/start_cloud_sql_proxy.sh
```

### Configure the environment

```bash
cp front/.env.cloud.generated front/.env
```

Open `front/.env` and confirm these key values are present and correct:

```bash
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/webui
VECTOR_DB=pgvector
STORAGE_PROVIDER=gcs
GCS_BUCKET_NAME=genesis-ai-hub-uploads
GOOGLE_APPLICATION_CREDENTIALS=/path/to/genesis-ai-hub-sa-key.json
```

The `GOOGLE_APPLICATION_CREDENTIALS` path was set by the setup script to the actual key file path. Verify the file exists there.

### Start the application

In a second terminal:

```bash
cd front/backend && ./start.sh
```

Open http://localhost:8080. On first startup, Alembic runs automatically and creates all database tables. If you see the login screen, the database connection is working.

---

## Phase 3 — Data Migration: SQLite to PostgreSQL (~10 min)

**Skip this phase if starting fresh with no existing data.** If `front/backend/data/webui.db` does not exist or is empty, the tables were already created in Phase 2 and you are done with database setup.

With the Cloud SQL Proxy still running in its terminal:

```bash
database/migrate_to_postgres.sh
```

The script reads `DATABASE_URL` from `front/.env` automatically. It will:

1. Create a timestamped backup at `front/backend/data/backups/TIMESTAMP/`
2. Export your SQLite data to SQL
3. Convert SQLite-specific syntax to PostgreSQL
4. Import into Cloud SQL
5. Enable the PgVector extension (if not already done)
6. Verify row counts across users, chats, and messages

If the script finds existing tables in PostgreSQL, it will ask before dropping them. Type `yes` to proceed (this is safe — you have the backup).

### Verify the migration

```bash
cd database && python3 verify_cloud_data.py
```

This connects to PostgreSQL using `front/.env` and prints a summary of all tables, user count, chat count, and message count. Confirm the numbers match your original SQLite data.

---

## Phase 4 — Production Deployment to Cloud Run (~15 min)

These steps deploy the application to Cloud Run so it is accessible from the internet with full SSO.

### Step 4a — Store DATABASE_URL in Secret Manager

Cloud Run connects to Cloud SQL via a Unix socket built into the container runtime (no proxy binary needed). The URL format is different from local:

```
postgresql://postgres:PASSWORD@/webui?host=/cloudsql/PROJECT_ID:us-west1:INSTANCE_NAME
```

Store it in Secret Manager:

```bash
echo -n "postgresql://postgres:YOUR_PASSWORD@/webui?host=/cloudsql/YOUR_PROJECT_ID:us-west1:YOUR_INSTANCE_NAME" | \
  gcloud secrets create database-url \
    --data-file=- \
    --project=YOUR_PROJECT_ID
```

If the secret already exists from a previous setup, add a new version instead:

```bash
echo -n "postgresql://postgres:YOUR_PASSWORD@/webui?host=/cloudsql/YOUR_PROJECT_ID:us-west1:YOUR_INSTANCE_NAME" | \
  gcloud secrets versions add database-url \
    --data-file=- \
    --project=YOUR_PROJECT_ID
```

Verify it was stored correctly:

```bash
gcloud secrets versions access latest --secret=database-url --project=YOUR_PROJECT_ID
```

The output should match what you entered (no trailing newline).

### Step 4b — Connect Cloud Run to Cloud SQL

**Before running**, open `database/connect_cloud_run_to_sql.sh` and check the config block at the top (lines 26–36). If your project uses different values than the team defaults, update them:

```bash
PROJECT_ID="your-project-id"
CLOUD_RUN_SERVICE="your-cloud-run-service-name"
CLOUD_RUN_REGION="us-west1"
NEW_SQL_INSTANCE="your-instance-name"
SERVICE_ACCOUNT="your-sa-name@your-project-id.iam.gserviceaccount.com"
```

Then run:

```bash
database/connect_cloud_run_to_sql.sh
```

The script will:
1. Verify the Cloud SQL instance is RUNNABLE
2. Verify the `database-url` secret exists
3. Grant the service account all required IAM roles
4. Update the Cloud Run service to use the service account, enable the Cloud SQL Auth Proxy sidecar, and mount `DATABASE_URL` from Secret Manager
5. Wait up to 120 seconds for the new revision to become healthy
6. Run an HTTP health check against `/health`
7. Print recent Cloud Run logs filtered for database errors

A successful run ends with HTTP 200 and no database errors in the logs.

### Step 4c — Configure Microsoft SSO

**Azure prerequisite:** You need to register the Cloud Run redirect URI in your Azure App Registration before running this step. First, get your stable Cloud Run URL:

```bash
gcloud run services describe YOUR_CLOUD_RUN_SERVICE \
  --region=us-west1 \
  --project=YOUR_PROJECT_ID \
  --format='value(status.url)'
```

This returns your stable URL (contains the project number, e.g. `https://openbeavs-deploy-test-716080272371.us-west1.run.app`). In Azure Portal:

1. App Registrations → your app → Authentication
2. Under "Redirect URIs", add: `https://YOUR-STABLE-URL/oauth/microsoft/callback`
3. Save

**Before running**, open `database/configure_sso.sh` and verify the config block at the top (lines 13–16) matches your project:

```bash
PROJECT_ID="your-project-id"
CLOUD_RUN_SERVICE="your-cloud-run-service-name"
CLOUD_RUN_REGION="us-west1"
SERVICE_ACCOUNT="your-sa-name@your-project-id.iam.gserviceaccount.com"
```

Then run:

```bash
database/configure_sso.sh
```

The script prompts for your three Azure credentials (Client ID, Client Secret — hidden input, Tenant ID). It stores them in Secret Manager and mounts them on the Cloud Run service as environment variables.

After the script completes, set `MICROSOFT_REDIRECT_URI` explicitly. Cloud Run has two URLs (see Gotchas); the stable URL must be set or OAuth redirects will fail:

```bash
gcloud run services update YOUR_CLOUD_RUN_SERVICE \
  --region=us-west1 \
  --project=YOUR_PROJECT_ID \
  --update-env-vars="MICROSOFT_REDIRECT_URI=https://YOUR-STABLE-URL/oauth/microsoft/callback"
```

---

## Phase 5 — Verification (~5 min)

Run the status checker to confirm all cloud resources are wired up correctly.

**Before running**, open `database/verify_cloud_status.sh` and check the config block at the top (lines 12–22). Update `PROJECT_ID`, `CLOUD_RUN_SERVICE`, `NEW_SQL_INSTANCE`, `SERVICE_ACCOUNT`, and `GCS_BUCKET` if your values differ from the defaults.

```bash
database/verify_cloud_status.sh
```

Expected: all checks pass or warn with no failures. If any item shows a failure, the output will tell you which role or secret is missing.

### End-to-end smoke test

1. Open the stable Cloud Run URL in a browser
2. Click "Sign in with Microsoft" and complete the SSO flow
3. Send a chat message — if it responds, the database is connected
4. Upload a small file — if it succeeds, GCS is connected
5. Tail live logs to confirm no errors:

```bash
gcloud logging tail \
  'resource.type=cloud_run_revision AND resource.labels.service_name=YOUR_SERVICE_NAME' \
  --project=YOUR_PROJECT_ID
```

---

## Phase 6 — CI/CD via Cloud Build

Once the infrastructure is set up, every merge to `main` automatically builds and deploys:

1. Cloud Build pulls the repo
2. Builds a unified Docker image (SvelteKit frontend + Python/uvicorn backend)
3. Pushes the image to Artifact Registry (`us-west1`)
4. Deploys to Cloud Run with the full production configuration from `cloudbuild.yaml`

No manual steps are needed for subsequent deployments.

### Manual trigger

To deploy without merging to main (e.g. to test a hotfix):

```bash
gcloud builds submit --project=YOUR_PROJECT_ID
```

### If deploying to a different GCP project

`cloudbuild.yaml` contains hardcoded values for the `osu-genesis-hub` deployment. Before CI/CD will work in a new project, update these values in `cloudbuild.yaml`:

- Artifact Registry path (`us-west1-docker.pkg.dev/osu-genesis-hub/...`)
- Cloud Run service name (`openbeavs-deploy-test`)
- Cloud SQL instance (`osu-genesis-hub:us-west1:genesis-ai-hub-db-west1`)
- `MICROSOFT_REDIRECT_URI` env var (contains the hardcoded Cloud Run URL)

---

## Gotchas and Known Issues

### Two Cloud Run URLs

Cloud Run gives each service two URLs:
- **Stable URL** — contains the project number: `716080272371.us-west1.run.app`. This is permanent.
- **Internal regional URL** — changes between revisions: `ahkgdqjvhq-uw.a.run.app`.

Open WebUI uses the internal URL for OAuth redirects by default, which causes `AADSTS50011` errors from Azure because the redirect URI in the App Registration does not match. Always set `MICROSOFT_REDIRECT_URI` explicitly to the stable URL (done in Step 4c).

### `--condition=None` on IAM bindings

The GCP project policy has conditional bindings. All `gcloud projects add-iam-policy-binding` calls must include `--condition=None` or they fail in non-interactive mode with a cryptic error. The provided scripts already include this flag.

### IAM propagation delay

After any `gcloud projects add-iam-policy-binding`, Cloud SQL export/import operations may fail for up to 60 seconds while IAM propagates. The `migrate_sql_us_west1.sh` script (for the historical region migration only) includes explicit 60-second waits for this reason.

### One service account per Cloud SQL instance

Each Cloud SQL instance has its own service account (visible via `gcloud sql instances describe INSTANCE --format='value(serviceAccountEmailAddress)'`). Granting GCS access to one instance's SA does not cover a different instance. If you create a second Cloud SQL instance, grant permissions to the new instance's SA separately.

### Service account key file security

`setup_google_cloud.sh` writes the key to `~/{SA_NAME}-key.json`. This file grants full access to GCS, Cloud SQL, and Secret Manager. It is gitignored by default — confirm with `git status` before any commit. In production, prefer Workload Identity Federation over key files.

### `DATABASE_URL` format differences

Local (via proxy) and Cloud Run (via Unix socket) use different URL formats:

```bash
# Local development (proxy running on localhost:5432)
DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/webui

# Cloud Run (Unix socket — no host/port, only socket path)
DATABASE_URL=postgresql://postgres:PASSWORD@/webui?host=/cloudsql/PROJECT_ID:us-west1:INSTANCE_NAME
```

The Cloud Run format is stored in Secret Manager. Never put the Cloud Run URL in `front/.env` — it only works inside a container with the Cloud SQL Auth Proxy sidecar.

---

## Rollback

If something goes wrong before deploying to Cloud Run:

```bash
# Stop the application (Ctrl+C in the ./start.sh terminal)

# Restore your .env (use the generated backup or the cloud-generated template)
cp front/.env.backup front/.env
# or
cp front/.env.cloud.generated front/.env  # then edit DATABASE_URL back to local SQLite

# If you ran the SQLite migration and want to revert, restore from backup
# (exact path is printed at the end of the migrate_to_postgres.sh run)
cp front/backend/data/backups/TIMESTAMP/webui.db.backup front/backend/data/webui.db

# Restart with local SQLite
cd front/backend && ./start.sh
```

Your original SQLite file is never modified by the migration script — only backed up and read. Rolling back is safe.
