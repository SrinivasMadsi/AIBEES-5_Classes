# Testing Scenarios — AI_Onboarding_Platform

This guide walks you through testing every path through the system. Each
scenario gives you exact values to enter, what to watch for, and what to
expect — so you can verify your local setup is working correctly and see
each concept in action.

> **Suggested order:** Work through Scenarios 1 → 2 → 3 → 4 in sequence.
> Each one demonstrates a different verdict path and builds on the
> previous. Scenarios 5 and 6 are bonus paths you can explore on your own.

---

## Before you start

Make sure your environment is running:

- Backend running on port 8000 (`uvicorn main:app --reload --port 8000`)
- Frontend running on port 5173 (`npm run dev`)
- Database connection works (`python scripts/test_db.py`)
- MCP server reachable (`python scripts/test_mcp.py`)

Keep your **backend terminal visible** while testing — that's where you'll
see the agent logs scrolling.

---

## Scenario 1 — Happy Path (verdict: PASS)

**Goal:** Submit a clean, well-formed configuration and see all three
agents run successfully to completion with no findings.

### Setup
- **Form:** Benefits & Services (form_id 1005)
- **Client:** Innova Tech Solutions (plan year starts 07/01)
- **Submitted by:** `ipm@healthcare.com`

### Values to enter

#### General Accumulator
| Question | Value |
|---|---|
| Q121 — Does the plan have accumulators? | **Yes** |
| Q122 — Contract year start date | **2026-07-01** |
| Q123 — Accumulator type | **combined** |

#### Out of Pocket
| Question | Value |
|---|---|
| Q141 — Individual OOP maximum | **6000** |
| Q142 — Family OOP maximum | **12000** |
| Q143 — Does OOP include prescription drugs? | **Yes** |

#### Deductible
| Question | Value |
|---|---|
| Q151 — Individual deductible | **2000** |
| Q152 — Family deductible | **4000** |
| Q153 — Does deductible reset on plan year boundary? | **Yes** |

#### Co-pay
| Question | Value |
|---|---|
| Q161 — Office visit co-pay | **25** |
| Q162 — Specialist co-pay | **50** |
| Q163 — Emergency room co-pay | **150** |

### Steps
1. Click **Save Submission**
2. Click **Validate Now**
3. Watch the backend logs as the agents run
4. Wait for the redirect to the Validation Results page

### Expected outcome

| Field | Value |
|---|---|
| Verdict | `PASS` |
| Plan type | `PPO` or `HDHP` (depends on LLM classification) |
| Final status | `validated_pass` |
| Findings | All pass (or warnings only) |
| Human reviews | 0 |
| Iteration count | 0 |

### What to look for in the backend logs

You should see all three agents executing in order:

```
[intake.parse_submission] parsed N answers
[intake.check_completeness] ✅ all required filled
[intake.classify_plan_type] → PPO (or HDHP)
[intake.detect_risk_signals] → N signal(s)
[intake.group_by_domain] → grouped into 2 domain(s)

[validation.fetch_sops_via_mcp] 🔌 calling sop-mcp server for 2 domain(s)...
    🔌 [accumulator] received 4 rule(s) from sop-mcp
    🔌 [financial] received 9 rule(s) from sop-mcp
[validation.apply_rules_to_answers] applied N rules
[validation.collect_findings] collected N finding(s)

[resolution.categorize_findings] sorted findings
[resolution.review_suggestions] verdict=PASS
[resolution.mark_validated] ✅ final_status=validated_pass

[finalize] persisted submission=... status=validated_pass
```

### What this scenario shows

- The full multi-agent pipeline runs end-to-end
- The `🔌 calling sop-mcp server` line confirms the agent is fetching SOPs
  via MCP (not reading files directly)
- The submission moves to `validated_pass` status with no human
  intervention needed
- Open Langfuse Cloud and check the latest trace — you'll see the
  hierarchical structure: main graph → each agent subgraph → individual nodes

---

## Scenario 2 — Auto-Correction (verdict: FAIL_FIXABLE)

**Goal:** Submit a configuration with a fixable issue. Watch the agent
detect it, generate a patch, apply it, and re-validate successfully.

### Setup
- **Form:** Benefits & Services (form_id 1005)
- **Client:** ACME Healthcare (plan year starts 01/01)

### Values to enter

#### General Accumulator
| Question | Value |
|---|---|
| Q121 — Does the plan have accumulators? | **Yes** |
| Q122 — Contract year start date | **2026-01-01** |
| Q123 — Accumulator type | **combined** |

#### Out of Pocket
| Question | Value |
|---|---|
| Q141 — Individual OOP maximum | **6000** |
| Q142 — Family OOP maximum | **12000** |
| Q143 — Does OOP include prescription drugs? | **Yes** |

#### Deductible — **⚠️ intentional issue here**
| Question | Value | Issue |
|---|---|---|
| Q151 — Individual deductible | **3000** | |
| Q152 — Family deductible | **4000** | ❌ Should be ≥ 6000 per rule DED-01 |
| Q153 — Does deductible reset on plan year boundary? | **Yes** | |

#### Co-pay
| Question | Value |
|---|---|
| Q161 — Office visit co-pay | **30** |
| Q162 — Specialist co-pay | **60** |
| Q163 — Emergency room co-pay | **200** |

### Expected outcome

| Field | Value |
|---|---|
| Verdict | `FAIL_FIXABLE` (first iteration), then `PASS` (second iteration) |
| Final status | `validated_with_fixes` |
| Findings | DED-01 fails first time, passes on retry |
| Patch applied | Q152: 4000 → 6000 |
| Iteration count | 1 |

### What to look for in the backend logs

You should see the validation run **twice** because of the self-correction loop:

```
First iteration:
[resolution.review_suggestions] verdict=FAIL_FIXABLE
[resolution.apply_auto_fixes] applied 1 patch(es), iteration → 1
    🔧 patched Q152: → 6000 (rule DED-01)
[main_router] FAIL_FIXABLE iter=1<1 — looping back to validation
... wait — iter becomes 1 which is NOT < 1, so it goes to finalize

(With MAX_SELF_CORRECTION_ITERATIONS=1, the loop runs once and finalizes
with the corrected values.)
```

### What this scenario shows

- **Self-correction grounded in deterministic data** — the LLM doesn't
  invent the new value `6000`; it comes from the SOP rule's
  `expected_value` field
- The Resolution Agent generates a **structured patch** (`update_field`
  with field_id and new_value), not natural language
- The Critic reviews the patch before applying it
- The main graph's conditional edge routes back to Validation for retry
- Inspect the findings on the result page — DED-01 will be marked as
  `auto_applied: true` with cyan "AUTO-FIXED" badge

---

## Scenario 3 — Human-in-the-Loop Escalation (verdict: FAIL_REJECT)

**Goal:** Submit a configuration with a regulatory violation. The agent
correctly refuses to auto-correct it and escalates to a BOM analyst for
human review.

### Setup
- **Form:** Benefits & Services (form_id 1005)
- **Client:** GlobalCorp Industries (high-risk client)

### Values to enter

#### General Accumulator — **⚠️ regulatory violation here**
| Question | Value | Issue |
|---|---|---|
| Q121 — Does the plan have accumulators? | **Yes** | |
| Q122 — Contract year start date | **2026-04-15** | ❌ Mid-year — fails ACC-02 (regulatory) |
| Q123 — Accumulator type | **combined** | |

#### Out of Pocket
| Question | Value |
|---|---|
| Q141 — Individual OOP maximum | **5500** |
| Q142 — Family OOP maximum | **11000** |
| Q143 — Does OOP include prescription drugs? | **Yes** |

#### Deductible
| Question | Value |
|---|---|
| Q151 — Individual deductible | **2500** |
| Q152 — Family deductible | **5000** |
| Q153 — Does deductible reset on plan year boundary? | **Yes** |

#### Co-pay
| Question | Value |
|---|---|
| Q161 — Office visit co-pay | **20** |
| Q162 — Specialist co-pay | **40** |
| Q163 — Emergency room co-pay | **120** |

### Phase A — IPM submits

1. Save the submission and click **Validate Now**
2. Wait for the validation to complete

### Expected outcome — Phase A

| Field | Value |
|---|---|
| Verdict | `FAIL_REJECT` |
| Final status | `pending_human_review` |
| Findings | ACC-02 marked as `fail_reject` severity |
| Human reviews created | 1 (for ACC-02) |
| What you see in the UI | Pink "Pending BOM Analyst Review" banner |

### Phase B — Switch to BOM analyst role

Now you'll act as the BOM analyst reviewing the escalated item.

1. In the left sidebar, click **Review Queue** (under "BOM Analyst")
2. You should see one pending review for GlobalCorp Industries
3. Click the review to open the detail page
4. Notice the side-by-side display:
   - The IPM's submitted value: `2026-04-15`
   - The agent's recommendation: reject due to fail_reject severity
   - The rule that triggered it: contract year must align with plan year
5. Choose one of three actions:

#### Option 5a — Override with comment
- Type comment: `Mid-year start approved by compliance team per exception ticket #4521`
- Click **Override with comment**
- The review is recorded as `overridden`
- Submission status becomes `approved`

#### Option 5b — Reject
- Type comment: `Mid-year start not permissible per CMS guidance. Please update.`
- Click **Reject (send back to IPM)**
- The review is recorded as `rejected`
- Submission status becomes `rejected`

#### Option 5c — Approve as-is
- Click **Approve as-is** (no comment needed)
- The review is recorded as `approved`
- Submission status becomes `approved`

### What to look for in the backend logs

When you submit a decision, you'll see in the backend logs:

```
INFO: 127.0.0.1 - "POST /api/reviews/N/decision HTTP/1.1" 200
```

If you then check the `business_data.audit_log` table in Neon, you'll see
a new row with `event_type='human_decision'` recording your action.

### What this scenario shows

- The agent **doesn't bypass regulatory rules** — it correctly identifies
  what needs human judgment and stops there
- Regulatory failures get marked with `fail_reject` severity (red
  "ESCALATED" badge)
- The submission state persists in `pending_human_review` indefinitely —
  you can close the backend, restart it, and the pending review is still
  there
- Three decision paths (approve / reject / override) give the BOM analyst
  flexibility to handle real-world cases
- Every decision is logged in `business_data.audit_log` with the
  reviewer's identity, decision, and comment — full compliance trail

---

## Scenario 4 — Fault Tolerance (crash + resume)

**Goal:** Crash the backend mid-validation and verify the system resumes
from where it left off instead of starting over.

### Setup
- Use any client and any of the form values from Scenario 1 (a clean
  happy path is easiest to observe)

### Steps

1. Fill out the form for **Sunrise Financial Group** with Scenario 1 values
2. Click **Save Submission**
3. Click **Validate Now**
4. **Watch the backend terminal carefully**
5. As soon as you see this line:
   ```
   [validation.fetch_sops_via_mcp] 🔌 calling sop-mcp server...
   ```
   immediately press **Ctrl+C** in the backend terminal to kill the process
6. Wait 3 seconds
7. Restart the backend:
   ```
   poetry run uvicorn main:app --reload --port 8000
   ```
8. In the UI, navigate to the submission's detail page (or click into it
   from the Submissions list)
9. Click the **Re-validate** button at the top right
10. Watch the logs

### Expected outcome

| Phase | What happens |
|---|---|
| Before crash | Intake completed, Validation started, then process killed |
| After restart + Re-validate | Pipeline resumes from the checkpoint, doesn't re-run Intake from scratch |
| Final state | Submission completes normally, same as if no crash happened |

### What to look for in the backend logs

After restart, when you click Re-validate, you should **not** see the
Intake Agent logs again (because that work was already checkpointed).
The logs jump straight to where the crash happened:

```
[validation.fetch_sops_via_mcp] 🔌 calling sop-mcp server for 2 domain(s)...
    🔌 [accumulator] received 4 rule(s) from sop-mcp
    🔌 [financial] received 9 rule(s) from sop-mcp
[validation.apply_rules_to_answers] applied N rules
...
```

If you see Intake logs running again, the resume didn't work as expected.

### What this scenario shows

- **PostgresSaver checkpoints state after every node**, including inside
  subgraphs
- Crashes mid-execution don't lose work — the graph picks up from the
  last successful checkpoint
- The `thread_id` for each submission persists in Postgres, so resuming
  is just a matter of invoking the graph with the same thread ID
- In production, this means deploys mid-day, network blips, and database
  hiccups won't cause work loss

### To verify checkpointing directly

In Neon SQL Editor:

```sql
SELECT thread_id, count(*) AS checkpoint_count
FROM public.checkpoints
GROUP BY thread_id
ORDER BY checkpoint_count DESC
LIMIT 10;
```

You'll see one row per `thread_id` (one per submission) with the
checkpoint count. Each row is one node execution that was persisted.

---

## Scenario 5 — Incomplete Submission (fast-fail)

**Goal:** Submit a form with required fields missing. Watch the Intake
Agent fast-fail before any expensive LLM or MCP calls happen.

### Setup
- **Form:** Benefits & Services (form_id 1005)
- **Client:** MediRx Pharmaceuticals

### Values to enter — **⚠️ leave required fields blank**

| Question | Value | Why it should be filled |
|---|---|---|
| Q121 — Does the plan have accumulators? | **Yes** | |
| Q122 — Contract year start date | _(LEAVE BLANK)_ | ❌ Required because Q121=Yes |
| Q123 — Accumulator type | _(LEAVE BLANK)_ | ❌ Required because Q121=Yes |
| All OOP/Deductible/Copay questions | (fill normally with any values) | |

### Expected outcome

| Field | Value |
|---|---|
| Verdict | `INCOMPLETE` |
| Final status | `rejected` |
| Pipeline stopped at | `intake_agent / check_completeness` node |
| Validation Agent | Never ran |
| Resolution Agent | Never ran |

### What to look for in the backend logs

```
[intake.parse_submission] parsed N answers
[intake.check_completeness] ❌ N/M required filled (X%)
[intake.return_incomplete_error] ❌ 2 required field(s) missing — halting
[finalize] persisted submission=... status=rejected
```

Notice the absence of:
- Any LLM calls (no `classify_plan_type` or `detect_risk_signals` logs)
- Any MCP calls (no `🔌 calling sop-mcp server` logs)
- Any Validation or Resolution Agent activity

### What this scenario shows

- **Fast-fail design** — the agent catches missing required data in
  milliseconds, before spending any LLM tokens or making any MCP calls
- The conditional edge in the Intake Agent (`_route_after_completeness`)
  routes to `return_incomplete_error` when fields are missing
- This is a cost-saving pattern: validate cheap things first, expensive
  things last
- The submission ends with `final_status=rejected` and the IPM would
  need to fix the missing fields and resubmit

---

## Scenario 6 — Clinical Form (multi-form support)

**Goal:** Submit a Clinical form (form_id 2005) to demonstrate that the
same agent architecture handles different form types using different
SOPs.

### Setup
- **Form:** Clinical (form_id 2005)
- **Client:** ACME Healthcare

### Values to enter

#### Prior Authorization — **⚠️ intentional issue here**
| Question | Value | Issue |
|---|---|---|
| Q171 — Is PA required for specialty drugs? | **Yes** | |
| Q172 — Maximum turnaround time (days) | **21** | ❌ Should be ≤ 14 (rule PA-01) |
| Q173 — Urgent request turnaround (hours) | **48** | ✅ OK |

#### Utilization Management
| Question | Value |
|---|---|
| Q181 — Is UM review required? | **Yes** |
| Q182 — Criteria reference URL | **https://healthcare.com/clinical-criteria** |
| Q183 — Concurrent review frequency (days) | **3** |

#### Care Management — **⚠️ another intentional issue**
| Question | Value | Issue |
|---|---|---|
| Q191 — Is care management offered? | **Yes** | |
| Q192 — Enrollment criteria diagnoses | **diabetes, hypertension** | ❌ Should be ICD-10 codes, not plain words |
| Q193 — Contact frequency | **monthly** | |

#### Eligibility
| Question | Value |
|---|---|
| Q201 — Verification method | **real-time** |
| Q202 — Refresh frequency (hours) | **4** |
| Q203 — Allow retroactive eligibility? | **No** |

### Expected outcome

| Field | Value |
|---|---|
| Verdict | `FAIL_REJECT` (CM-01 needs human review) |
| Findings | PA-01 (fixable), CM-01 (reject) |
| Auto-fix applied | Q172: 21 → 14 |
| Human reviews | 1 (for invalid ICD codes in Q192) |

### What to look for in the backend logs

This time the Validation Agent fetches the **clinical** SOP, not the
financial one:

```
[validation.fetch_sops_via_mcp] 🔌 calling sop-mcp server for 1 domain(s)...
    🔌 [clinical] received 11 rule(s) from sop-mcp
```

To fix the ICD code issue, you'd enter values like `E11.9, I10`
(diabetes mellitus, hypertension) instead of plain English.

### What this scenario shows

- The **same agent architecture** handles multiple form types
- Different forms load different SOPs via MCP — the agent code doesn't
  change, only the SOP retrieved changes
- The clinical SOP enforces different rules (ICD-10 format checks, PA
  turnaround limits) than the financial SOP
- Adding a new form is a data change (insert into `business_data.forms`
  and add a new SOP markdown file), not a code change

---

## Reference — All Validation Rules

For constructing your own custom test cases, here's the complete rule
inventory across the 3 SOPs:

### Accumulator SOP (4 rules)

| Rule ID | Severity | Check |
|---|---|---|
| ACC-01 | fail_fixable | If Q121=Yes, Q122 must be provided |
| ACC-02 | **fail_reject** | Q122 must be 01/01 or 07/01 of any year |
| ACC-03 | fail_fixable | Q123 must be `family-only` / `combined` / `individual-only` |
| ACC-04 | warning | HDHP accumulator pairing |

### Financial SOP (9 rules)

| Rule ID | Severity | Check |
|---|---|---|
| OOP-01 | fail_fixable | Q142 ≥ Q141 × 2 (family ≥ 2× individual) |
| OOP-02 | warning | Q141 ≥ 5000 (ACA recommended minimum) |
| OOP-03 | **fail_reject** | HDHP OOP cap (Q141 ≤ 8050) |
| DED-01 | fail_fixable | Q152 ≥ Q151 × 2 |
| DED-02 | fail_fixable | Q151 ≤ Q141 (deductible ≤ OOP) |
| DED-03 | warning | HDHP deductible floor (Q151 ≥ 1500) |
| CP-01 | fail_fixable | Q163 ≥ Q161 × 4 (ER ≥ 4× office visit) |
| CP-02 | warning | Specialist co-pay 1.5–3× office |
| CP-03 | **fail_reject** | No co-pay over $500 |

### Clinical SOP (11 rules)

| Rule ID | Severity | Check |
|---|---|---|
| PA-01 | fail_fixable | Q172 ≤ 14 days |
| PA-02 | fail_fixable | Q173 ≤ 72 hours |
| PA-03 | fail_fixable | If Q171=Yes, Q172 required |
| UM-01 | fail_fixable | If Q181=Yes, Q182 required |
| UM-02 | fail_fixable | Q182 must be a valid HTTPS URL |
| UM-03 | warning | Q183 between 1–7 days |
| CM-01 | **fail_reject** | Q192 must contain valid ICD-10 codes |
| CM-02 | warning | Q193 frequency reasonableness |
| EL-01 | fail_fixable | Q202 between 1–24 hours |
| EL-02 | warning | Retroactive + verification method check |
| EL-03 | warning | Real-time + slow refresh check |

---

## Troubleshooting

### My logs don't show the expected output

- Make sure the backend terminal is showing logs (`uvicorn` should be
  running with `--reload`)
- Check that the database connection works (`python scripts/test_db.py`)
- Verify the MCP server is reachable (`python scripts/test_mcp.py`)

### Validation completes but no findings appear

- Open the Validation Results page for the submission and refresh
- Check the database directly:
  ```sql
  SELECT * FROM business_data.findings
  WHERE submission_id = '<your_submission_id>';
  ```

### Scenario 4 doesn't resume cleanly

- The crash needs to happen *during* a node execution, not between nodes
- If you wait too long, the validation may complete before you can kill it
- Try killing during the LLM-heavy nodes (`classify_plan_type` or
  `detect_risk_signals`) which take longer

### LLM classification gives a different plan_type than expected

- The LLM uses pattern reasoning over the answers — different combinations
  of answers can yield different classifications
- Both `PPO` and `HDHP` are valid outcomes for Scenario 1's values
- This is expected behavior, not a bug

### The system says "Submission already exists"

- The frontend prevents creating a second submission for the same client
  + form combination
- Either edit the existing submission or change the client