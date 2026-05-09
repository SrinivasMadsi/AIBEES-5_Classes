"""
print_graph.py
Renders the LangGraph graph visually using LangGraph's built-in methods.

LangGraph can render the graph in 3 ways:
  1. PNG image  → saved as graph.png (open in any image viewer)
  2. ASCII      → prints directly in terminal (zero setup)
  3. Mermaid    → paste into https://mermaid.live

Usage:
    python print_graph.py
"""

import warnings
warnings.filterwarnings("ignore")

from core.graph import build_graph

app = build_graph()

# ── METHOD 1: PNG Image ───────────────────────────────────────────────────────
print("\n🖼️  Generating graph.png ...")
try:
    app.get_graph().draw_mermaid_png(output_file_path="graph.png")
    print("  ✅ graph.png saved! Open it to see the full visual flow.")
except Exception as e:
    print(f"  ⚠️  PNG generation failed: {e}")
    print("  👉 Run: python -m pip install grandalf  then retry")

# ── METHOD 2: ASCII in terminal ───────────────────────────────────────────────
print("\n" + "="*60)
print("  LANGGRAPH FLOW — ASCII (terminal view)")
print("="*60 + "\n")
print(app.get_graph().draw_ascii())

# ── METHOD 3: Mermaid code ────────────────────────────────────────────────────
print("\n" + "="*60)
print("  LANGGRAPH FLOW — Mermaid")
print("  Paste into https://mermaid.live to visualize")
print("="*60 + "\n")
print(app.get_graph().draw_mermaid())