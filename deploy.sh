#!/bin/bash

# Exit on error
set -e

# --- Configuration ---
# GCP Project ID and Region (replace with your values)
GCP_PROJECT_ID="your-gcp-project-id"
GCP_REGION="your-gcp-region"

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
  --allow-unauthenticated

# Get the backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME --platform managed --region $GCP_REGION --format 'value(status.url)')

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
  --allow-unauthenticated

echo "Frontend deployed!"
