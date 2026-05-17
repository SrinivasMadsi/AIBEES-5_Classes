# SOP: Accumulator Configuration

**Document ID:** SOP-ACC-001
**Version:** v3.2
**Last Reviewed:** 2026-01-15
**Owner:** BOM Accumulator Team
**Domain:** accumulator

---

## Purpose

This Standard Operating Procedure defines the validation rules for the
**General Accumulator** sub-section of the Benefits & Services form. These
rules MUST be applied to every client onboarding submission.

---

## Section 4.1 — General Accumulator Configuration

### Rule ACC-01 — Accumulator activation requires contract year

**Severity:** fail_fixable
**Field:** 122 (contract year start date)

If Q121 *"Does the plan have accumulators?"* = `Yes`, then the contract year
start date (Q122) **MUST** be provided.

**Suggested fix:** Prompt the IPM to provide the contract year start date.

---

### Rule ACC-02 — Contract year alignment (REGULATORY)

**Severity:** fail_reject
**Field:** 122 (contract year start date)

The contract year start date MUST align with one of the standard plan-year
boundaries: **January 1st** or **July 1st** of the calendar year.

Mid-year contract starts (any date other than 01/01 or 07/01) violate CMS
plan-year alignment guidance and require **special exception approval** from
the BOM Compliance team.

**Auto-fix:** NOT permitted. Escalate to BOM analyst for human review.

---

### Rule ACC-03 — Accumulator type validity

**Severity:** fail_fixable
**Field:** 123 (accumulator type)

The accumulator type (Q123) must be one of:
- `family-only`
- `combined`
- `individual-only`

For employer-sponsored group plans, `combined` is the most common
configuration and is the recommended default when ambiguous.

---

### Rule ACC-04 — High-deductible plan accumulator pairing

**Severity:** warning
**Fields:** 121 (accumulators), 151 (individual deductible)

If the plan classification is `HDHP` (High Deductible Health Plan), the
accumulator should typically be set to `Yes`. HDHPs without accumulators
require justification.

---

## References

- CMS Plan Year Guidance, 45 CFR § 156.140
- UHC Internal Policy: Accumulator Configuration v2.3
