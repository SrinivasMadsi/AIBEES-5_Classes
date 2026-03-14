# =============================================================================
# config.py  —  Central configuration for the Enterprise RAG Pipeline
# Edit this file before running any pipeline step.
# =============================================================================

# ── GCP Project ───────────────────────────────────────────────────────────────
PROJECT_ID  = "project-b629d2c5-6ec0-4b7d-b32"  # Replace with your GCP Project ID
REGION      = "us-central1"

# ── GCS Buckets ───────────────────────────────────────────────────────────────
SOURCE_BUCKET   = "aib-raw-pdfs"          # bucket containing raw PDF files
PDF_PREFIX      = "pdfs/"                  # folder inside SOURCE_BUCKET
EMBED_BUCKET    = "aib-embeddings-0926"   # bucket for embedding artefacts
EMBED_BUCKET_URI = f"gs://{EMBED_BUCKET}"

# ── Embedding Model ───────────────────────────────────────────────────────────
# gemini-embedding-001 replaces deprecated text-embedding-004
EMBEDDING_MODEL = "gemini-embedding-001"
DIMENSIONS      = 3072   # default for gemini-embedding-001;

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE    = 1000
CHUNK_OVERLAP = 200

# ── Vertex AI Vector Search ───────────────────────────────────────────────────
INDEX_DISPLAY_NAME  = "rag_vind_0926"
DEPLOYED_INDEX_ID   = "rag_vind_0926_de"

# ── LLM ───────────────────────────────────────────────────────────────────────
LLM_MODEL         = "gemini-2.5-pro"
LLM_TEMPERATURE   = 0.2
LLM_MAX_TOKENS    = 1024
RETRIEVER_TOP_K   = 5

# ── Tracker (incremental ingestion state) ────────────────────────────────────
TRACKER_BLOB = "metadata/ingested_files.json"

# ── Local state file (written by step_02, read by step_03 / step_04) ─────────
RAG_CONFIG_FILE = ".rag_config.json"
