#!/bin/bash
set -e

echo "====================================================="
echo "   GENESIS AI HUB DEPLOYMENT MENU                    "
echo "====================================================="
echo "Which environment would you like to update?"
echo "  1) Development (dev)  - For testing WIP code"
echo "  2) Testing (test)     - For QA and release candidates"
echo "  3) Live (prod)        - Production environment"
echo "====================================================="
read -p "Enter choice [1-3]: " env_choice

case $env_choice in
    1)
        ENV_SUFFIX="-dev"
        ENV_NAME="Development"
        # PROJECT_ID="your-dev-project-id" # Uncomment if you split into separate GCP projects
        ;;
    2)
        ENV_SUFFIX="-test"
        ENV_NAME="Testing"
        # PROJECT_ID="your-test-project-id" # Uncomment if you split into separate GCP projects
        ;;
    3)
        ENV_SUFFIX="-prod"
        ENV_NAME="Production"
        # PROJECT_ID="your-prod-project-id" # Uncomment if you split into separate GCP projects
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

# --- Configuration ---
BASE_SERVICE_NAME="open-webui"
SERVICE_NAME="${BASE_SERVICE_NAME}${ENV_SUFFIX}"
REGION="us-west1"
REPO_NAME="open-webui-repo"

# Grabs the current active project, or uses the overrides in the case statement above
PROJECT_ID=$(gcloud config get-value project)

# Append the environment and a timestamp to the image tag so you keep a history of builds
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="genesis-hub${ENV_SUFFIX}-${TIMESTAMP}" 
TARGET="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${BASE_SERVICE_NAME}:${IMAGE_TAG}"

echo ""
echo "====================================================="
echo "   PREPARING $ENV_NAME DEPLOYMENT                    "
echo "====================================================="
echo "Project:      $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region:       $REGION"
echo "Target Image: $TARGET"
echo "====================================================="

read -p "Proceed with build and deployment to $ENV_NAME? (y/n): " confirm
if [[ "$confirm" != "y" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# 1. Setup Registry (If not exists)
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" >/dev/null 2>&1; then
    gcloud artifacts repositories create "$REPO_NAME" --repository-format=docker --location="$REGION"
fi

# 2. BUILD THE CUSTOM IMAGE
echo "-----------------------------------------------------"
echo "Building Container from Local Source (High Memory)..."
echo "-----------------------------------------------------"
gcloud builds submit . --tag "$TARGET" --machine-type=e2-highcpu-8

# 3. DEPLOY TO CLOUD RUN
echo "-----------------------------------------------------"
echo "Deploying to Cloud Run: $SERVICE_NAME ..."
echo "-----------------------------------------------------"

gcloud run deploy "$SERVICE_NAME" \
    --image="$TARGET" \
    --region="$REGION" \
    --platform="managed" \
    --allow-unauthenticated \
    --execution-environment="gen2" \
    --memory="8Gi" \
    --cpu="4" \
    --min-instances=1 \
    --port=8080 \
    --timeout=600 \
    --set-env-vars="HOST=0.0.0.0,WEBUI_PORT=8080,PYTHONUNBUFFERED=1,WEBUI_AUTH=True,DATA_DIR=/tmp,HF_HOME=/tmp/cache,SENTENCE_TRANSFORMERS_HOME=/tmp/cache,ENABLE_RAG_WEB_SEARCH=False,ENABLE_RAG_LOCAL_DOCS=False,HF_HUB_DISABLE_PROGRESS_BARS=1"

echo "====================================================="
echo "$ENV_NAME Deployment Complete!"
echo "URL: $(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")"
echo "====================================================="
