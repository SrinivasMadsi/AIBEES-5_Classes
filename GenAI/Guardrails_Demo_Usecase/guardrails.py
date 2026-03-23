"""
PII Guardrail System — Enhanced Version
Detects and redacts Personally Identifiable Information from RAG responses.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Pattern


@dataclass
class RedactionResult:
    """Structured result from a filter_response call."""
    original: str
    redacted: str
    was_modified: bool
    redaction_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def summary(self) -> str:
        if not self.was_modified:
            return "No PII detected."
        parts = [f"{k}: {v}" for k, v in self.redaction_counts.items() if v > 0]
        return "Redacted — " + ", ".join(parts)


class PIIGuardrail:
    """
    Regex-based guardrail for detecting and redacting PII in LLM responses.

    Improvements over v1:
    - Added credit card, address, and ZIP code patterns
    - Extended trigger keywords (mobile, address, card, zip, dob, birth)
    - Returns structured RedactionResult with per-type counts
    - Centralised pattern registry — easy to extend
    - Input sanitisation (handles None gracefully)
    """

    # ------------------------------------------------------------------
    # PII Pattern Registry: (label, compiled_pattern, replacement_token)
    # ------------------------------------------------------------------
    _PATTERNS: List[Tuple[str, Pattern, str]] = [
        (
            "SSN",
            re.compile(r"(?<!\d)\d{3}[\s\-]?\d{2}[\s\-]?\d{4}(?!\d)"),
            "[SSN REDACTED]",
        ),
        (
            "Phone",
            re.compile(
                r"""
                (?:
                  \(\s*\d{3}\s*\)\s*\d{3}[\s\-]?\d{4}
                  |
                  \b\d{3}[\s\-]\d{3}[\s\-]\d{4}\b
                )
                """,
                re.VERBOSE,
            ),
            "[PHONE REDACTED]",
        ),
        (
            "Email",
            re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
            "[EMAIL REDACTED]",
        ),
        (
            "AccountNumber",
            re.compile(r"\bA\s*C\s*C\s*[\s\-]?\d{8,}\b"),
            "[ACCOUNT REDACTED]",
        ),
        (
            "CreditCard",
            re.compile(r"\b(?:\d{4}[\s\-]){3}\d{4}\b"),
            "[CARD REDACTED]",
        ),
        (
            "DateOfBirth",
            re.compile(
                r"(?:"
                r"(?:January|February|March|April|May|June|July|August|"
                r"September|October|November|December)\s+\d{1,2},\s+\d{4}"
                r"|"
                r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b"
                r")"
            ),
            "[DOB REDACTED]",
        ),
        (
            "ZipCode",
            re.compile(r"\b\d{5}(?:-\d{4})?\b"),
            "[ZIP REDACTED]",
        ),
        (
            "StreetAddress",
            re.compile(
                r"\b\d{1,5}\s+(?:[A-Za-z0-9#&'.\-]+\s){1,5}"
                r"(?:Street|St|Avenue|Ave|Drive|Dr|Road|Rd|Lane|Ln|"
                r"Boulevard|Blvd|Court|Ct|Place|Pl|Way|Circle|Cir)\b",
                re.IGNORECASE,
            ),
            "[ADDRESS REDACTED]",
        ),
    ]

    # Keywords that suggest the user is requesting PII
    _PII_TRIGGER_KEYWORDS: List[str] = [
        "ssn",
        "social security",
        "dob",
        "date of birth",
        "birth",
        "phone",
        "mobile",
        "cell",
        "email",
        "account",
        "address",
        "credit card",
        "card number",
        "zip",
        "postal",
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def contains_pii_request(self, text: str) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Check whether the user query appears to be requesting PII.

        Returns:
            (bool, {"triggers": [...matched keywords...]})
        """
        if not text:
            return False, {"triggers": []}

        lowered = text.lower()
        triggers = [kw for kw in self._PII_TRIGGER_KEYWORDS if kw in lowered]
        return bool(triggers), {"triggers": triggers}

    def filter_response(self, text: str) -> RedactionResult:
        """
        Redact all recognised PII patterns from *text*.

        Returns a RedactionResult with the cleaned text and per-type counts.
        """
        if not text:
            return RedactionResult(
                original=text or "",
                redacted=text or "",
                was_modified=False,
            )

        redacted = text
        counts: Dict[str, int] = {}

        for label, pattern, replacement in self._PATTERNS:
            new_text, n = pattern.subn(replacement, redacted)
            if n:
                counts[label] = n
            redacted = new_text

        return RedactionResult(
            original=text,
            redacted=redacted,
            was_modified=redacted != text,
            redaction_counts=counts,
        )

    # ------------------------------------------------------------------
    # Convenience helper (backward-compat shim for old callers)
    # ------------------------------------------------------------------

    def filter_response_legacy(self, text: str) -> Tuple[str, bool]:
        """Legacy tuple interface: returns (redacted_text, was_modified)."""
        result = self.filter_response(text)
        return result.redacted, result.was_modified
