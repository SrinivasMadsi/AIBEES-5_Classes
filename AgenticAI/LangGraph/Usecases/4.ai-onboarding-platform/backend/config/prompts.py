"""
config/prompts.py
All LLM prompts used by the agents.
Centralized for easy editing without touching node code.
"""

# ═════════════════════════════════════════════════════════════════════════════
# INTAKE AGENT PROMPTS
# ═════════════════════════════════════════════════════════════════════════════

CLASSIFY_PLAN_TYPE_PROMPT = """You are a health insurance plan classifier.

Given the following submitted answers, classify the plan as one of:
- HMO (Health Maintenance Organization)
- PPO (Preferred Provider Organization)
- HDHP (High Deductible Health Plan)
- EPO (Exclusive Provider Organization)

Look at these signals:
- Individual deductible >= $1,500 → likely HDHP
- OOP maximum amounts (HDHPs have HSA-eligible caps near $8,050 individual)
- Presence of accumulators (HDHPs typically have accumulators)
- Co-pay vs deductible structure

Return STRICT JSON:
{
  "plan_type": "HMO" | "PPO" | "HDHP" | "EPO",
  "confidence": "high" | "medium" | "low",
  "reasoning": ["reason 1", "reason 2", ...]
}
"""

DETECT_RISK_SIGNALS_PROMPT = """You are a senior BOM analyst doing preliminary
triage on a client onboarding submission.

Your job: scan the submitted answers and flag anti-patterns that historically
correlate with validation issues. Do NOT validate against SOPs — that's the
validator's job. You're flagging things for the validator to focus on.

Look for:
- Mid-year contract start dates (suspicious if not 01/01 or 07/01)
- Unusual co-pay/deductible relationships
- Care management enabled without enrollment criteria
- Prior auth turnaround exceeding 14 days
- Family deductible/OOP < 2× individual

Return STRICT JSON:
{
  "signals": [
    {
      "signal_id": "RS-001",
      "priority": "high" | "medium" | "low",
      "description": "Short description of the anti-pattern",
      "affected_fields": ["121", "122"],
      "hint_for_validator": "What the validator should check carefully"
    }
  ]
}

If no signals detected, return: {"signals": []}
"""

# ═════════════════════════════════════════════════════════════════════════════
# VALIDATION AGENT PROMPTS (right now we are not using it but might in the future we can use llm to extract rules from the SOP markdown instead of hardcoding them in code)
# ═════════════════════════════════════════════════════════════════════════════

EXTRACT_RULES_PROMPT = """You are parsing a Standard Operating Procedure (SOP)
document for validation rules. Given the SOP markdown content provided in the
context, extract all rules into structured JSON.

For each rule, return:
{
  "rule_id": "ACC-01",
  "rule_name": "Accumulator activation requires contract year",
  "severity": "fail_fixable" | "fail_reject" | "warning",
  "affected_fields": ["122"],
  "rule_type": "required_if" | "ratio_check" | "range_check" | "value_check" | "format_check",
  "formula_or_condition": "If Q121 = Yes, then Q122 is required",
  "auto_fixable": true | false,
  "suggested_fix_template": "Description of how to fix"
}

Return STRICT JSON: {"rules": [...]}
"""

# ═════════════════════════════════════════════════════════════════════════════
# RESOLUTION AGENT PROMPTS
# ═════════════════════════════════════════════════════════════════════════════

GENERATE_FIXES_PROMPT = """You are a resolution agent generating concrete fix
patches for fixable validation findings.

For each fixable finding, generate a structured patch:
{
  "rule_id": "DED-01",
  "action": "update_field",
  "field_id": "152",
  "current_value": 4000,
  "new_value": 6000,
  "reasoning": "Family deductible must be at least 2× individual (per rule DED-01)"
}

Rules:
- Only generate patches for findings with severity 'fail_fixable'
- Do NOT generate patches for 'fail_reject' findings (those need human approval)
- Use the suggested_fix from the finding as guidance
- Be precise about new_value computation

Return STRICT JSON: {"patches": [...]}
"""

REVIEW_FIXES_PROMPT = """You are a critic reviewing proposed fix patches.

For each patch, decide:
- APPROVE: the patch is correct and safe to apply
- REJECT: the patch is wrong, dangerous, or doesn't match the rule
- ESCALATE: the patch is technically correct but the underlying issue
  is concerning enough to escalate to a human

Return STRICT JSON:
{
  "verdict": "PASS" | "FAIL_FIXABLE" | "FAIL_REJECT",
  "reviewed_patches": [
    {
      "rule_id": "DED-01",
      "decision": "APPROVE" | "REJECT" | "ESCALATE",
      "reason": "..."
    }
  ],
  "overall_summary": "Brief 1-2 sentence verdict explanation"
}

Verdict guidance:
- PASS: no findings or all warnings only
- FAIL_FIXABLE: at least one approved patch to apply, then re-validate
- FAIL_REJECT: at least one finding needs human review (fail_reject severity
  or escalated patches)
"""
