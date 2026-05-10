"""
app.py — Patient Medical History RAG System
Run: streamlit run app.py
"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import base64, asyncio
import streamlit as st
from langchain_core.messages import HumanMessage

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from config import BRAND_ORANGE, BRAND_DARK, BRAND_YELLOW, BRAND_LIGHT, BRAND_ORANGE2
from core.vector_store import ingest_pdf, get_ingested_files
from graph.builder import build_simple_graph, build_agentic_graph, save_graph_pngs
from utils.langfuse_setup import init_langfuse, make_config


# ── SVG Assets ──────────────────────────────────────────────────────────────
LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 80">
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
  <text x="68" y="34" font-family="Trebuchet MS,sans-serif" font-size="22" font-weight="800" fill="white">AI</text>
  <text x="68" y="60" font-family="Trebuchet MS,sans-serif" font-size="22" font-weight="800" fill="white">Bees</text>
</svg>"""

USER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="50" fill="#3A3A3A"/>
  <circle cx="50" cy="36" r="16" fill="#F5C518"/>
  <ellipse cx="50" cy="80" rx="26" ry="20" fill="#F5C518"/>
</svg>"""

BOT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
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

def b64(s): return "data:image/svg+xml;base64," + base64.b64encode(s.strip().encode()).decode()
USER_AVATAR = b64(USER_SVG)
BOT_AVATAR  = b64(BOT_SVG)
LOGO_B64    = base64.b64encode(LOGO_SVG.strip().encode()).decode()

BRAND_ORANGE  = "#E8500A"
BRAND_DARK    = "#3A3A3A"
BRAND_YELLOW  = "#F5C518"
BRAND_LIGHT   = "#FFF8F3"
BRAND_ORANGE2 = "#FF6B2B"

# ── CSS ──────────────────────────────────────────────────────────────────────
CSS = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background-color: {BRAND_LIGHT} !important;
    font-family: 'Nunito', sans-serif !important;
}}
[data-testid="stSidebar"] {{
    background: linear-gradient(160deg, {BRAND_DARK} 0%, #1e1e1e 100%) !important;
    border-right: 3px solid {BRAND_ORANGE} !important;
}}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] small {{ color: #e0e0e0 !important; font-family: 'Nunito', sans-serif !important; }}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] b {{ color: {BRAND_YELLOW} !important; font-weight: 800 !important; }}
[data-testid="stSidebar"] hr {{ border-color: {BRAND_ORANGE} !important; opacity: 0.4; }}
[data-testid="stSidebar"] .stButton > button {{
    background: {BRAND_ORANGE} !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 700 !important; transition: all 0.2s ease;
}}
[data-testid="stFileUploaderDropzone"] {{
    background: rgba(255,255,255,0.08) !important;
    border: 1.5px dashed {BRAND_YELLOW} !important; border-radius: 8px !important;
}}
[data-testid="stChatMessage"] {{
    background: white !important; border-radius: 14px !important;
    padding: 14px 18px !important; margin-bottom: 10px !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07) !important;
    border: 1px solid #f0e8e0 !important;
}}
[data-testid="stChatInput"] textarea {{
    background: white !important; border-radius: 12px !important;
    font-family: 'Nunito', sans-serif !important; color: {BRAND_DARK} !important;
}}
[data-testid="stChatInput"] button {{ background: {BRAND_ORANGE} !important; border-radius: 8px !important; }}
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-thumb {{ background: {BRAND_ORANGE}; border-radius: 10px; }}
.stApp > header {{ display: none; }}
.mode-badge {{
    display: inline-block; font-size: 0.72rem; font-weight: 700;
    padding: 2px 10px; border-radius: 20px; margin-bottom: 8px;
}}
.badge-agentic {{ background: #E8F5E9; color: #1B5E20; }}
.badge-simple  {{ background: #FFF3E0; color: #BF360C; }}
.badge-compare {{ background: #EDE7F6; color: #4A148C; }}
</style>"""


# ══════════════════════════════════════════════════════════════════════════════
#  APP SETUP
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Patient History RAG — AIBees", page_icon="🏥", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

st.markdown(f"""
<div style="display:flex;align-items:center;gap:18px;padding:18px 24px;
background:linear-gradient(135deg,{BRAND_DARK} 0%,#2a2a2a 100%);
border-radius:16px;margin-bottom:20px;box-shadow:0 6px 24px rgba(0,0,0,0.18);
border-left:5px solid {BRAND_ORANGE};">
    <img src="data:image/svg+xml;base64,{LOGO_B64}" width="130" alt="AIBees"/>
    <div>
        <h1 style="margin:0;font-size:1.7rem;font-weight:800;color:white;">
            Patient History <span style="color:{BRAND_YELLOW};">RAG System</span>
        </h1>
        <p style="margin:4px 0 0;font-size:0.82rem;color:#aaa;">
            🏥 Simple RAG vs Agentic RAG &nbsp;·&nbsp; FAISS &nbsp;·&nbsp; Gemini 2.5 Pro
        </p>
    </div>
</div>""", unsafe_allow_html=True)


# ── One-time session init ─────────────────────────────────────────────────────
if "app_ready" not in st.session_state:
    st.session_state.simple_graph      = build_simple_graph()
    st.session_state.agentic_graph     = build_agentic_graph()
    save_graph_pngs()
    lf, _ = init_langfuse()
    st.session_state.langfuse          = lf
    st.session_state.langfuse_handler  = None   # handlers created per-call
    st.session_state.chat_history      = []
    st.session_state.app_ready         = True


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:10px 0 4px;">
        <img src="data:image/svg+xml;base64,{LOGO_B64}" width="180" alt="AIBees"/>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📄 Upload Patient Records")
    st.caption("Upload PDF records — discharge summaries, lab reports, consultation notes.")

    uploaded = st.file_uploader("Choose a PDF", type="pdf", label_visibility="collapsed")
    if uploaded is not None:
        if st.button("➕ Ingest into Knowledge Base", use_container_width=True):
            with st.spinner("Embedding and indexing…"):
                ok, msg = ingest_pdf(uploaded.read(), uploaded.name)
            if ok:
                st.success(f"✅ {uploaded.name} ingested.")
            else:
                st.warning(f"⚠️ {uploaded.name} already in KB.")

    st.markdown("---")
    st.markdown("### 📚 Knowledge Base")
    files = get_ingested_files()
    if files:
        for f in files:
            st.markdown(f"&nbsp;&nbsp;📄 `{f}`")
        st.caption(f"**{len(files)}** record(s) loaded")
    else:
        st.caption("No records ingested yet.")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Reset KB"):
            import shutil
            from config import COMBINED_INDEX, REGISTRY_FILE
            if COMBINED_INDEX.exists(): shutil.rmtree(COMBINED_INDEX)
            if REGISTRY_FILE.exists():  REGISTRY_FILE.unlink()
            st.session_state.chat_history = []
            st.rerun()
    with col2:
        if st.button("💬 Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("---")
    st.markdown("**💡 Try these queries:**")
    for q in [
        "Is it safe to give Ibuprofen to Suresh Babu?",
        "What is Ravi Kumar's HbA1c trend?",
        "Which patients have drug allergies?",
        "Can Ananya Krishnan take Aspirin?",
        "Which patients need urgent follow-up?",
    ]:
        st.markdown(f"&nbsp;&nbsp;› _{q}_")

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#888;font-size:0.75rem;'>"
        "© 2026 AIBees Academy<br/>All rights reserved</div>",
        unsafe_allow_html=True,
    )


# ── Gate ──────────────────────────────────────────────────────────────────────
if not files:
    st.markdown("""
    <div style="background:white;border:2px dashed #E8500A;border-radius:16px;
    padding:36px;text-align:center;margin-top:20px;">
        <div style="font-size:3rem;">🏥</div>
        <h3 style="color:#E8500A;margin:10px 0 6px;">Upload patient records to begin</h3>
        <p style="color:#666;margin:0;">Use the sidebar to upload PDF records into the knowledge base.</p>
    </div>""", unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def make_initial_state(question: str) -> dict:
    return {
        "question":          question,
        "messages":          [HumanMessage(content=question)],
        "retrieved_context": "",
        "search_log":        [],
        "final_answer":      None,
        "iteration_count":   0,
    }

def run_graph(graph, question: str, run_name: str, tags: list) -> dict:
    # make_config creates a fresh CallbackHandler per call with correct
    # session_id, user_id, tags set on the handler itself (not metadata)
    cfg = make_config(None, run_name=run_name, tags=tags)
    return graph.invoke(make_initial_state(question), config=cfg)

def render_trace(search_log: list, expanded: bool = False):
    if not search_log:
        return
    n = len(search_log)
    with st.expander(f"🔍 Search trace — {n} search(es) performed", expanded=expanded):
        for i, s in enumerate(search_log, 1):
            st.markdown(f"**Search {i}:** `{s['query']}` → **{s['chunks']}** excerpts retrieved")
        if n > 1:
            st.info(
                f"Agent searched **{n} times**. Each query was chosen by the LLM "
                "after reading the previous results. This is Agentic RAG.", icon="💡",
            )

def mode_badge(mode: str):
    cfg = {
        "agentic": ("badge-agentic", "🤖 Agentic RAG"),
        "simple":  ("badge-simple",  "⚡ Simple RAG"),
        "compare": ("badge-compare", "🔬 Compare side-by-side"),
    }
    cls, label = cfg.get(mode, ("badge-agentic", mode))
    st.markdown(f'<span class="mode-badge {cls}">{label}</span>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CHAT HISTORY DISPLAY
# ══════════════════════════════════════════════════════════════════════════════
for turn in st.session_state.chat_history:
    avatar = USER_AVATAR if turn["role"] == "user" else BOT_AVATAR
    with st.chat_message(turn["role"], avatar=avatar):
        if turn["role"] == "assistant":
            mode_badge(turn.get("mode", "agentic"))

        if turn.get("mode") == "compare":
            col_ag, col_si = st.columns(2)
            with col_ag:
                st.markdown(
                    "<div style='background:#E8F5E9;border-left:4px solid #2E7D32;"
                    "padding:10px 14px;border-radius:8px;margin-bottom:8px;'>"
                    "<b style='color:#1B5E20'>🤖 Agentic RAG</b><br/>"
                    "<span style='color:#4CAF50;font-size:0.8rem'>Iterative retrieval</span>"
                    "</div>", unsafe_allow_html=True)
                st.markdown(turn["ag_answer"])
                render_trace(turn.get("ag_log", []))
            with col_si:
                st.markdown(
                    "<div style='background:#FFF3E0;border-left:4px solid #E65100;"
                    "padding:10px 14px;border-radius:8px;margin-bottom:8px;'>"
                    "<b style='color:#BF360C'>⚡ Simple RAG</b><br/>"
                    "<span style='color:#FF7043;font-size:0.8rem'>Single search</span>"
                    "</div>", unsafe_allow_html=True)
                st.markdown(turn["si_answer"])
                render_trace(turn.get("si_log", []))
        else:
            st.markdown(turn["content"])
            if turn.get("search_log"):
                render_trace(turn["search_log"], expanded=False)


# ══════════════════════════════════════════════════════════════════════════════
#  MODE + INPUT  — Captured together atomically inside st.form
#  This is the ONLY reliable way to read mode + question in the same submit.
#  st.chat_input fires a separate rerun from st.radio, causing the mode to
#  always read as the default.  st.form submits BOTH widgets in one rerun.
# ══════════════════════════════════════════════════════════════════════════════
with st.form("ask_form", clear_on_submit=True):
    mode_col, input_col, btn_col = st.columns([1.8, 5, 0.7])

    with mode_col:
        # selectbox inside the form — value is captured on the same submit
        mode_choice = st.selectbox(
            "Mode",
            options=["agentic", "simple", "compare"],
            format_func=lambda m: {
                "agentic": "🤖 Agentic RAG",
                "simple":  "⚡ Simple RAG",
                "compare": "🔬 Compare side-by-side",
            }[m],
            label_visibility="collapsed",
        )

    with input_col:
        question = st.text_input(
            "Question",
            placeholder="Ask anything about any patient's records…",
            label_visibility="collapsed",
        )

    with btn_col:
        submitted = st.form_submit_button("➤", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PROCESS SUBMISSION
# ══════════════════════════════════════════════════════════════════════════════
if submitted and question.strip():
    q = question.strip()

    # Show user message
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(q)
    st.session_state.chat_history.append({"role": "user", "content": q})

    # ── AGENTIC RAG ───────────────────────────────────────────────────────────
    if mode_choice == "agentic":
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            mode_badge("agentic")
            with st.spinner("🐝 Agent is searching and reasoning…"):
                result = run_graph(st.session_state.agentic_graph, q, "agentic-rag", ["agentic-rag"])
            answer     = result.get("final_answer") or "No answer produced."
            search_log = result.get("search_log", [])
            st.markdown(answer)
            render_trace(search_log, expanded=len(search_log) > 1)
        st.session_state.chat_history.append({
            "role": "assistant", "mode": "agentic",
            "content": answer, "search_log": search_log,
        })

    # ── SIMPLE RAG ────────────────────────────────────────────────────────────
    elif mode_choice == "simple":
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            mode_badge("simple")
            with st.spinner("⚡ Searching records…"):
                result = run_graph(st.session_state.simple_graph, q, "simple-rag", ["simple-rag"])
            answer     = result.get("final_answer") or "No answer produced."
            search_log = result.get("search_log", [])
            st.markdown(answer)
            render_trace(search_log, expanded=False)
            st.info("Simple RAG: one search, one LLM call — no iterative reasoning.", icon="ℹ️")
        st.session_state.chat_history.append({
            "role": "assistant", "mode": "simple",
            "content": answer, "search_log": search_log,
        })

    # ── COMPARE SIDE-BY-SIDE ──────────────────────────────────────────────────
    elif mode_choice == "compare":
        with st.spinner("🔬 Running both RAG modes…"):
            ag_result = run_graph(st.session_state.agentic_graph, q, "agentic-rag-compare", ["compare"])
            si_result = run_graph(st.session_state.simple_graph,  q, "simple-rag-compare",  ["compare"])

        ag_answer = ag_result.get("final_answer") or "No answer produced."
        si_answer = si_result.get("final_answer") or "No answer produced."
        ag_log    = ag_result.get("search_log", [])
        si_log    = si_result.get("search_log", [])

        with st.chat_message("assistant", avatar=BOT_AVATAR):
            mode_badge("compare")
            col_ag, col_si = st.columns(2)
            with col_ag:
                st.markdown(
                    "<div style='background:#E8F5E9;border-left:4px solid #2E7D32;"
                    "padding:10px 14px;border-radius:8px;margin-bottom:8px;'>"
                    "<b style='color:#1B5E20'>🤖 Agentic RAG</b><br/>"
                    "<span style='color:#4CAF50;font-size:0.8rem'>Iterative retrieval</span>"
                    "</div>", unsafe_allow_html=True)
                st.markdown(ag_answer)
                render_trace(ag_log, expanded=True)
            with col_si:
                st.markdown(
                    "<div style='background:#FFF3E0;border-left:4px solid #E65100;"
                    "padding:10px 14px;border-radius:8px;margin-bottom:8px;'>"
                    "<b style='color:#BF360C'>⚡ Simple RAG</b><br/>"
                    "<span style='color:#FF7043;font-size:0.8rem'>Single search</span>"
                    "</div>", unsafe_allow_html=True)
                st.markdown(si_answer)
                render_trace(si_log, expanded=False)
                st.info("One search. No iteration.", icon="ℹ️")

        st.session_state.chat_history.append({
            "role": "assistant", "mode": "compare",
            "ag_answer": ag_answer, "si_answer": si_answer,
            "ag_log": ag_log, "si_log": si_log,
            "content": f"Agentic: {ag_answer}\n\nSimple: {si_answer}",
        })

    # Flush Langfuse traces to cloud
    try:
        from utils.langfuse_setup import flush_traces
        flush_traces(st.session_state.langfuse)
    except Exception:
        pass

    st.rerun()