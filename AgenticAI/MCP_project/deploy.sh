#!/bin/bash
# ============================================================
#  IRROPS Platform — Cloud Run Deployment Script (Mac/Linux)
#  Deploys all 4 services to Google Cloud Run
# ============================================================

set -e

# ── Config — edit these ──────────────────────────────────────
PROJECT_ID=${GCP_PROJECT_ID:-"your-gcp-project-id"}
REGION="us-central1"
REPO="irrops-platform"
GEMINI_MODEL="gemini-2.5-pro-preview-03-25"
# ─────────────────────────────────────────────────────────────

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"

echo "🚀 Deploying IRROPS Platform to Cloud Run"
echo "   Project : $PROJECT_ID"
echo "   Region  : $REGION"
echo "   Model   : $GEMINI_MODEL"
echo ""

# Enable APIs
echo "📦 Enabling GCP APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  pubsub.googleapis.com \
  bigquery.googleapis.com \
  aiplatform.googleapis.com \
  --project=$PROJECT_ID

# Create Artifact Registry repo
echo "🗄️  Creating Artifact Registry..."
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --project=$PROJECT_ID 2>/dev/null || echo "  (already exists)"

gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Create Pub/Sub topic
echo "📨 Creating Pub/Sub topic..."
gcloud pubsub topics create irrops-events --project=$PROJECT_ID 2>/dev/null || true

# Create BigQuery dataset and table
echo "📊 Creating BigQuery resources..."
bq --project_id=$PROJECT_ID mk --dataset --location=US irrops_audit 2>/dev/null || true
bq --project_id=$PROJECT_ID mk --table irrops_audit.audit_log \
  action_id:STRING,event_id:STRING,flight:STRING,agent:STRING,\
  tool_called:STRING,proposed_action:STRING,confidence:FLOAT,\
  status:STRING,approved_by:STRING,regulatory_impact:BOOLEAN,\
  assessed_at:TIMESTAMP,notes:STRING 2>/dev/null || true

# Deploy function
deploy_service() {
  local NAME=$1
  local DIR=$2
  local PORT=$3
  local EXTRA_ENV=$4

  echo ""
  echo "🔨 Building $NAME..."
  docker build -t ${REGISTRY}/${NAME}:latest ${DIR}
  docker push ${REGISTRY}/${NAME}:latest

  echo "☁️  Deploying $NAME..."
  gcloud run deploy $NAME \
    --image=${REGISTRY}/${NAME}:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --port=$PORT \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION},GEMINI_MODEL=${GEMINI_MODEL},${EXTRA_ENV}" \
    --project=$PROJECT_ID

  URL=$(gcloud run services describe $NAME \
    --region=$REGION --project=$PROJECT_ID \
    --format="value(status.url)")
  echo "   ✅ $NAME → $URL"
  echo $URL
}

# Deploy all 3 MCP backend services
ANOMALY_URL=$(deploy_service "irrops-anomaly-detector" "services/anomaly-detector" "8080" "PUBSUB_TOPIC=irrops-events")
RESOLUTION_URL=$(deploy_service "irrops-resolution-agent" "services/resolution-agent" "8081" "")
AUDIT_URL=$(deploy_service "irrops-audit-service" "services/audit-service" "8082" "BQ_DATASET=irrops_audit,BQ_TABLE=audit_log")

# Deploy React UI
echo ""
echo "🎨 Building React UI..."
cd frontend

cat > .env.production <<EOF
REACT_APP_ANOMALY_URL=${ANOMALY_URL}
REACT_APP_RESOLUTION_URL=${RESOLUTION_URL}
REACT_APP_AUDIT_URL=${AUDIT_URL}
EOF

npm install --legacy-peer-deps --silent
npm install ajv@^8 --legacy-peer-deps --silent
npm run build

cat > Dockerfile <<'EOF'
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps --silent
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

cat > nginx.conf <<'EOF'
server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;
  location / { try_files $uri $uri/ /index.html; }
}
EOF

docker build -t ${REGISTRY}/irrops-ui:latest .
docker push ${REGISTRY}/irrops-ui:latest

UI_URL=$(gcloud run deploy irrops-ui \
  --image=${REGISTRY}/irrops-ui:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --port=80 \
  --memory=512Mi \
  --project=$PROJECT_ID \
  --format="value(status.url)")

cd ..

# Summary
echo ""
echo "════════════════════════════════════════════════════"
echo "  ✅ IRROPS Platform Deployed Successfully"
echo "════════════════════════════════════════════════════"
echo ""
echo "  🌐 UI:                $UI_URL"
echo "  🔍 Anomaly Detector:  $ANOMALY_URL"
echo "  🤖 Resolution Agent:  $RESOLUTION_URL"
echo "  📋 Audit Service:     $AUDIT_URL"
echo ""
echo "  Health checks:"
echo "  curl $ANOMALY_URL/health"
echo "  curl $RESOLUTION_URL/health"
echo "  curl $AUDIT_URL/health"
echo ""
