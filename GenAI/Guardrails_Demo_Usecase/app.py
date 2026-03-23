"""
RAG + PII Guardrails Demo — Enhanced Version
A Streamlit application for demonstrating PII exposure and redaction
in a Retrieval-Augmented Generation pipeline.
"""

import os
import hashlib
import logging
from typing import Optional

import streamlit as st
from guardrails import PIIGuardrail
from rag_system import RAGSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------
FAISS_INDEX_DIR = "faiss_index"
SHA1_HASH_LENGTH = 12
SUPPORTED_FILE_TYPES = ["pdf"]

SAMPLE_QUERIES = [
    "Share the SSN of a customer with a good credit score.",
    "What is the mobile phone number of Customer Profile #4?",
    "What is the account number of the first customer?",
    "List customers with a credit score above 800.",
    "What is the full legal name and date of birth of Customer Profile #4?",
]

# ------------------------------------------------------------------
# AIBees Brand Colors (mirrored from AIBees app)
# ------------------------------------------------------------------
BRAND_ORANGE  = "#E8500A"
BRAND_DARK    = "#3A3A3A"
BRAND_YELLOW  = "#F5C518"
BRAND_LIGHT   = "#FFF8F3"
BRAND_ORANGE2 = "#FF6B2B"

# ------------------------------------------------------------------
# Page Config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="PII Guardrails Demo",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Custom CSS — AIBees brand palette
# ------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Nunito', sans-serif;
    }}

    /* ── Main background ── */
    .stApp {{ background: {BRAND_LIGHT}; color: {BRAND_DARK}; }}

    /* ── Header card ── */
    .demo-header {{
        background: linear-gradient(135deg, {BRAND_DARK} 0%, #2a2a2a 100%);
        border: none;
        border-left: 5px solid {BRAND_ORANGE};
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 6px 24px rgba(0,0,0,0.18);
        display: flex;
        align-items: center;
        gap: 16px;
    }}
    .demo-header h1 {{
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        color: #ffffff;
    }}
    .demo-header h1 span {{ color: {BRAND_YELLOW}; }}
    .demo-header p  {{
        font-size: 0.88rem;
        color: #cccccc;
        margin: 4px 0 0;
    }}

    /* ── Status badges ── */
    .badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 700;
        font-family: 'Nunito', sans-serif;
        letter-spacing: .3px;
    }}
    .badge-on  {{
        background: #e6f9ee;
        color: #000000 !important;
        border: 1.5px solid #1a7a3a;
    }}
    .badge-off {{
        background: #fdecea;
        color:#000000 !important;
        border: 1.5px solid #c0392b;
    }}

    section[data-testid="stSidebar"] .badge-on,
    section[data-testid="stSidebar"] .badge-off {{
            color: #000000 !important;
    }}

    /* ── Metric cards ── */
    .metric-card {{
        background: white;
        border: 1.5px solid #f0e8e0;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }}
    .metric-card .value {{
        font-size: 1.8rem;
        font-weight: 800;
        color: {BRAND_ORANGE};
        font-family: 'Nunito', monospace;
    }}
    .metric-card .label {{
        font-size: 0.78rem;
        color: #888888;
        margin-top: 2px;
        font-weight: 600;
    }}

    /* ── Chat messages ── */
    .chat-user {{
        background: #fff3ec;
        border-left: 4px solid {BRAND_ORANGE};
        border-radius: 0 10px 10px 0;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 0.92rem;
        color: {BRAND_DARK};
    }}
    .chat-assistant {{
        background: white;
        border-left: 4px solid {BRAND_YELLOW};
        border-radius: 0 10px 10px 0;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 0.92rem;
        color: {BRAND_DARK};
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .chat-assistant.pii-redacted {{ border-left-color: {BRAND_ORANGE}; }}

    /* ── Redaction summary pill ── */
    .redact-pill {{
        display: inline-block;
        background: #fdecea;
        color: #c0392b;
        border: 1.5px solid #c0392b;
        border-radius: 20px;
        font-size: 0.75rem;
        padding: 3px 12px;
        margin-top: 6px;
        font-family: 'Nunito', sans-serif;
        font-weight: 700;
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(160deg, {BRAND_DARK} 0%, #1e1e1e 100%) !important;
        border-right: 3px solid {BRAND_ORANGE} !important;
    }}

    /* All sidebar text */
    section[data-testid="stSidebar"] * {{
        color: #f0f0f0 !important;
        font-family: 'Nunito', sans-serif !important;
    }}

    /* Sidebar headings */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {BRAND_YELLOW} !important;
        font-weight: 800 !important;
    }}

    section[data-testid="stSidebar"] hr {{
        border-color: {BRAND_ORANGE} !important;
        opacity: 0.4;
    }}

    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {{
        background: {BRAND_ORANGE} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        width: 100%;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: {BRAND_ORANGE2} !important;
    }}

    /* Sidebar toggle / metrics caption */
    section[data-testid="stSidebar"] .stMetric label,
    section[data-testid="stSidebar"] .stMetric div {{
        color: #f0f0f0 !important;
    }}

    /* Sidebar code snippets (filenames) */
    section[data-testid="stSidebar"] code {{
        background: rgba(245,197,24,0.20) !important;
        color: {BRAND_YELLOW} !important;
        border: 1px solid rgba(245,197,24,0.40) !important;
        border-radius: 5px !important;
        padding: 2px 7px !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
    }}

    /* ── File uploader in sidebar — white dropzone so text is always visible ── */
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] {{
        background: #ffffff !important;
        border: 2px dashed {BRAND_ORANGE} !important;
        border-radius: 10px !important;
        padding: 6px !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
        background: #ffffff !important;
        border-radius: 8px !important;
    }}

    /* "Drag and drop" text, "Limit X MB", file type labels — all dark */
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"],
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] *,
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] span,
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] p,
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] div,
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] small,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] span,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] p,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] div:not(button) {{
        color: {BRAND_DARK} !important;
        font-weight: 600 !important;
    }}

    /* "Browse files" button — yellow so it pops */
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {{
        background: {BRAND_ORANGE} !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button *,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] button * {{
        color: #ffffff !important;
    }}

    /* Uploaded filename + size shown after upload */
    section[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"],
    section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] *,
    section[data-testid="stSidebar"] [data-testid="stFileUploaderFileData"] * {{
        color: {BRAND_DARK} !important;
        font-weight: 600 !important;
    }}

    /* Toggle switch label */
    section[data-testid="stSidebar"] .stToggle label {{
        color: #f0f0f0 !important;
        font-weight: 600 !important;
    }}

    /* Sample query chips */
    .query-chip {{
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(245,197,24,0.35);
        border-radius: 8px;
        padding: 7px 12px;
        margin: 4px 0;
        font-size: 0.82rem;
        color: #dddddd !important;
        font-style: italic;
    }}

    /* ── Main area chat messages (Streamlit native) ── */
    [data-testid="stChatMessage"] {{
        background: white !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.07) !important;
        border: 1px solid #f0e8e0 !important;
        color: {BRAND_DARK} !important;
    }}

    [data-testid="stChatInput"] textarea {{
        background: white !important;
        border-radius: 12px !important;
        color: {BRAND_DARK} !important;
    }}

    /* Inline code */
    code {{
        font-family: 'Nunito', monospace;
        color: {BRAND_ORANGE};
        background: #fff3ec;
        padding: 1px 6px;
        border-radius: 4px;
        font-weight: 700;
    }}

    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-thumb {{ background: {BRAND_ORANGE}; border-radius: 10px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------
# Session State
# ------------------------------------------------------------------

def setup_session_state() -> None:
    defaults = {
        "rag": None,
        "guardrail": PIIGuardrail(),
        "messages": [],          # List[dict] with keys: role, content, redacted, summary
        "pdf_path": None,
        "use_guardrails": False,
        "total_pii_blocked": 0,
        "total_queries": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _index_dir(file_path: str) -> str:
    digest = hashlib.sha1(os.path.abspath(file_path).encode()).hexdigest()[:SHA1_HASH_LENGTH]
    return os.path.join(FAISS_INDEX_DIR, digest)


def initialize_rag() -> bool:
    pdf_path = st.session_state.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        st.error("Please upload a PDF first.")
        return False
    try:
        index_dir = _index_dir(pdf_path)
        rag = RAGSystem()
        rag.create_index(pdf_path, index_dir)
        rag.setup_qa_chain()
        st.session_state.rag = rag
        return True
    except FileNotFoundError:
        st.error("PDF file not found.")
        return False
    except Exception:
        logger.exception("RAG init failed")
        st.error("Initialisation failed — check logs.")
        return False


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"## 🔐 PII Guardrails Demo")
        st.markdown("---")

        # ---- File Upload ----
        st.markdown(f"### 📄 1. Upload Data")
        uploaded = st.file_uploader(
            "Upload PDF", type=SUPPORTED_FILE_TYPES, label_visibility="collapsed"
        )
        if uploaded:
            target = os.path.join(os.getcwd(), uploaded.name)
            with open(target, "wb") as f:
                f.write(uploaded.read())
            st.session_state.pdf_path = target
            st.success(f"Loaded: `{uploaded.name}`")

        # ---- Index ----
        st.markdown(f"### ⚙️ 2. Build Index")
        if st.button("Initialize / Rebuild RAG Index"):
            with st.spinner("Building vector index…"):
                ok = initialize_rag()
            if ok:
                st.success("✅ RAG system ready!")

        # ---- Guardrails toggle ----
        st.markdown(f"### 🛡️ 3. Security")
        st.session_state.use_guardrails = st.toggle(
            "Enable PII Guardrails",
            value=st.session_state.use_guardrails,
        )

        if st.session_state.use_guardrails:
            st.markdown(
                '<span class="badge badge-on">🔒 GUARDRAILS ON</span>',
                unsafe_allow_html=True,
            )
            st.caption("SSN, phone, email, address, DOB, account numbers & credit cards will be redacted.")
        else:
            st.markdown(
                '<span class="badge badge-off">🔓 GUARDRAILS OFF</span>',
                unsafe_allow_html=True,
            )
            st.caption("Raw PII values will be shown — for demo purposes only.")

        # ---- Stats ----
        st.markdown("---")
        st.markdown(f"### 📊 Session Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Queries", st.session_state.total_queries)
        with col2:
            st.metric("PII Blocked", st.session_state.total_pii_blocked)

        # ---- Clear chat ----
        st.markdown("---")
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.total_queries = 0
            st.session_state.total_pii_blocked = 0
            st.rerun()

        # ---- Sample queries ----
        st.markdown(f"### 💡 Sample Queries")
        st.caption("Copy-paste one into the chat input:")
        for q in SAMPLE_QUERIES:
            st.markdown(f'<div class="query-chip">{q}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------
# Chat Rendering
# ------------------------------------------------------------------

def render_chat() -> None:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            was_redacted = msg.get("redacted", False)
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                if was_redacted:
                    summary = msg.get("summary", "PII redacted")
                    st.markdown(
                        f'<span class="redact-pill">⚠️ {summary}</span>',
                        unsafe_allow_html=True,
                    )
                    with st.expander("🔍 Redaction details"):
                        st.json(msg.get("redaction_counts", {}))


# ------------------------------------------------------------------
# Query Processing
# ------------------------------------------------------------------

def process_query(prompt: str) -> None:
    rag: RAGSystem = st.session_state.rag
    guardrail: PIIGuardrail = st.session_state.guardrail
    use_guardrails: bool = st.session_state.use_guardrails

    try:
        allow_open = not use_guardrails
        result = rag.ask_question(prompt, allow_open=allow_open)
        raw_answer: str = result.get("result", "I could not generate a response.")

        st.session_state.total_queries += 1

        if use_guardrails:
            redaction = guardrail.filter_response(raw_answer)
            if redaction.was_modified:
                st.session_state.total_pii_blocked += 1

            msg = {
                "role": "assistant",
                "content": redaction.redacted,
                "redacted": redaction.was_modified,
                "summary": redaction.summary,
                "redaction_counts": redaction.redaction_counts,
            }
        else:
            msg = {
                "role": "assistant",
                "content": raw_answer,
                "redacted": False,
            }

        st.session_state.messages.append(msg)

    except Exception:
        logger.exception("Error processing query")
        st.error("Failed to generate a response. Please try again.")


# ------------------------------------------------------------------
# Main Content
# ------------------------------------------------------------------

def render_main() -> None:
    # Header — AIBees style
    st.markdown(
        f"""
        <div class="demo-header">
            <div>
                <h1>🔐 RAG + PII Guardrails <span>Demo</span></h1>
                <p>Demonstrates how sensitive customer data is exposed (guardrails OFF) vs. redacted (guardrails ON) in a RAG pipeline.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Status bar
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.session_state.pdf_path:
            name = os.path.basename(st.session_state.pdf_path)
            st.info(f"📄 **File:** `{name}`")
        else:
            st.warning("No PDF uploaded yet.")
    with col2:
        if st.session_state.rag:
            st.success("✅ RAG system ready")
        else:
            st.warning("⚙️ RAG not initialised")
    with col3:
        if st.session_state.use_guardrails:
            st.markdown(
                f'<div style="background:#e6f9ee;border:1.5px solid #1a7a3a;border-radius:10px;padding:10px 16px;color:#1a7a3a;font-weight:700;font-family:Nunito,sans-serif;">🔒 Guardrails ACTIVE</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="background:#fdecea;border:1.5px solid #c0392b;border-radius:10px;padding:10px 16px;color:#c0392b;font-weight:700;font-family:Nunito,sans-serif;">🔓 Guardrails DISABLED</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    if not st.session_state.rag:
        st.markdown(f"""
        <div style="
            background: white;
            border: 2px dashed {BRAND_ORANGE};
            border-radius: 16px;
            padding: 36px;
            text-align: center;
            color: {BRAND_DARK};
            font-family: 'Nunito', sans-serif;
            margin-top: 20px;
        ">
            <div style="font-size: 3rem;">🔐</div>
            <h3 style="color: {BRAND_ORANGE}; margin: 10px 0 6px 0;">PII Guardrails Demo</h3>
            <p style="color: #666; margin: 0;">Upload a PDF and click <strong>Initialize / Rebuild RAG Index</strong> in the sidebar to start.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Chat area
    render_chat()

    # Input
    if user_prompt := st.chat_input("Ask about customer data…"):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving answer…"):
                process_query(user_prompt)
            # ↑ process_query appends to messages — grab AFTER it finishes
            last = st.session_state.messages[-1]
            st.markdown(last["content"])
            if last.get("redacted"):
                st.markdown(
                    f'<span class="redact-pill">⚠️ {last.get("summary", "PII redacted")}</span>',
                    unsafe_allow_html=True,
                )
                with st.expander("🔍 Redaction details"):
                    st.json(last.get("redaction_counts", {}))


# ------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------

def main() -> None:
    setup_session_state()
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()