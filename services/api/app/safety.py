from __future__ import annotations

import re

BLOCKED_PATTERNS = [
    r"\bkill myself\b",
    r"\bsuicide\b",
    r"\bself[- ]?harm\b",
    r"\bmedical diagnosis\b",
    r"\bwhich stock\b",
    r"\bguarantee\b.*\bmarriage\b",
    r"\bguarantee\b.*\bmoney\b",
]


def reject_unsafe_question(question: str) -> None:
    lowered = question.lower()
    if any(re.search(pattern, lowered) for pattern in BLOCKED_PATTERNS):
        raise ValueError(
            "This question needs grounded professional support, not astrology. "
            "Ask a reflective life, relationship, or career-direction question instead."
        )


def reading_guardrail(text: str) -> str:
    text = re.sub(r"\bwill definitely\b", "may", text, flags=re.IGNORECASE)
    text = re.sub(r"\bguaranteed\b", "not guaranteed", text, flags=re.IGNORECASE)
    return text.strip()
