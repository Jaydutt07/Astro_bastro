from __future__ import annotations

import json
import re
from typing import Any

import httpx
from astro_core import ChartSnapshot, ProblemInsightResponse, ReadingResponse, build_fallback_problem_insight, build_fallback_reading

from .config import settings
from .safety import reading_guardrail, reject_unsafe_question


READING_SCHEMA: dict[str, Any] = {
    "name": "reading_response",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "headline",
            "summary",
            "love",
            "career",
            "money",
            "mind",
            "doActions",
            "dontActions",
            "luckySupports",
            "astroEvidence",
            "safetyDisclaimer",
        ],
        "properties": {
            "headline": {"type": "string", "maxLength": 90},
            "summary": {"type": "string", "maxLength": 260},
            "love": {"type": "string", "maxLength": 170},
            "career": {"type": "string", "maxLength": 170},
            "money": {"type": "string", "maxLength": 170},
            "mind": {"type": "string", "maxLength": 170},
            "doActions": {"type": "array", "items": {"type": "string", "maxLength": 42}, "minItems": 3, "maxItems": 3},
            "dontActions": {"type": "array", "items": {"type": "string", "maxLength": 48}, "minItems": 3, "maxItems": 3},
            "luckySupports": {
                "type": "object",
                "additionalProperties": False,
                "required": ["colors", "numbers", "mantra"],
                "properties": {
                    "colors": {"type": "array", "items": {"type": "string", "maxLength": 24}, "minItems": 2, "maxItems": 3},
                    "numbers": {"type": "array", "items": {"type": "integer"}, "minItems": 1, "maxItems": 3},
                    "mantra": {"type": "string", "maxLength": 80},
                },
            },
            "astroEvidence": {"type": "array", "items": {"type": "string", "maxLength": 130}, "minItems": 3, "maxItems": 4},
            "safetyDisclaimer": {"type": "string", "maxLength": 180},
        },
    },
}


PROBLEM_SCHEMA: dict[str, Any] = {
    "name": "problem_insight_response",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "problemTitle",
            "reassurance",
            "astroPattern",
            "timeline",
            "watchouts",
            "freeSolution",
            "premiumSolutions",
            "astroEvidence",
            "safetyDisclaimer",
        ],
        "properties": {
            "problemTitle": {"type": "string", "maxLength": 110},
            "reassurance": {"type": "string", "maxLength": 280},
            "astroPattern": {"type": "string", "maxLength": 900},
            "timeline": {"type": "string", "maxLength": 460},
            "watchouts": {"type": "array", "items": {"type": "string", "maxLength": 150}, "minItems": 3, "maxItems": 3},
            "freeSolution": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "practice", "duration", "why", "isFree"],
                "properties": {
                    "title": {"type": "string", "maxLength": 80},
                    "practice": {"type": "string", "maxLength": 380},
                    "duration": {"type": "string", "maxLength": 45},
                    "why": {"type": "string", "maxLength": 240},
                    "isFree": {"type": "boolean"},
                },
            },
            "premiumSolutions": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["title", "practice", "duration", "why", "isFree"],
                    "properties": {
                        "title": {"type": "string", "maxLength": 80},
                        "practice": {"type": "string", "maxLength": 320},
                        "duration": {"type": "string", "maxLength": 45},
                        "why": {"type": "string", "maxLength": 220},
                        "isFree": {"type": "boolean"},
                    },
                },
            },
            "astroEvidence": {"type": "array", "items": {"type": "string", "maxLength": 210}, "minItems": 3, "maxItems": 4},
            "safetyDisclaimer": {"type": "string", "maxLength": 180},
        },
    },
}


DRAFT_ARTIFACT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bfinal\s+json\b",
        r"\bjson\s+cannot\b",
        r"\brephrase\b",
        r"\bwait\b.*\bjson\b",
        r"\bromatically\b",
        r"\bmarks[- ]wise\b",
        r"\bscale\s+pe\b",
        r"\bzaroor\b",
        r"\bbanata\b",
        r"\bneed\s+fix\b",
    ]
]

INCOMPLETE_ENDING_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"[-,;:]$",
        r"\b(and|or|with|through|because|for|from|into|while|this|that|a|the)$",
        r"\bnon-not guaranteed\b",
    ]
]


async def render_reading(
    chart: ChartSnapshot,
    intent: str = "daily",
    question: str | None = None,
    memory_context: dict[str, Any] | None = None,
) -> ReadingResponse:
    if question:
        reject_unsafe_question(question)

    fallback = build_fallback_reading(chart, intent=intent)
    if not settings.openai_api_key:
        return fallback

    prompt = _prompt(chart, intent, question, memory_context)
    request_json: dict[str, Any] = {
        "model": settings.openai_model,
        "store": False,
        "max_output_tokens": settings.openai_reading_max_output_tokens,
        "input": [
            {
                "role": "system",
                "content": (
                    "You write concise Vedic astrology readings for Indian English users. "
                    "Use only the supplied chart facts and user memory as evidence. Do not invent chart placements. "
                    "Return final JSON only. No draft notes, self-corrections, markdown, Hinglish, or internal analysis. "
                    "Keep every Do and Avoid as one short imperative phrase. "
                    "Do not offer medical, legal, financial, crisis, or guaranteed fate claims. "
                    "Tone: elegant, simple, reassuring, spiritually grounded, never cruel."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": READING_SCHEMA["name"],
                "strict": True,
                "schema": READING_SCHEMA["schema"],
            }
        },
    }
    _apply_model_controls(request_json, problem=False)
    for _ in range(settings.openai_max_attempts):
        try:
            parsed = await _structured_payload(request_json)
            return ReadingResponse.model_validate(parsed)
        except Exception:
            continue
    return fallback


async def render_problem_insight(
    chart: ChartSnapshot,
    category: str,
    problem_text: str,
    memory_context: dict[str, Any] | None = None,
) -> ProblemInsightResponse:
    reject_unsafe_question(problem_text)
    fallback = build_fallback_problem_insight(chart, problem_text=problem_text, category=category)
    if not settings.openai_api_key:
        return fallback

    prompt = _problem_prompt(chart, category, problem_text, memory_context)
    request_json: dict[str, Any] = {
        "model": settings.openai_model,
        "store": False,
        "max_output_tokens": settings.openai_problem_max_output_tokens,
        "input": [
            {
                "role": "system",
                "content": (
                    "You write empathetic Vedic astrology problem insights for Indian English users. "
                    "Use only supplied chart facts and memory as evidence. Return final JSON only. "
                    "No draft notes, self-corrections, markdown, Hinglish, or internal analysis. "
                    "Frame root causes as astrological lenses, not absolute truth. "
                    "Explain heavy astrology terms in plain words. "
                    "Every sentence and list item must finish cleanly; never stop mid-phrase to satisfy length. "
                    "Provide one free remedy and three premium remedy options. "
                    "Do not claim guaranteed outcomes, cures, wealth, marriage, or fixed fate. "
                    "Do not replace medical, legal, financial, or crisis support."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": PROBLEM_SCHEMA["name"],
                "strict": True,
                "schema": PROBLEM_SCHEMA["schema"],
            }
        },
    }
    _apply_model_controls(request_json, problem=True)
    for _ in range(settings.openai_max_attempts):
        try:
            parsed = await _structured_payload(request_json)
            return ProblemInsightResponse.model_validate(parsed)
        except Exception:
            continue
    return fallback


def _prompt(
    chart: ChartSnapshot,
    intent: str,
    question: str | None,
    memory_context: dict[str, Any] | None,
) -> str:
    return json.dumps(
        {
            "intent": intent,
            "question": question,
            "chart": _compact_chart(chart),
            "userMemory": _compact_memory(memory_context),
            "style": {
                "voice": "classy, simple, elegant, royal, grounded in Vedic evidence",
                "readingLength": "short mobile sections",
                "mustInclude": "specific astroEvidence items derived from chart and memory only",
                "avoid": "heavy jargon, Hinglish, draft notes, self-corrections, long Do/Avoid lines",
            },
        },
        ensure_ascii=True,
    )


def _httpx_verify() -> bool | str:
    return settings.openai_ca_bundle or settings.openai_verify_ssl


async def _structured_payload(request_json: dict[str, Any]) -> Any:
    payload = await _responses_payload(request_json)
    content = _extract_text(payload)
    parsed = _normalize_payload(_guardrail_payload(json.loads(content)))
    _reject_draft_artifacts(parsed)
    _reject_incomplete_strings(parsed)
    return parsed


async def _responses_payload(request_json: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=settings.openai_timeout_seconds, verify=_httpx_verify()) as client:
        response = await client.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=request_json,
        )
        response.raise_for_status()
        return response.json()


def _problem_prompt(
    chart: ChartSnapshot,
    category: str,
    problem_text: str,
    memory_context: dict[str, Any] | None,
) -> str:
    return json.dumps(
        {
            "category": category,
            "problem": problem_text,
            "chart": _compact_chart(chart),
            "userMemory": _compact_memory(memory_context),
            "style": {
                "voice": "private, calming, culturally Indian, elegant, royal, specific, never fear-based",
                "mustInclude": [
                    "one concise reassurance",
                    "Saade Saati or Saturn context when relevant",
                    "timeline language without guaranteed predictions",
                    "one free remedy",
                    "three premium remedies",
                ],
                "avoid": [
                    "heavy unexplained jargon",
                    "Hinglish",
                    "draft notes",
                    "self-corrections",
                    "guaranteed claims",
                ],
            },
        },
        ensure_ascii=True,
    )


def _apply_model_controls(request_json: dict[str, Any], *, problem: bool) -> None:
    if settings.openai_model.startswith("gpt-5"):
        request_json["reasoning"] = {"effort": settings.openai_reasoning_effort}
        request_json.setdefault("text", {})["verbosity"] = settings.openai_verbosity
    if problem:
        request_json["max_output_tokens"] = settings.openai_problem_max_output_tokens
    else:
        request_json["max_output_tokens"] = settings.openai_reading_max_output_tokens


def _compact_chart(chart: ChartSnapshot) -> dict[str, Any]:
    important_transits = {"Moon", "Saturn", "Jupiter", "Rahu", "Ketu"}
    return {
        "profile": {
            "fullName": chart.profile.full_name,
            "birthDate": chart.profile.birth_date.isoformat(),
            "birthTime": chart.profile.birth_time,
            "birthTimeConfidence": chart.profile.birth_time_confidence,
            "birthplaceText": chart.profile.birthplace_text,
            "timezone": chart.profile.timezone,
        },
        "generatedFor": chart.generated_for.isoformat(),
        "ascendant": _compact_point(chart.ascendant),
        "moon": _compact_point(chart.moon),
        "sun": _compact_point(chart.sun),
        "dasha": chart.dasha.model_dump(by_alias=True, mode="json"),
        "numerology": chart.numerology.model_dump(by_alias=True, mode="json"),
        "natalPlanets": [
            {"planet": item.planet, "house": item.house, "point": _compact_point(item.point)}
            for item in chart.planets
        ],
        "transits": [
            {"planet": item.planet, "house": item.house, "point": _compact_point(item.point)}
            for item in chart.transits
            if item.planet in important_transits
        ],
    }


def _compact_point(point: Any) -> dict[str, Any]:
    return {
        "sign": point.sign,
        "degree": round(float(point.degree), 1),
        "nakshatra": point.nakshatra,
        "pada": point.pada,
    }


def _compact_memory(memory_context: dict[str, Any] | None) -> dict[str, Any] | None:
    if not memory_context:
        return None
    recent = []
    for item in list(memory_context.get("recentProblems", []))[-3:]:
        details = str(item.get("problemDetails", ""))
        recent.append(
            {
                "category": item.get("category", ""),
                "problemTitle": item.get("problemTitle", ""),
                "problemDetails": details[:240],
            }
        )
    return {
        "problemCount": int(memory_context.get("problemCount", 0)),
        "recentProblems": recent,
        "categoryCounts": dict(memory_context.get("categoryCounts", {})),
        "solutionHistory": list(memory_context.get("solutionHistory", []))[-3:],
    }


def _guardrail_payload(value: Any) -> Any:
    if isinstance(value, str):
        return reading_guardrail(value)
    if isinstance(value, list):
        return [_guardrail_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _guardrail_payload(item) for key, item in value.items()}
    return value


def _reject_draft_artifacts(value: Any) -> None:
    if isinstance(value, str):
        if any(pattern.search(value) for pattern in DRAFT_ARTIFACT_PATTERNS):
            raise ValueError("Generated text contained draft or mixed-language artifacts.")
        return
    if isinstance(value, list):
        for item in value:
            _reject_draft_artifacts(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_draft_artifacts(item)


def _reject_incomplete_strings(value: Any) -> None:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and any(pattern.search(stripped) for pattern in INCOMPLETE_ENDING_PATTERNS):
            raise ValueError("Generated text ended mid-phrase.")
        return
    if isinstance(value, list):
        for item in value:
            _reject_incomplete_strings(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_incomplete_strings(item)


def _normalize_payload(value: Any, parent_key: str | None = None) -> Any:
    if isinstance(value, str):
        cleaned = re.sub(r"\bnon-not guaranteed\b", "not guaranteed", value, flags=re.IGNORECASE)
        if parent_key in {"doActions", "dontActions"}:
            cleaned = re.sub(r"^(do|avoid|don't|dont)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"^(do|avoid|don't|dont)\s+", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()
    if isinstance(value, list):
        return [_normalize_payload(item, parent_key=parent_key) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_payload(item, parent_key=key) for key, item in value.items()}
    return value


def _extract_text(payload: dict[str, Any]) -> str:
    if "output_text" in payload:
        return str(payload["output_text"])
    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                chunks.append(str(content.get("text", "")))
    if chunks:
        return "".join(chunks)
    raise ValueError("No text output returned by OpenAI")
