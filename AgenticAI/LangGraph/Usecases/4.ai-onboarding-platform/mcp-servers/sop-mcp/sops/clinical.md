# SOP: Clinical Programs Configuration

**Document ID:** SOP-CLN-001
**Version:** v2.8
**Last Reviewed:** 2026-01-30
**Owner:** BOM Clinical Team
**Domain:** clinical

---

## Purpose

Validation rules for Prior Authorization, Utilization Management, Care
Management, and Eligibility sub-sections of the Clinical form.

---

## Section 6.1 — Prior Authorization

### Rule PA-01 — Turnaround time limit (REGULATORY)

**Severity:** fail_fixable
**Field:** 172 (max turnaround days)

If prior authorization is required (Q171 = `Yes`), the maximum turnaround
time (Q172) MUST NOT exceed **14 calendar days** per CMS guidance.

**Formula:** `Q172 <= 14`

**Suggested fix:** Cap turnaround time at 14 days.

---

### Rule PA-02 — Urgent request turnaround

**Severity:** fail_fixable
**Field:** 173 (urgent turnaround hours)

Urgent prior auth requests (Q173) MUST be resolved within **72 hours**
(3 days). This aligns with NCQA standards.

**Formula:** `Q173 <= 72`

**Suggested fix:** Cap urgent turnaround at 72 hours.

---

### Rule PA-03 — PA required but no turnaround set

**Severity:** fail_fixable
**Fields:** 171, 172

If Q171 = `Yes`, Q172 (turnaround days) MUST be provided. Missing
turnaround time creates SLA ambiguity.

---

## Section 6.2 — Utilization Management

### Rule UM-01 — Criteria reference required

**Severity:** fail_fixable
**Field:** 182 (criteria reference URL)

If UM review is required (Q181 = `Yes`), a criteria reference URL (Q182)
MUST be provided. This URL must point to publicly accessible clinical
guidelines (MCG, InterQual, or UHC internal criteria documents).

**Suggested fix:** Prompt IPM to provide a valid criteria URL.

---

### Rule UM-02 — Valid criteria URL format

**Severity:** fail_fixable
**Field:** 182 (criteria reference URL)

The criteria URL (Q182) MUST be a valid HTTPS URL.

**Suggested fix:** Reformat URL or request a valid one.

---

### Rule UM-03 — Concurrent review frequency

**Severity:** warning
**Field:** 183 (concurrent review days)

Concurrent review frequency (Q183) should be between **1 and 7 days** for
acute inpatient stays. Values outside this range may indicate
non-standard configuration.

---

## Section 6.3 — Care Management

### Rule CM-01 — Enrollment criteria required

**Severity:** fail_reject
**Field:** 192 (enrollment criteria ICD codes)

If care management is offered (Q191 = `Yes`), enrollment criteria
(Q192) MUST list at least one valid ICD-10 diagnosis code (format:
letter + 2-3 digits, optionally followed by . and additional digits,
e.g., `E11.9`, `I10`, `J44.0`).

Missing or invalid ICD codes prevent proper member identification.

**Auto-fix:** NOT permitted. Escalate to BOM clinical reviewer.

---

### Rule CM-02 — Contact frequency reasonableness

**Severity:** warning
**Field:** 193 (contact frequency)

For care management programs:
- `weekly` is appropriate for high-acuity (catastrophic, transplant)
- `monthly` is the typical standard
- `quarterly` should be flagged for review (may be too infrequent)

---

## Section 6.4 — Eligibility

### Rule EL-01 — Refresh frequency bounds

**Severity:** fail_fixable
**Field:** 202 (refresh hours)

Eligibility refresh frequency (Q202) MUST be between **1 and 24 hours**.
Values outside this range either:
- Below 1 hour: causes unnecessary load on eligibility systems
- Above 24 hours: violates timely eligibility verification standards

**Suggested fix:** Clamp value to [1, 24].

---

### Rule EL-02 — Retroactive eligibility with batch verification

**Severity:** warning
**Fields:** 201 (verification method), 203 (retroactive)

If retroactive eligibility (Q203) = `Yes`, the verification method
(Q201) should be `real-time` or `batch`, NOT `manual`. Manual
verification with retroactive eligibility creates operational risk.

---

### Rule EL-03 — Real-time verification staleness

**Severity:** warning
**Fields:** 201, 202

If verification method = `real-time`, refresh frequency (Q202) should
be ≤ 4 hours. Longer refresh windows defeat the purpose of real-time
verification.

---

## References

- CMS Final Rule CMS-9123-F (PA turnaround)
- NCQA UM Standards 2026
- ICD-10-CM Official Guidelines for Coding and Reporting
- UHC Internal Policy: Clinical Operations Standards v2.0
