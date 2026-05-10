# Patient Medical History RAG System

## Simple RAG vs Agentic RAG — side by side

---

## Project Structure

```
patient_history/
├── app.py                    ← Streamlit UI
├── main.py                   ← CLI entry point
├── config.py                 ← All settings and paths
├── requirements.txt
├── graph_simple.png          ← Auto-saved on startup
├── graph_agentic.png         ← Auto-saved on startup
│
├── data/
│   ├── sample_records/       ← Drop patient PDFs here
│   └── faiss_store/          ← Auto-created FAISS index
│
├── graph/
│   ├── state.py              ← ONE RAGState used by both graphs
│   ├── edges.py              ← should_continue (agentic loop edge)
│   └── builder.py            ← build_simple_graph() + build_agentic_graph()
│
├── nodes/
│   ├── rag_search.py         ← FAISS search node (shared by both graphs)
│   ├── rag_simple.py         ← Simple RAG answer node (one LLM call)
│   └── rag_agent.py          ← Agentic RAG: reason node + answer node
│
├── core/
│   ├── vector_store.py       ← FAISS ingest and retrieval
│   └── prompts.py            ← All LLM prompts
│
└── utils/
    ├── llm.py
    ├── embeddings.py
    └── langfuse_setup.py
```

---

## Graph Flows

### Simple RAG
```
START → rag_search → rag_simple → END
```
One search. One LLM call. Done.

### Agentic RAG
```
START → rag_search → rag_reason → should_continue
                          ↑              |
                          |    search again?  → rag_search
                          |
                       final answer? → rag_answer → END
```
The LLM reads search results and decides whether it needs another search.

---

## Loosely Coupled Design

### To remove Simple RAG:
In `graph/builder.py` comment out:
```python
# from nodes.rag_simple import rag_simple_node
# def build_simple_graph(): ...
```
In `app.py` comment out:
```python
# from graph.builder import build_simple_graph
# st.session_state.simple_graph = build_simple_graph()
```

### To remove Agentic RAG:
Same pattern — comment out `build_agentic_graph` import and usage.

---

## Langfuse Graph Visualisation

Both `build_simple_graph()` and `build_agentic_graph()` return compiled
LangGraph `StateGraph` objects. When invoked with `config=make_config(handler, ...)`
from `utils/langfuse_setup.py`, Langfuse records them as graph traces — not
flat spans. In Langfuse → Traces → click any trace → you will see the graph
with nodes and edges visualised.

Simple RAG trace: `__start__ → rag_search → rag_simple → __end__`
Agentic RAG trace: `__start__ → rag_search → rag_reason → rag_search → rag_reason → rag_answer → __end__`

The agentic trace shows the loop visually — how many times it searched before answering.

---

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:
```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

Run UI:
```bash
streamlit run app.py
```

Run CLI:
```bash
python main.py --question "Is it safe to give Ibuprofen to Suresh Babu?" --mode agentic
python main.py --question "What is Ravi Kumar's HbA1c trend?" --mode simple
```

---

## Test Questions That Show the Difference

| Question | Simple RAG | Agentic RAG |
|---|---|---|
| "Is it safe to give Ibuprofen to Suresh Babu?" | Searches "Ibuprofen gout" → may say yes | Searches gout → finds CKD → searches NSAIDs kidney → DANGEROUS |
| "Can Ananya take Aspirin for headache?" | May miss Samter's triad | Searches allergy → confirms bronchospasm → CONTRAINDICATED |
| "What is Ravi Kumar's HbA1c trend?" | Returns one value | Searches discharge → searches lab report → compares both visits |
| "Which patients need urgent follow-up?" | Partial answer | Searches multiple patient records across documents |
