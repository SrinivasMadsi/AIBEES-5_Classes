#!/bin/bash
# =============================================================================
# deploy_ui.sh — Build, push and deploy AI Bees Healthcare Bot UI to Cloud Run
# Usage: ./deploy_ui.sh <image_name>:<version> <api_url>
# Example:
#   ./deploy_ui.sh medical_ui:v1 https://rag-api-xxx-uc.a.run.app
# =============================================================================

set -e

# ── Input validation ──────────────────────────────────────────────────────────
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "❌ Error: Missing arguments."
  echo "   Usage: ./deploy_ui.sh <image_name>:<version> <api_url>"
  echo "   Example:"
  echo "     ./deploy_ui.sh medical_ui:v1 https://rag-api-xxx-uc.a.run.app"
  exit 1
fi

IMAGE_INPUT="$1"
API_URL="$2"

IMAGE_NAME="${IMAGE_INPUT%%:*}"
IMAGE_VERSION="${IMAGE_INPUT##*:}"

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID="project-b629d2c5-6ec0-4b7d-b32"
REGION="us-central1"
REPO="aibees5"
SERVICE_NAME="medical-ui"
REGISTRY="${REGION}-docker.pkg.dev"
FULL_IMAGE="${REGISTRY}/${PROJECT_ID}/${REPO}/${IMAGE_NAME}:${IMAGE_VERSION}"

# ── Summary ───────────────────────────────────────────────────────────────────
echo "============================================="
echo "  AI Bees Healthcare Bot — UI Deployment"
echo "============================================="
echo "  Image      : ${FULL_IMAGE}"
echo "  Service    : ${SERVICE_NAME}"
echo "  API URL    : ${API_URL}"
echo "============================================="
echo ""

# ── Step 1: Build ─────────────────────────────────────────────────────────────
echo "🔨 [1/4] Building Docker image..."
docker build -t "${IMAGE_NAME}:${IMAGE_VERSION}" .
echo "✅ Build complete."
echo ""

# ── Step 2: Tag ───────────────────────────────────────────────────────────────
echo "🏷️  [2/4] Tagging image..."
docker tag "${IMAGE_NAME}:${IMAGE_VERSION}" "${FULL_IMAGE}"
echo "✅ Tagged: ${FULL_IMAGE}"
echo ""

# ── Step 3: Push ──────────────────────────────────────────────────────────────
echo "📤 [3/4] Pushing to Artifact Registry..."
gcloud auth configure-docker "${REGISTRY}" --quiet
docker push "${FULL_IMAGE}"
echo "✅ Pushed."
echo ""

# ── Step 4: Deploy to Cloud Run with API URL as env var ───────────────────────
echo "🚀 [4/4] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${FULL_IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 3 \
  --allow-unauthenticated \
  --set-env-vars="API_URL=${API_URL}" \
  --quiet
echo "✅ Deployment complete."
echo ""

# ── Output ────────────────────────────────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format "value(status.url)")

echo "============================================="
echo "  ✅ AI Bees Healthcare Bot Deployed!"
echo "============================================="
echo "  UI URL   : ${SERVICE_URL}"
echo "  API URL  : ${API_URL}"
echo ""
echo "  Open in browser: ${SERVICE_URL}"
echo "============================================="