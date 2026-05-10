"""
core/tools.py
─────────────
Tool functions for the Agentic RAG sub-agents.
Pure Python + FAISS retrieval, zero LangGraph imports.

AGENTIC RAG DIFFERENCE FROM REGULAR RAG:
  Regular RAG: one similarity search → LLM answers
  Agentic RAG: the agent DECIDES what to search, reads the results,
               decides what to search NEXT based on what it found,
               and iterates until it has a complete picture.

  These tools are what enable that iterative retrieval loop.
  The agent calls search_patient_records() with different queries
  on each iteration — not the same query every time.

Tool groups:
  RETRIEVER_TOOLS — semantic search over the vector store
  ANALYSER_TOOLS  — structured analysis of retrieved content
  SUMMARISER_TOOLS— produce structured summary sections
  FLAGGER_TOOLS   — identify and prioritise critical issues
"""

from langchain_core.tools import tool
from core.vector_store import search


# ══════════════════════════════════════════════════════════════════════════
# RETRIEVER TOOLS
# ══════════════════════════════════════════════════════════════════════════

@tool
def search_patient_records(query: str) -> str:
    """
    Search all ingested patient medical records using a semantic query.
    Returns the most relevant text chunks from the patient's history.
    Use specific queries for better results, e.g.:
      'diabetes HbA1c blood sugar levels'
      'cardiac medications prescribed'
      'surgical procedures operations history'
      'allergies adverse drug reactions'
    """
    chunks = search(query, k=5)
    if not chunks:
        return "No relevant records found for this query."
    result = f"Search results for '{query}':\n\n"
    for i, chunk in enumerate(chunks, 1):
        result += f"[Excerpt {i}]:\n{chunk}\n\n"
    return result


@tool
def search_by_record_type(record_type: str) -> str:
    """
    Search for a specific type of medical record.
    Use one of: 'lab results', 'prescriptions', 'discharge summary',
    'consultation notes', 'radiology', 'allergies', 'vitals', 'diagnoses'
    Returns relevant chunks for that record type.
    """
    query_map = {
        "lab results":          "laboratory test results blood urine pathology CBC LFT KFT",
        "prescriptions":        "medications prescribed drugs dosage pharmacy",
        "discharge summary":    "discharge summary hospital admission admitted",
        "consultation notes":   "consultation doctor notes clinical assessment",
        "radiology":            "X-ray MRI CT scan ultrasound radiology imaging",
        "allergies":            "allergies adverse reactions drug allergy",
        "vitals":               "blood pressure pulse temperature weight height BMI vitals",
        "diagnoses":            "diagnosis diagnosed condition disease disorder",
    }
    query = query_map.get(record_type.lower(), record_type)
    chunks = search(query, k=4)
    if not chunks:
        return f"No {record_type} records found in the patient's history."
    result = f"Records of type '{record_type}':\n\n"
    for i, chunk in enumerate(chunks, 1):
        result += f"[{i}]: {chunk}\n\n"
    return result


# ══════════════════════════════════════════════════════════════════════════
# ANALYSER TOOLS
# ══════════════════════════════════════════════════════════════════════════

@tool
def search_lab_trends(test_name: str) -> str:
    """
    Search for historical values of a specific lab test to identify trends.
    Examples: 'HbA1c', 'creatinine', 'hemoglobin', 'cholesterol', 'TSH'
    Returns all mentions of that test with values and dates if available.
    """
    chunks = search(f"{test_name} test result value level", k=5)
    if not chunks:
        return f"No historical data found for {test_name}."
    result = f"Historical data for {test_name}:\n\n"
    for i, chunk in enumerate(chunks, 1):
        result += f"[{i}]: {chunk}\n\n"
    return result


@tool
def search_medication_history(medication_name: str) -> str:
    """
    Search for history of a specific medication: when it was prescribed,
    dosage changes, whether it was stopped and why.
    Use generic names when possible, e.g. 'metformin', 'amlodipine'.
    """
    chunks = search(f"{medication_name} prescribed dosage stopped discontinued", k=4)
    if not chunks:
        return f"No records found for medication: {medication_name}."
    result = f"Medication history for {medication_name}:\n\n"
    for i, chunk in enumerate(chunks, 1):
        result += f"[{i}]: {chunk}\n\n"
    return result


# ══════════════════════════════════════════════════════════════════════════
# SUMMARISER TOOLS
# ══════════════════════════════════════════════════════════════════════════

@tool
def retrieve_chronic_conditions() -> str:
    """
    Retrieve all records related to chronic, ongoing, or long-term conditions.
    Use this to build the 'active conditions' section of the patient summary.
    """
    chunks = search("chronic condition ongoing long-term disease diabetes hypertension", k=5)
    if not chunks:
        return "No chronic condition records found."
    return "Chronic condition records:\n\n" + "\n\n".join(f"[{i}]: {c}" for i, c in enumerate(chunks, 1))


@tool
def retrieve_recent_history(timeframe: str = "recent") -> str:
    """
    Retrieve the most recent medical events, visits, or test results.
    Pass timeframe as 'recent', 'last 6 months', or 'last year'.
    Use this to build the 'recent history' section of the summary.
    """
    chunks = search(f"{timeframe} visit consultation test result 2024 2023", k=5)
    if not chunks:
        return f"No {timeframe} history found."
    return f"Recent history ({timeframe}):\n\n" + "\n\n".join(f"[{i}]: {c}" for i, c in enumerate(chunks, 1))


# ══════════════════════════════════════════════════════════════════════════
# FLAGGER TOOLS
# ══════════════════════════════════════════════════════════════════════════

@tool
def search_critical_events() -> str:
    """
    Search for critical medical events: emergency admissions, ICU stays,
    severe adverse reactions, code blue events, or life-threatening diagnoses.
    Use this to populate the 'critical flags' section for the doctor.
    """
    chunks = search("emergency ICU critical severe life-threatening adverse reaction hospital admission", k=5)
    if not chunks:
        return "No critical events found in patient history."
    return "Critical events found:\n\n" + "\n\n".join(f"[{i}]: {c}" for i, c in enumerate(chunks, 1))


@tool
def search_drug_interactions_and_allergies() -> str:
    """
    Search for all known allergies, drug reactions, contraindications,
    and medication warnings in the patient's records.
    Critical for pre-consultation safety check.
    """
    chunks = search("allergy allergic reaction contraindicated drug interaction warning adverse", k=5)
    if not chunks:
        return "No allergy or drug interaction records found."
    return "Allergy and drug interaction records:\n\n" + "\n\n".join(f"[{i}]: {c}" for i, c in enumerate(chunks, 1))


# ── Tool group exports ─────────────────────────────────────────────────────
RETRIEVER_TOOLS  = [search_patient_records, search_by_record_type]
ANALYSER_TOOLS   = [search_lab_trends, search_medication_history]
SUMMARISER_TOOLS = [retrieve_chronic_conditions, retrieve_recent_history]
FLAGGER_TOOLS    = [search_critical_events, search_drug_interactions_and_allergies]
