"""
scripts/smoke_test.py
End-to-end agent run from the CLI, no UI required.
Run:  python scripts/smoke_test.py
"""
import json
import sys
import uuid
from pathlib import Path

# Add backend/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from core.tracer import tracer
from graph import get_graph, initial_state


SAMPLE_REQUESTS = [
    "Need 5 Dell Latitude 5450 laptops, 5 Logitech MX Master mice, and 5 Logitech K380 keyboards "
    "for the Hyderabad office. Charge to budget PO-2026-Q2-0847.",

    "Order 3 Lenovo ThinkPad T14 Gen 4 laptops for Sales Bangalore office. "
    "Use budget PO-2026-Q2-0445.",
]


def run_one(message: str):
    thread_id = f"smoke-{uuid.uuid4().hex[:8]}"
    config = {
        "configurable": {"thread_id": thread_id},
        **tracer.build_config(
            run_name="smoke-test",
            session_id=thread_id,
            user_id="smoke-tester",
            tags=["smoke-test"],
        ),
    }

    state = initial_state(message, max_iterations=settings.max_self_correction_iterations)

    print("\n" + "=" * 70)
    print(f"REQUEST: {message}")
    print("=" * 70)

    graph = get_graph(use_checkpointer=True)
    result = graph.invoke(state, config=config)

    print("\n" + "=" * 70)
    print(f"RESULT (thread={thread_id})")
    print("=" * 70)
    print(f"Verdict      : {result.get('verdict')}")
    print(f"Final status : {result.get('final_status')}")
    print(f"Iterations   : {result.get('iteration_count')}")
    print(f"\nCritic summary:\n  {result.get('critic_summary', '')[:500]}")

    print("\nFindings:")
    for f in result.get("findings", []):
        marker = {"pass": "✓", "fail": "✗", "warning": "!"}.get(f["status"], "·")
        print(f"  {marker} [{f['check_name']}] {f['finding'][:100]}")

    if result.get("final_po"):
        print(f"\nFinal PO total: ₹{result['final_po'].get('total_amount', 0):,.2f}")

    tracer.flush()


def main():
    for msg in SAMPLE_REQUESTS:
        run_one(msg)


if __name__ == "__main__":
    main()
