# AIBees Academy - IT Helpdesk Assistant
import os
import base64
import streamlit as st
import hashlib
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from dotenv import load_dotenv
import asyncio

# Fix for Streamlit's threaded environment — ensure an event loop always exists
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

def _svg_to_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.strip().encode()).decode()

USER_AVATAR      = _svg_to_uri(_USER_SVG)
ASSISTANT_AVATAR = _svg_to_uri(_BEE_SVG)
LOGO_B64         = base64.b64encode(_LOGO_SVG.strip().encode()).decode()

# ── Custom CSS ────────────────────────────────────────────────────────────────
CUSTOM_CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

  html, body, [data-testid="stAppViewContainer"] {{
      background-color: {BRAND_LIGHT} !important;
      font-family: 'Nunito', sans-serif !important;
  }}

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {{
      background: linear-gradient(160deg, {BRAND_DARK} 0%, #1e1e1e 100%) !important;
      border-right: 3px solid {BRAND_ORANGE} !important;
  }}
  [data-testid="stSidebar"] * {{
      color: #f0f0f0 !important;
      font-family: 'Nunito', sans-serif !important;
  }}
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
      font-family: 'Nunito', sans-serif !important;
      transition: all 0.2s ease;
  }}
  [data-testid="stSidebar"] .stButton > button:hover {{
      background: {BRAND_ORANGE2} !important;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(232,80,10,0.4) !important;
  }}

  /* ── Sidebar file uploader ── */
  [data-testid="stSidebar"] [data-testid="stFileUploader"] {{
      background: rgba(255,255,255,0.08) !important;
      border: 1px dashed rgba(245,197,24,0.5) !important;
      border-radius: 10px !important;
      padding: 8px !important;
  }}
  [data-testid="stSidebar"] [data-testid="stFileUploader"] * {{
      color: #f0f0f0 !important;
  }}
  /* Drag and drop zone inner section */
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
      background: rgba(255,255,255,0.06) !important;
      border-radius: 8px !important;
  }}
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {{
      color: #f0f0f0 !important;
  }}
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] * {{
      color: #f0f0f0 !important;
  }}
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] span,
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] small,
  [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] p {{
      color: #cccccc !important;
      font-size: 0.8rem !important;
  }}
  [data-testid="stSidebar"] [data-testid="stFileUploader"] button {{
      background: {BRAND_YELLOW} !important;
      color: {BRAND_DARK} !important;
      border: none !important;
      font-weight: 700 !important;
      border-radius: 6px !important;
  }}

  /* ── Sidebar code text ── */
  [data-testid="stSidebar"] code {{
      background: rgba(255,255,255,0.12) !important;
      color: {BRAND_YELLOW} !important;
      border-radius: 4px !important;
      padding: 1px 5px !important;
  }}

  /* ── Header ── */
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
      font-family: 'Nunito', sans-serif;
      line-height: 1.2;
  }}
  .aibees-header-text h1 span {{ color: {BRAND_YELLOW}; }}
  .aibees-header-text p {{
      margin: 4px 0 0 0;
      font-size: 0.82rem;
      color: #aaa;
      font-family: 'Nunito', sans-serif;
  }}

  /* ── Chat messages ── */
  [data-testid="stChatMessage"] {{
      background: white !important;
      border-radius: 14px !important;
      padding: 14px 18px !important;
      margin-bottom: 10px !important;
      box-shadow: 0 2px 10px rgba(0,0,0,0.07) !important;
      border: 1px solid #f0e8e0 !important;
      font-family: 'Nunito', sans-serif !important;
  }}

  /* ── Chat input ── */
  [data-testid="stChatInput"] textarea {{
      background: white !important;
      border: none !important;
      border-radius: 12px !important;
      font-family: 'Nunito', sans-serif !important;
      font-size: 0.95rem !important;
      color: {BRAND_DARK} !important;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
  }}
  [data-testid="stChatInput"] textarea:focus {{
      box-shadow: 0 2px 12px rgba(0,0,0,0.12) !important;
      outline: none !important;
  }}

  /* ── Sidebar collapse button — replace keyboard icon with chevron ── */
  [data-testid="stSidebarCollapsedControl"] {{
      background: {BRAND_ORANGE} !important;
      border-radius: 0 8px 8px 0 !important;
      width: 28px !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
  }}
  [data-testid="stSidebarCollapsedControl"] svg {{ display: none !important; }}
  [data-testid="stSidebarCollapsedControl"]::after {{
      content: "‹‹" !important;
      color: white !important;
      font-size: 1rem !important;
      font-weight: 800 !important;
      font-family: 'Nunito', sans-serif !important;
      letter-spacing: -2px !important;
  }}
  [data-testid="stSidebarCollapsedControl"]:hover {{
      background: {BRAND_ORANGE2} !important;
      cursor: pointer !important;
  }}
  /* Broad catch-all for different Streamlit versions */
  button[kind="header"] svg,
  [data-testid*="Collapse"] svg,
  [data-testid*="collapse"] svg {{
      display: none !important;
  }}
  [data-testid*="Collapse"]::after,
  [data-testid*="collapse"]::after {{
      content: "‹‹" !important;
      color: white !important;
      font-size: 1rem !important;
      font-weight: 800 !important;
  }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: {BRAND_LIGHT}; }}
  ::-webkit-scrollbar-thumb {{ background: {BRAND_ORANGE}; border-radius: 10px; }}
</style>
"""

# ── Models ──────────────────────────────────────────────────────────────────
embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.5,
)

# ── Helpers ──────────────────────────────────────────────────────────────────
# function to extract text from PDF using PyMuPDF (fitz)
def extract_text_from_pdf(pdf_file) -> str:
    """Extract all text from an uploaded PDF file object."""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

# function to compute MD5 hash of text for caching purposes
def compute_md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

# function to create and save a FAISS index from text
def create_faiss_index(text: str, index_path: str) -> None:
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    db = FAISS.from_texts(chunks, embedding_model)
    db.save_local(index_path)

# function to load an existing FAISS index or create it if it doesn't exist
def load_or_create_faiss(pdf_file) -> FAISS:
    text = extract_text_from_pdf(pdf_file)
    file_hash = compute_md5(text)
    index_path = os.path.join(FAISS_INDEX_DIR, file_hash)
    if not os.path.exists(index_path):
        with st.spinner("🔍 Indexing document — this only happens once…"):
            create_faiss_index(text, index_path)
    return FAISS.load_local(
        index_path, embedding_model, allow_dangerous_deserialization=True
    )

# function to build the prompt for the LLM, including system instructions,
#  conversation history, and retrieved context
def build_prompt(context: str, history: list[dict], question: str) -> list[dict]:
    """
    Construct the full message list for the LLM:
      1. System instruction
      2. Previous conversation turns (for memory)
      3. New user turn with retrieved context injected
    """
    system_message = {
        "role": "system",
        "content": (
            "You are the AIBees Academy Knowledge Assistant — an expert AI tutor and helpdesk agent. "
            "Answer questions using the provided document context. "
            "Be concise, warm, encouraging, and professional. "
            "If the answer is not in the context, say so honestly and suggest reaching out to the AIBees team."
        ),
    }

    # Reconstruct history as alternating user/assistant turns
    history_messages = []
    for turn in history:
        history_messages.append({"role": "user",      "content": turn["question"]})
        history_messages.append({"role": "assistant", "content": turn["answer"]})

    # Current user message with context injected
    user_message = {
        "role": "user",
        "content": (
            f"Use the following document excerpts to answer the question.\n\n"
            f"--- Document Context ---\n{context}\n--- End Context ---\n\n"
            f"Question: {question}"
        ),
    }

    return [system_message] + history_messages + [user_message]


# ── Streamlit App ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AIBees Knowledge Assistant",
    page_icon="🐝",
    layout="centered"
)

# Inject CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Branded Header ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="aibees-header">
    <img src="data:image/svg+xml;base64,{LOGO_B64}" width="100" alt="AIBees Logo"/>
    <div class="aibees-header-text">
        <h1>IT Helpdesk <span>Assistant</span></h1>
        <p>🐝 RAG &nbsp;·&nbsp; Gemini 2.5 Flash &nbsp;·&nbsp; FAISS &nbsp;·&nbsp; AIBees Academy</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Session State Init ───────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "db" not in st.session_state:
    st.session_state.db = None
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

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
        # Re-index only when a new file is uploaded
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

# ── Main Chat Area ────────────────────────────────────────────────────────────
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

# Render existing conversation with AIBees avatars
for turn in st.session_state.chat_history:
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(turn["question"])
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        st.markdown(turn["answer"])

# Chat input at the bottom
user_query = st.chat_input("Ask a question about IT policies…")

if user_query:
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_query)

    # Retrieve relevant chunks from FAISS
    similar_chunks = st.session_state.db.similarity_search(user_query, k=4)
    context = "\n\n".join(chunk.page_content.strip() for chunk in similar_chunks)

    # Build prompt with full conversation history for memory
    messages = build_prompt(context, st.session_state.chat_history, user_query)

    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        with st.spinner("🐝 Thinking…"):
            answer = llm.invoke(messages).content.strip()
        st.markdown(answer)

    # Persist this turn in session state
    st.session_state.chat_history.append(
        {"question": user_query, "answer": answer}
    )