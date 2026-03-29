"""
Make sure you remove previous faiss_store folder from the directory before running this code.
"""

import os
# Allow multiple OpenMP libraries to coexist; fixes the libiomp5md.dll error.
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import hashlib
import streamlit as st
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import OllamaLLM
import subprocess
import time
import warnings

warnings.filterwarnings("ignore")

# --------------------------
# Setup Ollama Server
# --------------------------
OLLAMA_EXE = r"C:\Users\medsi\AppData\Local\Programs\Ollama\ollama.exe"

# Start Ollama server in background
server = subprocess.Popen(
    [OLLAMA_EXE, "serve"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
time.sleep(5)  # wait for server

# --------------------------
# Models
# --------------------------
embedding_model = OllamaEmbeddings(model="nomic-embed-text")   # embedding model
llm = OllamaLLM(base_url="http://localhost:11434", model="llama3.2:1b")  # LLM for answering

# --------------------------
# Utility Functions
# --------------------------
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return "\n".join([page.get_text() for page in doc])

def compute_md5(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def create_faiss_index(text, index_path):
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    db = FAISS.from_texts(chunks, embedding_model)
    db.save_local(index_path)

def load_or_create_faiss(pdf_file):
    text = extract_text_from_pdf(pdf_file)
    file_hash = compute_md5(text)
    index_path = os.path.join("faiss_store", file_hash)
    os.makedirs("faiss_store", exist_ok=True)

    if not os.path.exists(index_path):
        create_faiss_index(text, index_path)
    return FAISS.load_local(index_path, embedding_model, allow_dangerous_deserialization=True)

# --------------------------
# Streamlit UI
# --------------------------
st.title("📄 Pharma Covigilance PDF Q&A (On-Prem RAG with Ollama)")

uploaded_file = st.file_uploader("Upload a PDF document", type="pdf")
if uploaded_file:
    db = load_or_create_faiss(uploaded_file)

    question = st.text_input("Ask your question:")
    if st.button("Search Document") and question:
        # Step 1: Retrieve top chunks
        similar_chunks = db.similarity_search(question, k=3)

        # Step 2: Build context
        context = "\n\n".join([chunk.page_content.strip() for chunk in similar_chunks])

        # Step 3: Build prompt
        prompt = f"""You are a helpful assistant answering questions from pharmacovigilance documents.
        Use the context below to answer the question as accurately as possible.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """

        # Step 4: Query Ollama LLM
        answer = llm.invoke(prompt)

        # Step 5: Show result
        st.subheader("Refined Answer from Document (via RAG):")
        st.markdown(answer)

# --------------------------
# Cleanup when app exits
# --------------------------
import atexit
atexit.register(lambda: server.terminate())
