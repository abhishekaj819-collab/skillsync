#!/usr/bin/env bash
# ==============================================================================
# SkillSetu Cloud SQL & IAM Least Privilege Provisioning Script
# Project: gen-lang-client-0304136646
# Engine: PostgreSQL 15 (Recommended for JSONB & Vector Telemetry)
# ==============================================================================

set -euo pipefail

PROJECT_ID="gen-lang-client-0304136646"
REGION="asia-south1"
INSTANCE_NAME="skillsetu-db-instance"
DATABASE_NAME="skillsetu_db"
DATABASE_USER="skillsetu_user"
SA_NAME="skillsetu-backend-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=== 1. Setting GCP Project ==="
gcloud config set project "${PROJECT_ID}"

echo "=== 2. Enabling Required Google Cloud APIs ==="
gcloud services enable \
  sqladmin.googleapis.com \
  iam.googleapis.com \
  accesscontextmanager.googleapis.com

echo "=== 3. Creating Service Account (Least Privilege) ==="
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --project="${PROJECT_ID}" \
    --display-name="SkillSetu Backend Cloud SQL Service Account" \
    --description="Dedicated service account with least privilege permissions for Cloud SQL access"
  echo "Service account created: ${SA_EMAIL}"
else
  echo "Service account ${SA_EMAIL} already exists."
fi

echo "=== 4. Binding Least-Privilege IAM Roles ==="
# Role 1: Cloud SQL Client (connect via Cloud SQL Python Connector / Proxy)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudsql.client" \
  --condition=None

# Role 2: Cloud SQL Instance User (IAM database authentication)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudsql.instanceUser" \
  --condition=None

echo "=== 5. Provisioning Cloud SQL Instance ==="
if ! gcloud sql instances describe "${INSTANCE_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud sql instances create "${INSTANCE_NAME}" \
    --project="${PROJECT_ID}" \
    --database-version="POSTGRES_15" \
    --tier="db-f1-micro" \
    --region="${REGION}" \
    --storage-size="10GB" \
    --storage-type="SSD" \
    --storage-auto-increase \
    --backup \
    --database-flags="cloudsql.iam_authentication=on"
  echo "Cloud SQL instance ${INSTANCE_NAME} created successfully."
else
  echo "Cloud SQL instance ${INSTANCE_NAME} already exists."
fi

echo "=== 6. Creating Database & Database User ==="
if ! gcloud sql databases describe "${DATABASE_NAME}" --instance="${INSTANCE_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud sql databases create "${DATABASE_NAME}" \
    --instance="${INSTANCE_NAME}" \
    --project="${PROJECT_ID}"
  echo "Database ${DATABASE_NAME} created."
else
  echo "Database ${DATABASE_NAME} already exists."
fi

# Add IAM database user for passwordless IAM authentication
gcloud sql users create "${SA_NAME}" \
  --instance="${INSTANCE_NAME}" \
  --project="${PROJECT_ID}" \
  --type="CLOUD_IAM_SERVICE_ACCOUNT" || true

echo "=== 7. Applying Principal Access Boundary (PAB) Policy ==="
# Note: PAB policies require Organization Administrator privileges.
if [ -f "infra/pab_policy.yaml" ]; then
  echo "Applying Principal Access Boundary policy..."
  gcloud alpha access-context-manager principal-access-boundary-policies create \
    --file="infra/pab_policy.yaml" || echo "PAB creation requires Organization Admin permissions; skipping if not in org."
fi

echo "=== Provisioning Complete ==="
echo "Connection Name: ${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
echo "Database: ${DATABASE_NAME}"
echo "Service Account: ${SA_EMAIL}"
