#!/usr/bin/env bash
# ==============================================================================
# Google Cloud Run Deployment Script for SkillSetu
# Project: gen-lang-client-0304136646
# Features: --min-instances=1 (Zero Cold Starts), 2Gi RAM, 2 vCPU
# ==============================================================================

set -euo pipefail

SERVICE_NAME="skillsetu-backend"
PROJECT_ID="gen-lang-client-0304136646"
REGION="asia-south1"

echo "=== 1. Ensuring Required GCP Services Are Enabled ==="
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project="${PROJECT_ID}"

echo "=== 2. Deploying ${SERVICE_NAME} to Google Cloud Run ==="
gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10 \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --project "${PROJECT_ID}"

echo "=== 3. Retrieving Deployed Service URL ==="
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --platform managed \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format="value(status.url)")

echo "========================================================="
echo "Deployment successful!"
echo "Cloud Run Service URL: ${SERVICE_URL}"
echo "========================================================="
