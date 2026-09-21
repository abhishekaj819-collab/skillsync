# ==============================================================================
# Google Cloud Run Deployment Script (PowerShell) for SkillSetu
# Project: gen-lang-client-0304136646
# Features: --min-instances=1 (Zero Cold Starts), 2Gi RAM, 2 vCPU
# ==============================================================================

$ErrorActionPreference = "Stop"

$ServiceName = "skillsetu-backend"
$ProjectId   = "gen-lang-client-0304136646"
$Region      = "asia-south1"

Write-Host "=== 1. Ensuring Required GCP Services Are Enabled ===" -ForegroundColor Cyan
gcloud services enable `
  run.googleapis.com `
  cloudbuild.googleapis.com `
  artifactregistry.googleapis.com `
  --project=$ProjectId

Write-Host "=== 2. Deploying $ServiceName to Google Cloud Run ===" -ForegroundColor Cyan
gcloud run deploy $ServiceName `
  --source . `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --min-instances 1 `
  --max-instances 10 `
  --port 8080 `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --project $ProjectId

Write-Host "=== 3. Retrieving Deployed Service URL ===" -ForegroundColor Cyan
$ServiceUrl = gcloud run services describe $ServiceName `
  --platform managed `
  --region $Region `
  --project $ProjectId `
  --format="value(status.url)"

Write-Host "=========================================================" -ForegroundColor Green
Write-Host "Deployment successful!" -ForegroundColor Green
Write-Host "Cloud Run Service URL: $ServiceUrl" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
