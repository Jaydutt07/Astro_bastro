from __future__ import annotations

import re
import unicodedata

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
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("**", "")
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    text = text.replace("—", "-").replace("–", "-")
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", "", text)
    text = re.sub(r"\bwill definitely\b", "may", text, flags=re.IGNORECASE)
    text = re.sub(r"\bguaranteed\b", "not guaranteed", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<=[.!?])(?=[A-Z])", " ", text)
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
