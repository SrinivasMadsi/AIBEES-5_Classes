#!/bin/bash
# =============================================================================
# deploy.sh — Build, push and deploy RAG API to Cloud Run
# Usage: ./deploy.sh <image_name>:<version>
# Example: ./deploy.sh rag_api_0320:v1
# =============================================================================

set -e  # Exit immediately on any error

# ── Input validation ──────────────────────────────────────────────────────────
if [ -z "$1" ]; then
  echo "❌ Error: No image name provided."
  echo "   Usage: ./deploy.sh <image_name>:<version>"
  echo "   Example: ./deploy.sh rag_api_0320:v1"
  exit 1
fi

IMAGE_INPUT="$1"

# Split input into name and version
IMAGE_NAME="${IMAGE_INPUT%%:*}"   # everything before ':'
IMAGE_VERSION="${IMAGE_INPUT##*:}" # everything after ':'

if [ "$IMAGE_NAME" = "$IMAGE_VERSION" ]; then
  echo "❌ Error: Please provide version tag in format <image_name>:<version>"
  echo "   Example: ./deploy.sh rag_api_0320:v1"
  exit 1
fi

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID="project-b629d2c5-6ec0-4b7d-b32"
REGION="us-central1"
REPO="aibees5"
SERVICE_NAME="rag-api-3"
REGISTRY="${REGION}-docker.pkg.dev"
FULL_IMAGE="${REGISTRY}/${PROJECT_ID}/${REPO}/${IMAGE_NAME}:${IMAGE_VERSION}"

# ── Summary ───────────────────────────────────────────────────────────────────
echo "============================================="
echo "  RAG API Deployment"
echo "============================================="
echo "  Image Name   : ${IMAGE_NAME}"
echo "  Version      : ${IMAGE_VERSION}"
echo "  Full Image   : ${FULL_IMAGE}"
echo "  Project      : ${PROJECT_ID}"
echo "  Region       : ${REGION}"
echo "  Service      : ${SERVICE_NAME}"
echo "============================================="
echo ""

# ── Step 1: Docker Build ──────────────────────────────────────────────────────
echo "🔨 [1/4] Building Docker image..."
docker build -t "${IMAGE_NAME}:${IMAGE_VERSION}" .
echo "✅ Docker build complete."
echo ""

# ── Step 2: Tag Image ─────────────────────────────────────────────────────────
echo "🏷️  [2/4] Tagging image for Artifact Registry..."
docker tag "${IMAGE_NAME}:${IMAGE_VERSION}" "${FULL_IMAGE}"
echo "✅ Tagged: ${FULL_IMAGE}"
echo ""

# ── Step 3: Push to Artifact Registry ────────────────────────────────────────
echo "📤 [3/4] Pushing image to Artifact Registry..."
gcloud auth configure-docker "${REGISTRY}" --quiet
docker push "${FULL_IMAGE}"
echo "✅ Image pushed to Artifact Registry."
echo ""

# ── Step 4: Deploy to Cloud Run ───────────────────────────────────────────────
echo " [4/4] Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${FULL_IMAGE}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 5 \
  --allow-unauthenticated \
  --quiet
echo "✅ Cloud Run deployment complete."
echo ""

# ── Output endpoint URL ───────────────────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format "value(status.url)")

echo "============================================="
echo "  ✅ Deployment Successful!"
echo "============================================="
echo "  Service URL : ${SERVICE_URL}"
echo ""
echo "  Sample CURL commands:"
echo ""
echo "  # Health check"
echo "  curl ${SERVICE_URL}/health"
echo ""
echo "  # Ask a question"
echo "  curl -X POST ${SERVICE_URL}/ask \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"query\": \"How should I treat fever?\"}'"
echo "============================================="
