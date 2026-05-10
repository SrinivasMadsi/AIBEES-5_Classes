"""
main.py — CLI entry point.

Usage:
  python main.py --question "Is it safe to give Ibuprofen to Suresh Babu?"
  python main.py --question "What is Ravi Kumar's HbA1c trend?" --mode agentic
  python main.py --question "Any allergies for Ananya?" --mode simple

On run:
  1. Ingests any new PDFs in data/sample_records/
  2. Saves graph_simple.png and graph_agentic.png
  3. Runs the selected graph and prints the answer
  4. Flushes Langfuse traces
"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import argparse
from pathlib import Path
from langchain_core.messages import HumanMessage

from graph.builder import build_simple_graph, build_agentic_graph, save_graph_pngs
from core.vector_store import ingest_pdf, get_ingested_files
from utils.langfuse_setup import init_langfuse, make_config, flush_traces
from config import SAMPLE_RECORDS


def auto_ingest():
    """Ingest any PDFs in data/sample_records/ not yet indexed."""
    SAMPLE_RECORDS.mkdir(parents=True, exist_ok=True)
    for pdf in SAMPLE_RECORDS.glob("*.pdf"):
        ok, msg = ingest_pdf(pdf.read_bytes(), pdf.name)
        print(f"  {'✓' if ok else '↷'} {msg}")


def make_state(question: str) -> dict:
    return {
        "question":         question,
        "messages":         [HumanMessage(content=question)],
        "retrieved_context": "",
        "search_log":       [],
        "final_answer":     None,
        "iteration_count":  0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", default="What are Ravi Kumar's active conditions?")
    parser.add_argument("--mode",     default="agentic", choices=["simple", "agentic"])
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  PATIENT MEDICAL HISTORY — RAG SYSTEM")
    print("="*60)

    # Ingest records
    print("\nChecking sample records...")
    auto_ingest()
    files = get_ingested_files()
    print(f"  {len(files)} file(s) in knowledge base: {files[:3]}")

    # Save graph PNGs
    print("\nSaving graph PNGs...")
    save_graph_pngs()

    # Init Langfuse
    langfuse, handler = init_langfuse()

    # Build graph
    graph = build_agentic_graph() if args.mode == "agentic" else build_simple_graph()
    state = make_state(args.question)
    cfg   = make_config(handler,
                        run_name=f"{args.mode}-rag",
                        tags=["patient-history", args.mode, "cli"])

    print(f"\nMode: {args.mode.upper()} RAG")
    print(f"Question: {args.question}\n")

    result = graph.invoke(state, config=cfg)

    print("\n" + "="*60)
    print("  ANSWER")
    print("="*60)
    print(result.get("final_answer", "No answer produced."))

    search_log = result.get("search_log", [])
    if search_log:
        print(f"\n  Searches performed: {len(search_log)}")
        for i, s in enumerate(search_log, 1):
            print(f"    {i}. '{s['query'][:60]}' → {s['chunks']} chunks")

    flush_traces(langfuse)


if __name__ == "__main__":
    main()
