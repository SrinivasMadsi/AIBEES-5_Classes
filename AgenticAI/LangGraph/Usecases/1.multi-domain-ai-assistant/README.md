# Enterprise AI Multi-Agent System — V2 (Modular)
### LangGraph + Gemini + FAISS + SQLite + Langfuse

---

## What Changed from V1

V2 is a modular refactor of V1. Same functionality, better structure.

| V1 | V2 |
|---|---|
| `multi_agent.py` — 580 lines | `multi_agent.py` — 60 lines (entry point only) |
| `tools.py` — all 3 domains mixed | `agents/licensing/tools.py` etc — fully separate |
| No base class — code repeated | `agents/base_agent.py` — shared logic once |
| Config via os.getenv() everywhere | `config/settings.py` — typed singleton |
| Langfuse in multi_agent.py | `observability/tracer.py` — isolated module |

---

## Project Structure

```
enterprise_ai_v2/
├── agents/
│   ├── base_agent.py          ← Abstract base all agents inherit from
│   ├── licensing/             ← Fully self-contained Licensing agent
│   │   ├── agent.py
│   │   ├── tools.py
│   │   └── prompts.py
│   ├── onprem/                ← Fully self-contained OnPrem agent
│   │   ├── agent.py
│   │   ├── tools.py
│   │   └── prompts.py
│   └── kb/                    ← Fully self-contained KB agent
│       ├── agent.py
│       ├── tools.py
│       └── prompts.py
├── core/
│   ├── graph.py               ← LangGraph graph builder
│   ├── supervisor.py          ← Supervisor agent + routing
│   ├── merger.py              ← Response merger node
│   ├── state.py               ← Shared AgentState
│   └── llm.py                 ← LLM factory
├── observability/
│   └── tracer.py              ← Langfuse setup + flush
├── config/
│   └── settings.py            ← Typed config from .env
├── data/                      ← Mock data (SharePoint + KB docs)
├── db/                        ← SQLite database
├── vector_stores/             ← FAISS indexes per domain
├── multi_agent.py             ← Entry point (thin!)
├── vector_store.py            ← FAISS builder
├── create_data.py             ← Creates mock data files
└── requirements.txt
```

---

## Setup

### Step 1 — Install
```bash
python -m pip install -r requirements.txt
```

### Step 2 — Configure
```bash
cp .env.example .env
# Fill in GOOGLE_API_KEY, LANGFUSE keys
```

### Step 3 — Create mock data
```bash
python create_data.py
```

### Step 4 — Setup database
```bash
python db/setup_db.py
```

### Step 5 — Build vector stores
```bash
python vector_store.py
```

### Step 6 — Run
```bash
python multi_agent.py
```

---

## How to Add a New Domain

Only 4 files needed. Zero changes to existing files:

```
agents/cloud/
├── __init__.py
├── prompts.py   ← system prompt
├── tools.py     ← scoped tools
└── agent.py     ← CloudAgent(BaseDomainAgent)
```

Then 2 lines in `core/graph.py`:
```python
graph.add_node("cloud_agent", cloud_agent_node)
graph.add_edge("cloud_agent", "merger")
```

---

## Demo Questions

### Single domain
```
What is a Licensing Smart Account?
What is an OnPrem Smart Account?
What is a KB Smart Account?
```

### Multi domain (showstopper!)
```
What is the difference between a Licensing Smart Account and an OnPrem Smart Account?
Explain Smart Accounts across Licensing, OnPrem and KB domains
```
