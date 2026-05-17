"""
agents/intake/nodes/group_by_domain.py
Node: group_by_domain

Splits the parsed answers into validation domains. The Validation Agent
will fetch a different SOP per domain.

Mapping of sub_section_id to domain:
  1110050 (General Accumulator)     → accumulator
  1110052 (Out of Pocket)            → financial
  1110053 (Deductible)               → financial
  1110054 (Co-pay)                   → financial
  1110080 (Prior Authorization)      → clinical
  1110081 (Utilization Management)   → clinical
  1110082 (Care Management)          → clinical
  1110083 (Eligibility)              → clinical
"""
from graph.state import MainState

SUB_SECTION_TO_DOMAIN = {
    1110050: "accumulator",
    1110052: "financial",
    1110053: "financial",
    1110054: "financial",
    1110080: "clinical",
    1110081: "clinical",
    1110082: "clinical",
    1110083: "clinical",
}


def group_by_domain_node(state: MainState) -> dict:
    """Group answer field_ids by validation domain."""
    parsed_answers = state.get("parsed_answers", {})

    domain_groups: dict[str, dict] = {
        "accumulator": {"field_ids": [], "sub_section_ids": [], "sub_section_names": []},
        "financial":   {"field_ids": [], "sub_section_ids": [], "sub_section_names": []},
        "clinical":    {"field_ids": [], "sub_section_ids": [], "sub_section_names": []},
    }

    for section in parsed_answers.get("sections", []):
        for sub in section.get("sub_sections", []):
            sub_id = sub["sub_section_id"]
            domain = SUB_SECTION_TO_DOMAIN.get(sub_id)
            if not domain:
                continue

            domain_groups[domain]["sub_section_ids"].append(sub_id)
            domain_groups[domain]["sub_section_names"].append(sub["sub_section_name"])

            for ans in sub.get("answers", []):
                domain_groups[domain]["field_ids"].append(ans["question_id"])

    # Remove empty domains
    domain_groups = {k: v for k, v in domain_groups.items() if v["field_ids"]}

    print(f"[intake.group_by_domain] → grouped into {len(domain_groups)} domain(s):")
    for domain, info in domain_groups.items():
        print(f"    • {domain}: {len(info['field_ids'])} fields across {len(info['sub_section_ids'])} sub-sections")

    return {"domain_groups": domain_groups}
