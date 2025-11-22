#!/bin/bash

# Exit on error
set -e

# --- Configuration ---
# Load variables from .env file
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found."
    exit 1
fi

# Validate that variables are set
if [ -z "$GCP_PROJECT_ID" ] || [ -z "$GCP_REGION" ]; then
    echo "Error: GCP_PROJECT_ID or GCP_REGION not set in .env."
    exit 1
fi

echo "Configuration loaded: Project $GCP_PROJECT_ID in Region $GCP_REGION"

# --- Pre-flight Checks ---

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker."
    exit 1
fi

# Check if user is logged into gcloud
if [ -z "$(gcloud auth list --filter=status:ACTIVE --format='value(account)')" ]; then
    echo "Error: You are not logged into Google Cloud. Run 'gcloud auth login'."
    exit 1
fi

# Service names
BACKEND_SERVICE_NAME="genesis-ai-hub-backend"
FRONTEND_SERVICE_NAME="genesis-ai-hub-frontend"

# --- Backend Deployment ---
echo "Deploying backend..."

# Build the Docker image
docker build -t gcr.io/$GCP_PROJECT_ID/$BACKEND_SERVICE_NAME:latest ./back

# Push the image to Google Container Registry
docker push gcr.io/$GCP_PROJECT_ID/$BACKEND_SERVICE_NAME:latest

# Deploy to Cloud Run
gcloud run deploy $BACKEND_SERVICE_NAME \
  --image gcr.io/$GCP_PROJECT_ID/$BACKEND_SERVICE_NAME:latest \
  --platform managed \
  --region $GCP_REGION \
  --project $GCP_PROJECT_ID \
  --allow-unauthenticated

# Get the backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME --platform managed --region $GCP_REGION --project $GCP_PROJECT_ID --format 'value(status.url)')

echo "Backend deployed to: $BACKEND_URL"

# --- Frontend Deployment ---
echo "Deploying frontend..."

# Build the Docker image, passing the backend URL as a build argument
docker build \
  --build-arg REACT_APP_BACKEND_URL=$BACKEND_URL \
  -t gcr.io/$GCP_PROJECT_ID/$FRONTEND_SERVICE_NAME:latest ./front

# Push the image to Google Container Registry
docker push gcr.io/$GCP_PROJECT_ID/$FRONTEND_SERVICE_NAME:latest

# Deploy to Cloud Run
gcloud run deploy $FRONTEND_SERVICE_NAME \
  --image gcr.io/$GCP_PROJECT_ID/$FRONTEND_SERVICE_NAME:latest \
  --platform managed \
  --region $GCP_REGION \
  --project $GCP_PROJECT_ID \
  --allow-unauthenticated

echo "Frontend deployed!"