#!/usr/bin/env python3
"""
app.py
──────
Streamlit UI for the Incremental RAG Pipeline — AIBees Edition.

Wraps the existing step_*.py logic without modifying it:
  • Step 1 — GCS Bucket Setup      (step_01_setup_gcs)
  • Step 2 — Create & Deploy Index  (step_02_create_index)
  • Step 3 — Ingest PDFs            (step_03_ingest)
  • Step 4 — Query the RAG pipeline (step_04_query)

Run:
    streamlit run app.py
"""

import json
import logging
import os
from io import StringIO
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ── Load .env ──────────────────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="AIBees RAG Pipeline",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── AIBees SVG Logo (inline — no external file needed) ────────────────────────
AIBEES_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 44" width="180" height="44">
  <!-- Hexagon honeycomb icon -->
  <polygon points="18,4 30,4 36,14 30,24 18,24 12,14"
           fill="#f59e0b" stroke="#d97706" stroke-width="1.5"/>
  <polygon points="18,4 30,4 36,14 30,24 18,24 12,14"
           fill="none" stroke="#fbbf24" stroke-width="0.5" transform="scale(0.7) translate(7.7,6)"/>
  <!-- Bee body stripes -->
  <ellipse cx="24" cy="14" rx="5" ry="7" fill="#3b1f0a"/>
  <rect x="19.5" y="10" width="9" height="2" rx="1" fill="#f59e0b"/>
  <rect x="19.5" y="13.5" width="9" height="2" rx="1" fill="#f59e0b"/>
  <!-- Wings -->
  <ellipse cx="18" cy="11" rx="4" ry="2.5" fill="#fed7aa" opacity="0.85"
           transform="rotate(-20 18 11)"/>
  <ellipse cx="30" cy="11" rx="4" ry="2.5" fill="#fed7aa" opacity="0.85"
           transform="rotate(20 30 11)"/>
  <!-- AIBees text -->
  <text x="46" y="19" font-family="'IBM Plex Mono', monospace" font-size="16"
        font-weight="700" fill="#f59e0b" letter-spacing="-0.5">AI</text>
  <text x="66" y="19" font-family="'IBM Plex Mono', monospace" font-size="16"
        font-weight="700" fill="#fff7ed" letter-spacing="-0.5">Bees</text>
  <!-- Tagline — fits within 180px viewBox -->
  <text x="46" y="33" font-family="'IBM Plex Sans', sans-serif" font-size="7"
        fill="#c2853a" letter-spacing="0.07em">RAG  •  VERTEX AI</text>
</svg>
"""

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #2d0f06;
    border-right: 2px solid #7c2d12;
}
section[data-testid="stSidebar"] * { color: #fed7aa !important; }
section[data-testid="stSidebar"] hr { border-color: #7c2d12 !important; }

/* ── Main area ── */
.main .block-container { padding-top: 1.5rem; max-width: 900px; }

/* ── Page title ── */
.rag-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.5rem; font-weight: 600; color: #431407;
    border-left: 4px solid #ea580c;
    padding-left: 0.75rem; margin-bottom: 0.2rem;
}
.rag-subtitle {
    font-size: 0.82rem; color: #9a3412;
    margin-left: 1.1rem; margin-bottom: 1.75rem;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Step badge ── */
.step-badge {
    display: inline-block; background: #7c2d12; color: #fed7aa;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
    font-weight: 600; letter-spacing: 0.14em;
    padding: 3px 10px; border-radius: 2px; margin-bottom: 0.5rem;
}

/* ── Cards ── */
.info-card {
    background: #fff7ed; border: 1px solid #fed7aa;
    border-left: 3px solid #ea580c; border-radius: 4px;
    padding: 0.85rem 1rem; margin-bottom: 1rem;
    font-size: 0.88rem; color: #431407;
}
.warn-card {
    background: #fef2f2; border: 1px solid #fecaca;
    border-left: 3px solid #ef4444; border-radius: 4px;
    padding: 0.85rem 1rem; margin-bottom: 1rem;
    font-size: 0.88rem; color: #7f1d1d;
}
.success-card {
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-left: 3px solid #22c55e; border-radius: 4px;
    padding: 0.85rem 1rem; margin-bottom: 1rem;
    font-size: 0.88rem; color: #14532d;
}
.error-card {
    background: #fef2f2; border: 1px solid #fecaca;
    border-left: 3px solid #ef4444; border-radius: 4px;
    padding: 0.85rem 1rem; margin-bottom: 1rem;
    font-size: 0.88rem; color: #7f1d1d;
}
.neutral-card {
    background: #fff7ed; border: 1px solid #fed7aa;
    border-left: 3px solid #9a3412; border-radius: 4px;
    padding: 0.85rem 1rem; margin-bottom: 1rem;
    font-size: 0.88rem; color: #431407;
}

/* ── Answer box ── */
.answer-box {
    background: #3b1f0a; color: #fed7aa;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.95rem; line-height: 1.75;
    padding: 1.25rem 1.5rem; border-radius: 6px;
    border-left: 3px solid #f59e0b; margin: 0.75rem 0;
}

/* ── Source pill ── */
.source-pill {
    display: inline-block; background: #7c2d12; color: #fed7aa;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem;
    padding: 2px 8px; border-radius: 2px; margin: 2px 3px 2px 0;
}

/* ── Log output ── */
.log-output {
    background: #1c0a02; color: #4ade80;
    font-family: 'IBM Plex Mono', monospace; font-size: 0.73rem;
    padding: 1rem; border-radius: 4px; max-height: 280px;
    overflow-y: auto; white-space: pre-wrap; line-height: 1.6;
}

/* ── Status chips ── */
.chip-ok   { color: #22c55e; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; }
.chip-warn { color: #f59e0b; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; }

/* ── Buttons ── */
.stButton > button {
    background: #7c2d12; color: #fed7aa;
    border: 1px solid #ea580c; border-radius: 3px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem; letter-spacing: 0.05em;
    padding: 0.45rem 1.2rem; transition: all 0.15s;
}
.stButton > button:hover {
    background: #ea580c; color: #fff7ed;
    border-color: #ea580c;
}

/* ── Overview tile ── */
.pipeline-tile {
    background: #3b1f0a; border: 1px solid #7c2d12;
    border-top: 3px solid #f59e0b;
    border-radius: 4px; padding: 1rem;
    text-align: center; height: 155px;
}
.tile-num   { font-family:'IBM Plex Mono',monospace; font-size:1.5rem; font-weight:700; color:#f59e0b; }
.tile-title { font-weight:600; color:#fed7aa; margin:4px 0 6px; font-size:0.9rem; }
.tile-desc  { font-size:0.75rem; color:#c2853a; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _rag_config_exists() -> bool:
    try:
        from config import RAG_CONFIG_FILE
        return Path(RAG_CONFIG_FILE).exists()
    except Exception:
        return False


def _load_rag_config() -> dict:
    try:
        from config import RAG_CONFIG_FILE
        with open(RAG_CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _capture_logs(fn, *args, **kwargs):
    """
    Run fn(*args, **kwargs) while capturing all log output to a string.
    Returns (result, log_text).

    WHY: Streamlit reruns the script on every interaction. Without capturing
    logs here, log output would only appear in the terminal, not in the UI.
    """
    log_stream = StringIO()
    handler    = logging.StreamHandler(log_stream)
    handler.setFormatter(
        logging.Formatter("%(asctime)s  [%(levelname)s]  %(message)s", "%H:%M:%S")
    )
    root = logging.getLogger()
    root.addHandler(handler)
    result = None
    try:
        result = fn(*args, **kwargs)
    except SystemExit:
        pass   # step scripts call sys.exit(0) on safe-skip paths
    except Exception as exc:
        log_stream.write(f"\nERROR: {exc}\n")
    finally:
        root.removeHandler(handler)
    return result, log_stream.getvalue()


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:

    # AIBees Logo
    st.markdown(AIBEES_LOGO_SVG, unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["Overview",
         "Step 1 — GCS Setup",
         "Step 2 — Create Index",
         "Step 3 — Ingest PDFs",
         "Step 4 — Query"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Live index status
    cfg_exists = _rag_config_exists()
    if cfg_exists:
        cfg = _load_rag_config()
        st.markdown('<span class="chip-ok">● index ready</span>', unsafe_allow_html=True)
        st.caption(f"Index: `{cfg.get('index_id','—')[:20]}…`")
    else:
        st.markdown('<span class="chip-warn">● index not created</span>', unsafe_allow_html=True)
        st.caption("Complete Step 2 first.")

    st.markdown("---")
    st.caption("Local VS Code → GCP Vertex AI")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Overview
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":

    # Header with logo + title side by side
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.markdown(
            "<div style='background:#3b1f0a;border:1px solid #7c2d12;border-radius:8px;"
            "padding:12px 10px;text-align:center;margin-top:4px;"
            "overflow:hidden;line-height:1;'>"
            + AIBEES_LOGO_SVG +
            "</div>",
            unsafe_allow_html=True,
        )
    with col_title:
        st.markdown('<div class="rag-title">Incremental RAG Pipeline</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="rag-subtitle">Google Vertex AI Vector Search + Gemini</div>',
                    unsafe_allow_html=True)

    # Pipeline tiles
    c1, c2, c3, c4 = st.columns(4)
    for col, num, title, desc in zip(
        [c1, c2, c3, c4],
        ["01", "02", "03", "04"],
        ["GCS Setup", "Create Index", "Ingest PDFs", "Query"],
        [
            "Create source + embed buckets in GCS.",
            "Provision Vertex AI Vector Search index + endpoint.",
            "Upload PDFs → chunk → embed → upsert.",
            "Ask questions answered by Gemini.",
        ],
    ):
        with col:
            st.markdown(
                f'<div class="pipeline-tile">'
                f'<div class="tile-num">{num}</div>'
                f'<div class="tile-title">{title}</div>'
                f'<div class="tile-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="info-card">🐝 <b>Incremental RAG</b> — each new PDF is embedded and '
        '<i>upserted</i> into the index without rebuilding it. This works because the index '
        'is created with <code>STREAM_UPDATE</code> mode in Vertex AI Vector Search. '
        'Old documents stay; only new ones are added.</div>',
        unsafe_allow_html=True,
    )

    # Config snapshot
    st.markdown("#### Config Snapshot")
    try:
        from config import (PROJECT_ID, REGION, SOURCE_BUCKET,
                            EMBED_BUCKET, DIMENSIONS, CHUNK_SIZE)
        for label, val in {
            "Project ID":            PROJECT_ID,
            "Region":                REGION,
            "Source Bucket":         f"gs://{SOURCE_BUCKET}",
            "Embed Bucket":          f"gs://{EMBED_BUCKET}",
            "Embedding Dimensions":  str(DIMENSIONS),
            "Chunk Size (tokens)":   str(CHUNK_SIZE),
        }.items():
            ck, cv = st.columns([1, 2])
            ck.caption(label)
            cv.code(val, language=None)
    except ImportError:
        st.warning("config.py not found in the project directory.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Step 1 — GCS Setup
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Step 1 — GCS Setup":
    st.markdown('<div class="step-badge">STEP 01</div>', unsafe_allow_html=True)
    st.markdown("## GCS Bucket Setup")

    st.markdown(
        '<div class="info-card">'
        'Creates two GCS buckets:<br>'
        '&nbsp;&nbsp;<b>SOURCE_BUCKET</b> — raw PDF uploads<br>'
        '&nbsp;&nbsp;<b>EMBED_BUCKET</b> — Vector Search embedding artefacts<br><br>'
        'Safe to re-run; existing buckets are skipped, not overwritten.</div>',
        unsafe_allow_html=True,
    )

    try:
        from config import SOURCE_BUCKET, EMBED_BUCKET, PROJECT_ID, REGION, PDF_PREFIX
    except ImportError:
        st.error("config.py not found.")
        st.stop()

    c1, c2 = st.columns(2)
    c1.metric("Source Bucket", f"gs://{SOURCE_BUCKET}")
    c2.metric("Embed Bucket",  f"gs://{EMBED_BUCKET}")

    st.markdown("---")
    if st.button("▶  Run GCS Setup"):
        with st.spinner("Creating buckets…"):
            import google.auth
            from google.cloud import storage as gcs
            from step_01_setup_gcs import create_bucket, create_placeholder_prefix

            def _run():
                credentials, _ = google.auth.default()
                client = gcs.Client(project=PROJECT_ID, credentials=credentials)
                create_bucket(client, SOURCE_BUCKET, REGION)
                create_placeholder_prefix(client, SOURCE_BUCKET, PDF_PREFIX)
                create_bucket(client, EMBED_BUCKET, REGION)

            _, logs = _capture_logs(_run)

        st.markdown('<div class="success-card">✓ Bucket setup complete.</div>',
                    unsafe_allow_html=True)
        if logs:
            st.markdown("**Logs**")
            st.markdown(f'<div class="log-output">{logs}</div>', unsafe_allow_html=True)
        st.markdown('<div class="neutral-card">Next → <b>Step 2: Create Index</b></div>',
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Step 2 — Create Index
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Step 2 — Create Index":
    st.markdown('<div class="step-badge">STEP 02</div>', unsafe_allow_html=True)
    st.markdown("## Create & Deploy Vector Search Index")

    st.markdown(
        '<div class="warn-card">'
        '⚠ <b>Takes ~30–45 minutes.</b> Run once. '
        'Re-running skips automatically if the index already exists.</div>',
        unsafe_allow_html=True,
    )

    try:
        from config import DIMENSIONS, INDEX_DISPLAY_NAME
    except ImportError:
        st.error("config.py not found.")
        st.stop()

    c1, c2, c3 = st.columns(3)
    c1.metric("Dimensions",  DIMENSIONS)
    c2.metric("Index Name",  INDEX_DISPLAY_NAME)
    c3.metric("Update Mode", "STREAM_UPDATE")

    if _rag_config_exists():
        st.markdown('<div class="success-card">✓ Index already created and deployed.</div>',
                    unsafe_allow_html=True)
        st.json(_load_rag_config())

        st.markdown("---")
        # Allow reset if index was manually deleted from GCP Console
        st.warning("If you deleted the index from GCP Console, reset below to recreate it.")
        if st.button("🗑  Reset config and recreate index"):
            from config import RAG_CONFIG_FILE
            Path(RAG_CONFIG_FILE).unlink(missing_ok=True)
            st.success("✓ .rag_config.json deleted. Refreshing…")
            st.rerun()

    else:
        st.markdown(
            '<div class="info-card">'
            'Creates a <b>Tree-AH (ScaNN)</b> index with <b>DOT_PRODUCT_DISTANCE</b> '
            'and deploys it to a public endpoint. IDs are saved to '
            '<code>.rag_config.json</code> for use by Steps 3 and 4.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        if st.button("▶  Create & Deploy Index"):
            with st.spinner("Creating index… keep this window open (30–45 min)."):
                from google.cloud import aiplatform
                from config import PROJECT_ID, REGION, EMBED_BUCKET_URI
                from step_02_create_index import (
                    create_index, create_endpoint, deploy_index, save_config
                )

                def _run():
                    aiplatform.init(project=PROJECT_ID, location=REGION,
                                    staging_bucket=EMBED_BUCKET_URI)
                    idx = create_index()
                    ep  = create_endpoint()
                    ep  = deploy_index(ep, idx)
                    save_config(idx, ep)

                _, logs = _capture_logs(_run)

            if _rag_config_exists():
                st.markdown('<div class="success-card">✓ Index created and deployed.</div>',
                            unsafe_allow_html=True)
                st.json(_load_rag_config())
            else:
                st.markdown(
                    '<div class="error-card">✗ Creation may have failed — check logs below.</div>',
                    unsafe_allow_html=True,
                )

            if logs:
                st.markdown("**Logs**")
                st.markdown(f'<div class="log-output">{logs}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Step 3 — Ingest PDFs
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Step 3 — Ingest PDFs":
    st.markdown('<div class="step-badge">STEP 03</div>', unsafe_allow_html=True)
    st.markdown("## Ingest PDFs into Vector Search")

    if not _rag_config_exists():
        st.markdown('<div class="error-card">Index not found. Complete Step 2 first.</div>',
                    unsafe_allow_html=True)
        st.stop()

    # ── Upload ──
    st.markdown("#### 1 — Upload PDFs to GCS")
    st.markdown(
        '<div class="info-card">'
        'Files are uploaded to your GCS <b>SOURCE_BUCKET</b>, then chunked, '
        'embedded with <code>gemini-embedding-001</code>, and upserted into '
        'Vertex AI Vector Search.</div>',
        unsafe_allow_html=True,
    )
    uploaded_files = st.file_uploader(
        "Select PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        for f in uploaded_files:
            st.caption(f"📄 {f.name}  ({f.size / 1024:.1f} KB)")

    # ── Mode ──
    st.markdown("#### 2 — Ingest Mode")
    mode = st.radio(
        "Mode",
        ["full", "incremental"],
        horizontal=True,
        help="full = all PDFs | incremental = only new PDFs not yet in the tracker",
    )
    st.markdown(
        '<div class="neutral-card">'
        '<b>full</b> — re-ingests every PDF in the bucket prefix.<br>'
        '<b>incremental</b> — skips PDFs already recorded in the GCS tracker. '
        'Use this when adding new documents to an existing index.</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    if st.button("▶  Start Ingestion"):
        if not uploaded_files:
            st.warning("Upload at least one PDF before ingesting.")
            st.stop()

        # Upload to GCS
        with st.spinner("Uploading PDFs to GCS…"):
            import google.auth
            from google.cloud import storage as gcs
            from config import SOURCE_BUCKET, PDF_PREFIX, PROJECT_ID

            credentials, _ = google.auth.default()
            client = gcs.Client(project=PROJECT_ID, credentials=credentials)
            bucket = client.bucket(SOURCE_BUCKET)
            for uf in uploaded_files:
                blob = bucket.blob(f"{PDF_PREFIX}/{uf.name}")
                blob.upload_from_file(uf, content_type="application/pdf")

        st.success(f"✓ {len(uploaded_files)} file(s) uploaded to "
                   f"gs://{SOURCE_BUCKET}/{PDF_PREFIX}/")

        # Ingest
        with st.spinner(f"Ingesting ({mode} mode)… embedding may take a few minutes."):
            from config import PDF_PREFIX
            from step_03_ingest import ingest

            _, logs = _capture_logs(
                ingest,
                prefix=PDF_PREFIX,
                incremental=(mode == "incremental"),
            )

        st.markdown('<div class="success-card">✓ Ingestion complete.</div>',
                    unsafe_allow_html=True)

        # Quick metrics
        if logs:
            upserted_lines = [l for l in logs.splitlines() if "vectors upserted" in l]
            total = sum(
                int(l.split("→")[1].strip().split()[0])
                for l in upserted_lines if "→" in l
            ) if upserted_lines else 0

            if total:
                c1, c2 = st.columns(2)
                c1.metric("Files Uploaded",   len(uploaded_files))
                c2.metric("Chunks Upserted",  total)

            st.markdown("**Logs**")
            st.markdown(f'<div class="log-output">{logs}</div>', unsafe_allow_html=True)

        st.markdown('<div class="neutral-card">Next → <b>Step 4: Query</b></div>',
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Step 4 — Query
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Step 4 — Query":
    st.markdown('<div class="step-badge">STEP 04</div>', unsafe_allow_html=True)
    st.markdown("## Query the RAG Pipeline")

    if not _rag_config_exists():
        st.markdown('<div class="error-card">Index not found. Complete Steps 1–3 first.</div>',
                    unsafe_allow_html=True)
        st.stop()

    @st.cache_resource(show_spinner="Connecting to Vector Search and loading LLM…")
    def get_chain(top_k: int):
        """
        WHY @st.cache_resource?
        ───────────────────────
        Streamlit reruns the entire script on every user interaction
        (button click, slider move, text input). Without this decorator,
        the RAG chain — which connects to Vertex AI Vector Search and
        loads the LLM — would be rebuilt from scratch on every interaction
        (~10 seconds each time).

        @st.cache_resource tells Streamlit: build this once, store it in
        memory, and reuse it for all subsequent reruns. It only rebuilds
        when the function arguments change (i.e. when top_k changes).
        """
        from google.cloud import aiplatform
        from config import PROJECT_ID, REGION, EMBED_BUCKET_URI
        from step_04_query import build_chain, load_config

        aiplatform.init(project=PROJECT_ID, location=REGION,
                        staging_bucket=EMBED_BUCKET_URI)
        return build_chain(load_config(), top_k=top_k)

    # Controls
    top_k   = st.slider("Chunks to retrieve (top-k)", 1, 10, 5)
    verbose = st.checkbox("Show retrieved source chunks")

    # Session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.markdown("---")

    question = st.text_input(
        "Ask a question",
        placeholder="Ask about your PDF contents",
        label_visibility="collapsed",
    )

    col_ask, col_clear = st.columns([1, 5])
    ask_clicked   = col_ask.button("Ask 🐝")
    clear_clicked = col_clear.button("Clear history")

    if clear_clicked:
        st.session_state.chat_history = []
        st.rerun()

    if ask_clicked and question.strip():
        chain = get_chain(top_k)
        with st.spinner("Retrieving chunks and generating answer…"):
            try:
                result = chain(question.strip())
                st.session_state.chat_history.append({
                    "question": question.strip(),
                    "answer":   result.get("answer", "—"),
                    "sources":  result.get("sources", []),
                })
            except Exception as exc:
                st.markdown(
                    f'<div class="error-card">✗ Query failed: {exc}</div>',
                    unsafe_allow_html=True,
                )

    # Render chat history newest-first
    for turn in reversed(st.session_state.chat_history):
        st.markdown(f"**Q:** {turn['question']}")
        st.markdown(
            f'<div class="answer-box">{turn["answer"]}</div>',
            unsafe_allow_html=True,
        )

        sources = turn.get("sources", [])
        if sources:
            seen, pills = set(), []
            for doc in sources:
                fname = doc.metadata.get("source_file", "unknown")
                page  = doc.metadata.get("page")
                key   = (fname, page)
                if key not in seen:
                    seen.add(key)
                    label = fname + (f" p.{page}" if page is not None else "")
                    pills.append(f'<span class="source-pill">📄 {label}</span>')
            st.markdown("Sources: " + "".join(pills), unsafe_allow_html=True)

            if verbose:
                with st.expander("Retrieved chunks"):
                    for i, doc in enumerate(sources, 1):
                        st.caption(f"Chunk {i} — {doc.metadata.get('source_file','?')}")
                        snippet = doc.page_content[:400]
                        st.text(snippet + ("…" if len(doc.page_content) > 400 else ""))

        st.markdown("---")