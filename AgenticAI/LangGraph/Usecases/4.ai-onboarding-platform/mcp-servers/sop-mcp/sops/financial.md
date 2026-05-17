# SOP: Financial Configuration

**Document ID:** SOP-FIN-001
**Version:** v4.1
**Last Reviewed:** 2026-02-01
**Owner:** BOM Financial Team
**Domain:** financial

---

## Purpose

Validation rules for Out-of-Pocket, Deductible, and Co-pay sub-sections of
the Benefits & Services form. These rules ensure plan financial parameters
are internally consistent and meet regulatory minimums.

---

## Section 5.1 — Out-of-Pocket (OOP)

### Rule OOP-01 — Family OOP minimum ratio

**Severity:** fail_fixable
**Fields:** 141 (individual OOP), 142 (family OOP)

The Family OOP maximum (Q142) MUST be at least **2 times** the Individual
OOP maximum (Q141).

**Formula:** `Q142 >= Q141 * 2`

**Suggested fix:** Set Family OOP = Individual OOP × 2.

---

### Rule OOP-02 — Minimum individual OOP (ACA compliance)

**Severity:** warning
**Field:** 141 (individual OOP)

For ACA-compliant plans, the Individual OOP maximum should not be below
**$5,000**. Values below this are unusual and may indicate a misconfiguration.

---

### Rule OOP-03 — HDHP OOP cap (REGULATORY)

**Severity:** fail_reject
**Field:** 141, 142 (individual and family OOP)

For plans classified as `HDHP`, the OOP maximum MUST NOT exceed:
- Individual: $8,050
- Family: $16,100

These are the 2026 IRS limits. Exceeding them disqualifies the plan from
HSA eligibility and requires BOM compliance review.

**Auto-fix:** NOT permitted. Escalate to BOM analyst.

---

## Section 5.2 — Deductible

### Rule DED-01 — Family deductible ratio

**Severity:** fail_fixable
**Fields:** 151 (individual deductible), 152 (family deductible)

The Family deductible (Q152) MUST be at least **2 times** the Individual
deductible (Q151).

**Formula:** `Q152 >= Q151 * 2`

**Suggested fix:** Set Family deductible = Individual deductible × 2.

---

### Rule DED-02 — Deductible vs OOP relationship

**Severity:** fail_fixable
**Fields:** 151 (individual deductible), 141 (individual OOP)

The Individual deductible (Q151) MUST be less than or equal to the
Individual OOP maximum (Q141).

**Formula:** `Q151 <= Q141`

A deductible higher than the OOP maximum is logically impossible and
indicates a data entry error.

**Suggested fix:** Cap deductible at OOP maximum.

---

### Rule DED-03 — HDHP deductible floor

**Severity:** warning
**Field:** 151 (individual deductible)

For plans classified as `HDHP`, the Individual deductible should be at
least **$1,500** (2026 IRS HDHP minimum). Plans below this threshold may
not qualify as HDHPs.

---

## Section 5.3 — Co-pay

### Rule CP-01 — ER co-pay should exceed office visit

**Severity:** fail_fixable
**Fields:** 161 (office visit), 163 (ER)

The Emergency Room co-pay (Q163) should be at least **4 times** the
Office Visit co-pay (Q161) to discourage non-emergency ER use.

**Formula:** `Q163 >= Q161 * 4`

**Suggested fix:** Set ER co-pay = Office Visit × 4.

---

### Rule CP-02 — Specialist co-pay relationship

**Severity:** warning
**Fields:** 161 (office visit), 162 (specialist)

Specialist co-pay (Q162) typically ranges from **1.5x to 3x** the Office
Visit co-pay. Values outside this range may indicate misconfiguration.

---

### Rule CP-03 — Maximum co-pay limit

**Severity:** fail_reject
**Fields:** 161, 162, 163

No single co-pay may exceed **$500** without BOM compliance approval.
This protects members from unreasonable point-of-service costs.

**Auto-fix:** NOT permitted. Escalate to BOM analyst.

---

## References

- ACA Section 1302 (Essential Health Benefits)
- IRS Notice 2025-12 (HDHP/HSA Limits for 2026)
- UHC Internal Policy: Financial Configuration Standards
