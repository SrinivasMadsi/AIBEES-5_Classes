# 🔐 RAG + PII Guardrails Demo

A Streamlit application demonstrating how a RAG pipeline exposes raw PII (guardrails **OFF**) and how regex-based redaction protects it (guardrails **ON**).

---

## What's new in v2

| Area | v1 | v2 |
|---|---|---|
| **Guardrail patterns** | SSN, phone, email, account, DOB | + credit card, street address, ZIP code |
| **Trigger keywords** | 6 keywords | 14 keywords (adds `mobile`, `address`, `card`, `zip`, `birth` …) |
| **Redaction result** | `(str, bool)` tuple | `RedactionResult` dataclass with per-type counts |
| **Config** | Hard-coded defaults | All overridable via `.env` |
| **LLM temperature** | 0.7 (creative) | 0.1 (deterministic — better for factual RAG) |
| **RAG prompt** | Allowed hallucination | Explicitly forbids inventing PII values |
| **UI** | Basic Streamlit | Polished dark theme, session stats, sample queries, redaction details |
| **requirements.txt** | Very old pinned versions | Updated, compatible versions |

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Google Cloud SDK: https://cloud.google.com/sdk/docs/install
- A GCP project with Vertex AI API enabled

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Authenticate with GCP

```bash
gcloud auth application-default login
```

### 4. Configure environment

Create a `.env` file in the project root:

```env
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# OPTIONAL (recommended for classrooms): run without any cloud setup
USE_VERTEXAI=0
```

**Mode notes**

- `USE_VERTEXAI=0` (default): runs fully locally using keyword retrieval — no GCP creds needed.
- `USE_VERTEXAI=1`: uses Vertex AI (Gemini) + FAISS via LangChain.

### 5. (Optional) Generate the sample PDF

```bash
python pdf_generator.py
```

### 6. Run the app

```bash
streamlit run app.py
```

---

## Using the demo

1. Upload `customer_credit_data_100_records.pdf` via the sidebar.
2. Click **Initialize / Rebuild RAG Index**.
3. Ask a question (use the sample queries in the sidebar as starting points).
4. Toggle **Enable PII Guardrails** and ask the same question again.

### Suggested demo questions

| Intent | Query |
|---|---|
| SSN leak | `Share the SSN of a customer with a good credit score.` |
| Phone leak | `What is the mobile phone number of Customer Profile #4?` |
| Account leak | `What is the account number of the first customer?` |
| Multi-field PII | `What is the full legal name and date of birth of Customer Profile #4?` |

---

## Architecture

```
app.py          ← Streamlit UI + orchestration
├── guardrails.py   ← Regex PII detection & redaction
├── rag_system.py   ← Vertex AI (Gemini) + FAISS retrieval
├── pdf_processor.py← Document loading & chunking
└── config.py       ← Environment-driven configuration
```

---

## File overview

| File | Purpose |
|---|---|
| `app.py` | Main Streamlit application |
| `config.py` | Centralised configuration |
| `guardrails.py` | PII detection and redaction engine |
| `rag_system.py` | RAG pipeline (embeddings + LLM + retrieval) |
| `pdf_processor.py` | PDF/TXT loader and text splitter |
| `pdf_generator.py` | Synthetic customer data PDF generator |
| `requirements.txt` | Python dependencies |

---

## Extending the guardrails

Add a new pattern to the `_PATTERNS` list in `guardrails.py`:

```python
(
    "Passport",
    re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"),
    "[PASSPORT REDACTED]",
),
```

No other changes needed — the pattern is automatically applied during `filter_response()`.
