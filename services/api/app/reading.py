from __future__ import annotations

import json
from typing import Any

import httpx
from astro_core import ChartSnapshot, ReadingResponse, build_fallback_reading

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
            "headline": {"type": "string"},
            "summary": {"type": "string"},
            "love": {"type": "string"},
            "career": {"type": "string"},
            "money": {"type": "string"},
            "mind": {"type": "string"},
            "doActions": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3},
            "dontActions": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3},
            "luckySupports": {
                "type": "object",
                "additionalProperties": False,
                "required": ["colors", "numbers", "mantra"],
                "properties": {
                    "colors": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 3},
                    "numbers": {"type": "array", "items": {"type": "integer"}, "minItems": 1, "maxItems": 3},
                    "mantra": {"type": "string"},
                },
            },
            "astroEvidence": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 5},
            "safetyDisclaimer": {"type": "string"},
        },
    },
}


async def render_reading(chart: ChartSnapshot, intent: str = "daily", question: str | None = None) -> ReadingResponse:
    if question:
        reject_unsafe_question(question)

    fallback = build_fallback_reading(chart, intent=intent)
    if not settings.openai_api_key:
        return fallback

    prompt = _prompt(chart, intent, question)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openai_model,
                    "store": False,
                    "input": [
                        {
                            "role": "system",
                            "content": (
                                "You write bold Vedic astrology readings for Indian English users. "
                                "Use the chart facts as evidence. Do not invent chart placements. "
                                "Do not offer medical, legal, financial, crisis, or guaranteed fate claims. "
                                "Tone: sharp, memorable, truthful, never cruel."
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
                },
            )
            response.raise_for_status()
            payload = response.json()
            content = _extract_text(payload)
            parsed = json.loads(content)
            safe_payload = {
                key: reading_guardrail(value) if isinstance(value, str) else value
                for key, value in parsed.items()
            }
            return ReadingResponse.model_validate(safe_payload)
    except Exception:
        return fallback


def _prompt(chart: ChartSnapshot, intent: str, question: str | None) -> str:
    chart_json = chart.model_dump(by_alias=True, mode="json")
    return json.dumps(
        {
            "intent": intent,
            "question": question,
            "chart": chart_json,
            "style": {
                "voice": "bold Co-Star-like, but grounded in Vedic evidence",
                "readingLength": "short mobile sections",
                "mustInclude": "specific astroEvidence items derived from chart only",
            },
        },
        ensure_ascii=True,
    )


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
