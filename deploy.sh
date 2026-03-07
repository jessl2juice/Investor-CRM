#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# BetterMind CRM — Cloud Run Deploy Script
# ============================================================
# Usage: ./deploy.sh [PROJECT_ID] [REGION]
# Example: ./deploy.sh bettermind-prod us-west1
# ============================================================

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${2:-us-west1}"
SERVICE_NAME="bettermind-crm"
CLOUD_SQL_INSTANCE="${CLOUD_SQL_INSTANCE:-bettermind-crm-db}"

# Load .env file if present
if [ -f .env ]; then
  set -a; source .env; set +a
fi

# Database credentials (set these in .env or export before running)
DB_USER="${DB_USER:?'DB_USER not set. Create a .env file or export DB_USER.'}"
DB_PASS="${DB_PASS:?'DB_PASS not set. Create a .env file or export DB_PASS.'}"
DB_NAME="${DB_NAME:?'DB_NAME not set. Create a .env file or export DB_NAME.'}"
TOKEN_SECRET="${TOKEN_SECRET:?'TOKEN_SECRET not set. Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"'}"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ No GCP project set. Usage: ./deploy.sh PROJECT_ID [REGION]"
  echo "   Or run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

echo ""
echo "🧠 BetterMind CRM — Deploying to Cloud Run"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Project:  $PROJECT_ID"
echo "  Region:   $REGION"
echo "  Service:  $SERVICE_NAME"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  --quiet

INSTANCE_CONN="${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE}"

# Deploy to Cloud Run (source-based deploy — no local Docker needed)
echo ""
echo "🚀 Deploying to Cloud Run with Cloud SQL..."
echo "   Instance: ${INSTANCE_CONN}"
echo "   (This uses Cloud Build — no local Docker required)"
echo ""

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --port 8080 \
  --add-cloudsql-instances "$INSTANCE_CONN" \
  --set-env-vars "INSTANCE_CONNECTION_NAME=${INSTANCE_CONN},DB_USER=${DB_USER},DB_PASS=${DB_PASS},DB_NAME=${DB_NAME},TOKEN_SECRET=${TOKEN_SECRET}" \
  --quiet

# Get the URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --format='value(status.url)')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ BetterMind CRM deployed successfully!"
echo ""
echo "   🌐 URL: $SERVICE_URL"
echo ""
echo "   API:  $SERVICE_URL/api/contacts"
echo "   Docs: $SERVICE_URL/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
