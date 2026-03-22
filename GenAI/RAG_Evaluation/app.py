# AIBees Academy - IT Helpdesk Assistant
# ============================================================
# This app has 3 parts:
#   1. Upload a PDF and ask questions  (main chat)
#   2. RAGAS Evaluation tab           (retrieval quality)
#   3. DeepEval Evaluation tab        (safety & hallucination)
# ============================================================

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # Fix Windows OpenMP conflict arise due to sentence-transformers and FAISS both using OpenMP. Not needed on Linux/Mac.

import base64
import hashlib
import asyncio
import streamlit as st
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Import our two simple evaluation files
from ragas_eval import run_ragas_evaluation, display_ragas_scores
from deepeval_eval import run_deepeval_evaluation, display_deepeval_scores

# Fix for Streamlit's threaded environment
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

load_dotenv()

FAISS_INDEX_DIR = "faiss_store"
os.makedirs(FAISS_INDEX_DIR, exist_ok=True)

# ── AIBees Brand Colors ───────────────────────────────────────────────────────
BRAND_ORANGE  = "#E8500A"
BRAND_DARK    = "#3A3A3A"
BRAND_YELLOW  = "#F5C518"
BRAND_LIGHT   = "#FFF8F3"
BRAND_ORANGE2 = "#FF6B2B"

# ── SVG Avatars ───────────────────────────────────────────────────────────────
_USER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="50" fill="#3A3A3A"/>
  <circle cx="50" cy="36" r="16" fill="#F5C518"/>
  <ellipse cx="50" cy="80" rx="26" ry="20" fill="#F5C518"/>
</svg>"""

_BEE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="50" fill="#E8500A"/>
  <ellipse cx="50" cy="58" rx="14" ry="18" fill="#3A3A3A"/>
  <rect x="36" y="53" width="28" height="5" rx="2" fill="#F5C518"/>
  <rect x="36" y="62" width="28" height="5" rx="2" fill="#F5C518"/>
  <circle cx="50" cy="38" r="11" fill="#F5C518"/>
  <circle cx="46" cy="37" r="2.5" fill="#3A3A3A"/>
  <circle cx="54" cy="37" r="2.5" fill="#3A3A3A"/>
  <line x1="46" y1="28" x2="41" y2="20" stroke="#3A3A3A" stroke-width="2" stroke-linecap="round"/>
  <circle cx="41" cy="19" r="2.5" fill="#3A3A3A"/>
  <line x1="54" y1="28" x2="59" y2="20" stroke="#3A3A3A" stroke-width="2" stroke-linecap="round"/>
  <circle cx="59" cy="19" r="2.5" fill="#3A3A3A"/>
  <ellipse cx="34" cy="48" rx="11" ry="7" fill="white" fill-opacity="0.75" transform="rotate(-20 34 48)"/>
  <ellipse cx="66" cy="48" rx="11" ry="7" fill="white" fill-opacity="0.75" transform="rotate(20 66 48)"/>
</svg>"""

_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 80">
  <rect width="140" height="80" rx="12" fill="#E8500A"/>
  <ellipse cx="42" cy="46" rx="10" ry="13" fill="#3A3A3A"/>
  <rect x="32" y="41" width="20" height="4" rx="2" fill="#F5C518"/>
  <rect x="32" y="48" width="20" height="4" rx="2" fill="#F5C518"/>
  <circle cx="42" cy="31" r="9" fill="#F5C518"/>
  <circle cx="39" cy="30" r="2" fill="#3A3A3A"/>
  <circle cx="45" cy="30" r="2" fill="#3A3A3A"/>
  <line x1="39" y1="23" x2="35" y2="16" stroke="#3A3A3A" stroke-width="1.8" stroke-linecap="round"/>
  <circle cx="34" cy="15" r="2" fill="#3A3A3A"/>
  <line x1="45" y1="23" x2="49" y2="16" stroke="#3A3A3A" stroke-width="1.8" stroke-linecap="round"/>
  <circle cx="50" cy="15" r="2" fill="#3A3A3A"/>
  <ellipse cx="30" cy="38" rx="9" ry="6" fill="white" fill-opacity="0.8" transform="rotate(-15 30 38)"/>
  <ellipse cx="54" cy="38" rx="9" ry="6" fill="white" fill-opacity="0.8" transform="rotate(15 54 38)"/>
  <text x="68" y="34" font-family="'Trebuchet MS', sans-serif" font-size="22" font-weight="800" fill="white">AI</text>
  <text x="68" y="60" font-family="'Trebuchet MS', sans-serif" font-size="22" font-weight="800" fill="white">Bees</text>
</svg>"""

def svg_to_base64(svg_text):
    """Convert SVG text to a base64 data URI so we can use it as an image src."""
    encoded = base64.b64encode(svg_text.strip().encode()).decode()
    return "data:image/svg+xml;base64," + encoded

USER_AVATAR      = svg_to_base64(_USER_SVG)
ASSISTANT_AVATAR = svg_to_base64(_BEE_SVG)
LOGO_B64         = base64.b64encode(_LOGO_SVG.strip().encode()).decode()

# ── CSS Styles ────────────────────────────────────────────────────────────────
CUSTOM_CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

  html, body, [data-testid="stAppViewContainer"] {{
      background-color: {BRAND_LIGHT} !important;
      font-family: 'Nunito', sans-serif !important;
  }}

  /* ── Sidebar background ── */
  [data-testid="stSidebar"] {{
      background: linear-gradient(160deg, {BRAND_DARK} 0%, #1e1e1e 100%) !important;
      border-right: 3px solid {BRAND_ORANGE} !important;
  }}

  /* ── All sidebar text white by default ── */
  [data-testid="stSidebar"] * {{
      color: #f0f0f0 !important;
      font-family: 'Nunito', sans-serif !important;
  }}

  /* ── Sidebar headings in yellow ── */
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 {{
      color: {BRAND_YELLOW} !important;
      font-weight: 800 !important;
  }}

  [data-testid="stSidebar"] hr {{
      border-color: {BRAND_ORANGE} !important;
      opacity: 0.4;
  }}

  /* ── Sidebar buttons ── */
  [data-testid="stSidebar"] .stButton > button {{
      background: {BRAND_ORANGE} !important;
      color: white !important;
      border: none !important;
      border-radius: 8px !important;
      font-weight: 700 !important;
  }}
  [data-testid="stSidebar"] .stButton > button:hover {{
      background: {BRAND_ORANGE2} !important;
  }}

  /* ══════════════════════════════════════════════════════
     FILE UPLOADER — make it readable on dark sidebar
  ══════════════════════════════════════════════════════ */

  /* Outer uploader wrapper */
  [data-testid="stSidebar"] [data-testid="stFileUploader"] {{
      background: rgba(255, 255, 255, 0.08) !important;
      border: 1.5px dashed {BRAND_YELLOW} !important;
      border-radius: 10px !important;
      padding: 6px !important;
  }}

  /* Dropzone inner area */
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
      background: rgba(255, 255, 255, 0.05) !important;
      border-radius: 8px !important;
  }}

  /* ALL text inside the dropzone — force white */
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] *,
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] span,
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] p,
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] div,
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] small {{
      color: #ffffff !important;
      font-weight: 600 !important;
  }}

  /* "Browse files" button */
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button,
  [data-testid="stSidebar"] [data-testid="stFileUploader"] button {{
      background: {BRAND_YELLOW} !important;
      color: {BRAND_DARK} !important;
      border: none !important;
      font-weight: 700 !important;
      border-radius: 6px !important;
  }}

  /* Uploaded filename + filesize shown after upload */
  [data-testid="stSidebar"] [data-testid="stFileUploaderFileName"],
  [data-testid="stSidebar"] [data-testid="stFileUploaderFile"] *,
  [data-testid="stSidebar"] [data-testid="stFileUploaderFileData"] * {{
      color: #ffffff !important;
      font-weight: 600 !important;
  }}

  /* small tag used for file size */
  [data-testid="stSidebar"] small {{
      color: #dddddd !important;
      font-size: 0.78rem !important;
  }}

  /* ── Active filename shown as inline code e.g. `IT_Helpdesk_Policy.pdf` ── */
  [data-testid="stSidebar"] code {{
      background: rgba(245, 197, 24, 0.20) !important;
      color: {BRAND_YELLOW} !important;
      border: 1px solid rgba(245, 197, 24, 0.40) !important;
      border-radius: 5px !important;
      padding: 2px 7px !important;
      font-size: 0.82rem !important;
      font-weight: 700 !important;
  }}

  /* ══════════════════════════════════════════════════════
     TEXT AREA — white background so text is readable
  ══════════════════════════════════════════════════════ */

  /* The actual textarea box — WHITE background, dark text */
  [data-testid="stSidebar"] textarea {{
      background-color: #ffffff !important;
      color: {BRAND_DARK} !important;
      border: 1.5px solid {BRAND_ORANGE} !important;
      border-radius: 8px !important;
      font-family: 'Nunito', sans-serif !important;
      font-size: 0.88rem !important;
      font-weight: 600 !important;
  }}
  [data-testid="stSidebar"] textarea:focus {{
      border-color: {BRAND_YELLOW} !important;
      box-shadow: 0 0 0 2px rgba(245,197,24,0.3) !important;
  }}
  [data-testid="stSidebar"] textarea::placeholder {{
      color: #999999 !important;
  }}

  /* Label above the textarea */
  [data-testid="stSidebar"] .stTextArea label p,
  [data-testid="stSidebar"] .stTextArea label {{
      color: {BRAND_YELLOW} !important;
      font-weight: 700 !important;
      font-size: 0.88rem !important;
  }}

  /* ══════════════════════════════════════════════════════
     TEXT INPUT — white background so text is readable
  ══════════════════════════════════════════════════════ */

  [data-testid="stSidebar"] input[type="text"],
  [data-testid="stSidebar"] input {{
      background-color: #ffffff !important;
      color: {BRAND_DARK} !important;
      border: 1.5px solid {BRAND_ORANGE} !important;
      border-radius: 8px !important;
      font-family: 'Nunito', sans-serif !important;
      font-weight: 600 !important;
  }}
  [data-testid="stSidebar"] input::placeholder {{
      color: #999999 !important;
  }}

  /* Label above text input */
  [data-testid="stSidebar"] .stTextInput label p,
  [data-testid="stSidebar"] .stTextInput label {{
      color: {BRAND_YELLOW} !important;
      font-weight: 700 !important;
  }}

  /* ── Main area styles ── */
  .aibees-header {{
      display: flex;
      align-items: center;
      gap: 18px;
      padding: 18px 24px;
      background: linear-gradient(135deg, {BRAND_DARK} 0%, #2a2a2a 100%);
      border-radius: 16px;
      margin-bottom: 20px;
      box-shadow: 0 6px 24px rgba(0,0,0,0.18);
      border-left: 5px solid {BRAND_ORANGE};
  }}
  .aibees-header-text h1 {{
      margin: 0;
      font-size: 1.7rem;
      font-weight: 800;
      color: white;
  }}
  .aibees-header-text h1 span {{ color: {BRAND_YELLOW}; }}
  .aibees-header-text p {{
      margin: 4px 0 0 0;
      font-size: 0.82rem;
      color: #aaa;
  }}

  [data-testid="stChatMessage"] {{
      background: white !important;
      border-radius: 14px !important;
      padding: 14px 18px !important;
      margin-bottom: 10px !important;
      box-shadow: 0 2px 10px rgba(0,0,0,0.07) !important;
      border: 1px solid #f0e8e0 !important;
  }}

  /* Main chat input — keep dark text on white */
  [data-testid="stChatInput"] textarea {{
      background: white !important;
      border-radius: 12px !important;
      color: {BRAND_DARK} !important;
  }}

  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-thumb {{ background: {BRAND_ORANGE}; border-radius: 10px; }}
</style>
"""

# ── AI Models ─────────────────────────────────────────────────────────────────
embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.5,
)

# ── PDF Helper Functions ──────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_file):
    """Read all text from a PDF file."""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

def compute_md5(text):
    """Create a unique ID from the text — used to cache the FAISS index."""
    return hashlib.md5(text.encode()).hexdigest()

def create_faiss_index(text, index_path):
    """Split text into chunks and save a FAISS vector index."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    db = FAISS.from_texts(chunks, embedding_model)
    db.save_local(index_path)

def load_or_create_faiss(pdf_file):
    """Load FAISS index from disk if it exists, otherwise create it."""
    text = extract_text_from_pdf(pdf_file)
    file_hash = compute_md5(text)
    index_path = os.path.join(FAISS_INDEX_DIR, file_hash)
    if not os.path.exists(index_path):
        with st.spinner("🔍 Indexing document — this only happens once…"):
            create_faiss_index(text, index_path)
    return FAISS.load_local(index_path, embedding_model, allow_dangerous_deserialization=True)

def build_prompt(context, history, question):
    """Build the full message list: system instruction + history + new question."""
    system_message = {
        "role": "system",
        "content": (
            "You are the AIBees Academy Knowledge Assistant — an expert AI tutor and helpdesk agent. "
            "Answer questions using the provided document context. "
            "Be concise, warm, encouraging, and professional. "
            "If the answer is not in the context, say so honestly."
        ),
    }
    history_messages = []
    for turn in history:
        history_messages.append({"role": "user",      "content": turn["question"]})
        history_messages.append({"role": "assistant", "content": turn["answer"]})

    user_message = {
        "role": "user",
        "content": (
            f"Use the following document excerpts to answer the question.\n\n"
            f"--- Document Context ---\n{context}\n--- End Context ---\n\n"
            f"Question: {question}"
        ),
    }
    return [system_message] + history_messages + [user_message]


# ── Streamlit App Setup ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="AIBees Knowledge Assistant",
    page_icon="🐝",
    layout="centered"
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Branded header
st.markdown(f"""
<div class="aibees-header">
    <img src="data:image/svg+xml;base64,{LOGO_B64}" width="100" alt="AIBees Logo"/>
    <div class="aibees-header-text">
        <h1>IT Helpdesk <span>Assistant</span></h1>
        <p>🐝 RAG · Gemini 2.5 Flash · FAISS · RAGAS · DeepEval · AIBees Academy</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "db" not in st.session_state:
    st.session_state.db = None
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""
if "last_chunks" not in st.session_state:
    st.session_state.last_chunks = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 10px 0 4px 0;">
        <img src="data:image/svg+xml;base64,{LOGO_B64}" width="160" alt="AIBees"/>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📄 Upload IT Policy Document")
    uploaded_file = st.file_uploader("Choose a PDF", type="pdf", label_visibility="collapsed")

    if uploaded_file:
        if uploaded_file.name != st.session_state.pdf_name:
            st.session_state.db = load_or_create_faiss(uploaded_file)
            st.session_state.pdf_name = uploaded_file.name
            st.session_state.chat_history = []
            st.success(f"✅ Loaded: {uploaded_file.name}")

    if st.session_state.pdf_name:
        st.markdown(f"&nbsp;&nbsp;📄 Active: `{st.session_state.pdf_name}`")

    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown("**💡 Sample questions:**")
    for q in [
        "How do I reset my password?",
        "What are the VPN setup steps?",
        "How do I report a phishing email?",
        "What is the laptop replacement process?",
        "What Wi-Fi networks are available?",
        "What happens to my access when I leave?",
    ]:
        st.markdown(f"&nbsp;&nbsp;› {q}")

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#888; font-size:0.75rem;'>"
        "© 2026 AIBees Academy<br/>All rights reserved</div>",
        unsafe_allow_html=True
    )

# ── No PDF uploaded yet — show welcome screen ─────────────────────────────────
if not st.session_state.db:
    st.markdown("""
    <div style="
        background: white;
        border: 2px dashed #E8500A;
        border-radius: 16px;
        padding: 36px;
        text-align: center;
        color: #3A3A3A;
        font-family: 'Nunito', sans-serif;
        margin-top: 20px;
    ">
        <div style="font-size: 3rem;">🐝</div>
        <h3 style="color: #E8500A; margin: 10px 0 6px 0;">Welcome to AIBees IT Helpdesk Assistant</h3>
        <p style="color: #666; margin: 0;">Upload an IT policy PDF from the sidebar to start asking questions.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── 3 Tabs: Chat | RAGAS | DeepEval ──────────────────────────────────────────
tab_chat, tab_ragas, tab_deepeval = st.tabs([
    "💬 Chat",
    "📊 RAGAS Evaluation",
    "🛡️ DeepEval Evaluation"
])


# ════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════════════════
with tab_chat:

    for turn in st.session_state.chat_history:
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(turn["question"])
        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            st.markdown(turn["answer"])

    user_query = st.chat_input("Ask a question about IT policies…")

    if user_query:
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(user_query)

        similar_chunks = st.session_state.db.similarity_search(user_query, k=4)
        context = "\n\n".join(chunk.page_content.strip() for chunk in similar_chunks)
        messages = build_prompt(context, st.session_state.chat_history, user_query)

        with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
            with st.spinner("🐝 Thinking…"):
                answer = llm.invoke(messages).content.strip()
            st.markdown(answer)

        st.session_state.last_question = user_query
        st.session_state.last_answer   = answer
        st.session_state.last_chunks   = [chunk.page_content for chunk in similar_chunks]

        st.session_state.chat_history.append(
            {"question": user_query, "answer": answer}
        )


# ════════════════════════════════════════════════════════════
# TAB 2 — RAGAS EVALUATION
# ════════════════════════════════════════════════════════════
with tab_ragas:

    st.markdown("### 📊 RAGAS — Retrieval Quality Evaluation")
    st.markdown("""
    RAGAS checks how well the **retrieval step** of your RAG pipeline is working.
    It needs the question, the LLM's answer, the retrieved chunks, and a ground truth answer.
    """)

    if st.session_state.last_question:
        st.info(f"**Last question:** {st.session_state.last_question}")
        st.info(f"**Last answer:** {st.session_state.last_answer[:200]}...")
    else:
        st.warning("Ask a question in the Chat tab first, then come here to evaluate it.")
        st.stop()

    ground_truth = st.text_area(
        "✍️ Enter the expected correct answer (ground truth):",
        placeholder="e.g. To reset your password, go to the IT portal at portal.company.com and click Forgot Password...",
        height=100
    )

    if st.button("▶️ Run RAGAS Evaluation", type="primary"):
        if not ground_truth.strip():
            st.warning("Please enter a ground truth answer before running RAGAS.")
        else:
            with st.spinner("⏳ Running RAGAS metrics... this may take 30-60 seconds"):
                scores = run_ragas_evaluation(
                    question         = st.session_state.last_question,
                    answer           = st.session_state.last_answer,
                    retrieved_chunks = st.session_state.last_chunks,
                    ground_truth     = ground_truth,
                    llm              = llm,
                    embedding_model  = embedding_model,
                )
            display_ragas_scores(scores)


# ════════════════════════════════════════════════════════════
# TAB 3 — DEEPEVAL EVALUATION
# ════════════════════════════════════════════════════════════
with tab_deepeval:

    st.markdown("### 🛡️ DeepEval — Safety & Hallucination Checks")
    st.markdown("""
    DeepEval checks the **quality and safety** of the LLM's response.
    It does NOT need a ground truth — it evaluates the answer directly using retrieved chunks.
    """)

    if st.session_state.last_question:
        st.info(f"**Last question:** {st.session_state.last_question}")
        st.info(f"**Last answer:** {st.session_state.last_answer[:200]}...")
    else:
        st.warning("Ask a question in the Chat tab first, then come here to evaluate it.")
        st.stop()

    ground_truth_optional = st.text_area(
        "✍️ Optional: Enter expected answer (helps with recall metric):",
        placeholder="Leave blank if you just want hallucination / toxicity / bias checks",
        height=80
    )

    if st.button("▶️ Run DeepEval Evaluation", type="primary"):
        with st.spinner("⏳ Running DeepEval checks... this may take 30-60 seconds"):
            scores = run_deepeval_evaluation(
                question         = st.session_state.last_question,
                answer           = st.session_state.last_answer,
                retrieved_chunks = st.session_state.last_chunks,
                ground_truth     = ground_truth_optional,
            )
        display_deepeval_scores(scores)