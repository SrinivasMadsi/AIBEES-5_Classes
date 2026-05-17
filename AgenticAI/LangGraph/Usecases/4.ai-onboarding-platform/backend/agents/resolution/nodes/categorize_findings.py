"""
agents/resolution/nodes/categorize_findings.py
Node: categorize_findings

Sorts findings into buckets by severity:
  • pass:    informational (rule was met)
  • warning: soft issues (no action needed but flagged)
  • fixable: failures that can be auto-corrected
  • reject:  failures requiring human review (regulatory/policy)
"""
from graph.state import MainState


def categorize_findings_node(state: MainState) -> dict:
    """Bucket findings into pass/warning/fixable/reject."""
    findings = state.get("findings", [])

    buckets = {
        "pass":    [],
        "warning": [],
        "fixable": [],
        "reject":  [],
    }

    for f in findings:
        status = f.get("status", "")
        severity = f.get("severity", "")

        if status == "pass":
            buckets["pass"].append(f)
        elif status == "warning" or severity == "warning":
            buckets["warning"].append(f)
        elif severity == "fail_reject":
            buckets["reject"].append(f)
        elif severity == "fail_fixable":
            buckets["fixable"].append(f)
        else:
            buckets["warning"].append(f)

    print(f"[resolution.categorize_findings] sorted findings:")
    print(f"    ✅ pass={len(buckets['pass'])}  ⚠️  warning={len(buckets['warning'])}  🔧 fixable={len(buckets['fixable'])}  🛑 reject={len(buckets['reject'])}")

    return {"finding_categories": buckets}
