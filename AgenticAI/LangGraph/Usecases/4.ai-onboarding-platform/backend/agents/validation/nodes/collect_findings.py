"""
agents/validation/nodes/collect_findings.py
Node: collect_findings

Final node of the Validation Agent. Logs a summary and passes control
to the Resolution Agent. The findings list itself was populated by
apply_rules_to_answers; this node just adds a summary.
"""
from graph.state import MainState


def collect_findings_node(state: MainState) -> dict:
    """Just log a summary — findings are already in state."""
    findings = state.get("findings", [])

    by_severity: dict[str, int] = {}
    for f in findings:
        by_severity[f.get("severity", "unknown")] = by_severity.get(f.get("severity", "unknown"), 0) + 1

    print(f"[validation.collect_findings] collected {len(findings)} finding(s)")
    for sev, count in by_severity.items():
        print(f"    • {sev}: {count}")

    return {}
