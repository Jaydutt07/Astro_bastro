from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from astro_core import BirthProfile, ReadingResponse, build_chart_snapshot, build_fallback_reading
from pydantic import BaseModel, Field


class QualityScore(BaseModel):
    profile_label: str = Field(alias="profileLabel")
    total: int
    specificity: int
    evidence: int
    safety: int
    tone: int
    notes: list[str]


class QualityReport(BaseModel):
    generated_for: date = Field(alias="generatedFor")
    average: float
    scores: list[QualityScore]


@dataclass(frozen=True)
class QualityProfile:
    label: str
    profile: BirthProfile


QUALITY_PROFILES = [
    QualityProfile(
        label="Umarga exact night birth",
        profile=BirthProfile.model_validate(
            {
                "birthDate": "2002-03-07",
                "birthTime": "22:44",
                "birthTimeConfidence": "exact",
                "birthplaceText": "Umarga, Maharashtra, India",
                "latitude": 17.8367,
                "longitude": 76.6206,
                "timezone": "Asia/Kolkata",
                "language": "en-IN",
                "consent": {"privacyAccepted": True, "aiPersonalization": True, "marketingOptIn": False},
            }
        ),
    ),
    QualityProfile(
        label="Mumbai approximate morning birth",
        profile=BirthProfile.model_validate(
            {
                "birthDate": "1997-11-19",
                "birthTime": "08:10",
                "birthTimeConfidence": "approximate",
                "birthplaceText": "Mumbai, Maharashtra, India",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "timezone": "Asia/Kolkata",
                "language": "en-IN",
                "consent": {"privacyAccepted": True, "aiPersonalization": True, "marketingOptIn": False},
            }
        ),
    ),
    QualityProfile(
        label="Delhi unknown noon proxy",
        profile=BirthProfile.model_validate(
            {
                "birthDate": "1989-01-28",
                "birthTime": "12:00",
                "birthTimeConfidence": "unknown",
                "birthplaceText": "Delhi, India",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "timezone": "Asia/Kolkata",
                "language": "en-IN",
                "consent": {"privacyAccepted": True, "aiPersonalization": True, "marketingOptIn": False},
            }
        ),
    ),
]


def evaluate_quality(for_date: date | None = None) -> QualityReport:
    target_date = for_date or date.today()
    scores: list[QualityScore] = []
    for item in QUALITY_PROFILES:
        chart = build_chart_snapshot(item.profile, for_date=target_date)
        reading = build_fallback_reading(chart)
        scores.append(score_reading(item.label, reading))
    average = round(sum(score.total for score in scores) / len(scores), 2)
    return QualityReport(generatedFor=target_date, average=average, scores=scores)


def score_reading(profile_label: str, reading: ReadingResponse) -> QualityScore:
    notes: list[str] = []
    evidence_blob = " ".join(reading.astro_evidence).lower()
    all_text = " ".join(
        [
            reading.headline,
            reading.summary,
            reading.love,
            reading.career,
            reading.money,
            reading.mind,
            evidence_blob,
        ]
    ).lower()

    specificity = _score(
        [
            any(token in all_text for token in ["nakshatra", "dasha", "ascendant", "house"]),
            len(reading.do_actions) == 3,
            len(reading.dont_actions) == 3,
        ],
        "specificity",
        notes,
    )
    evidence = _score(
        [
            len(reading.astro_evidence) >= 4,
            "engine:" in evidence_blob,
            "numerology" in evidence_blob,
        ],
        "evidence",
        notes,
    )
    safety = _score(
        [
            "not medical" in reading.safety_disclaimer.lower(),
            "guarantee" not in all_text,
            "will definitely" not in all_text,
        ],
        "safety",
        notes,
    )
    tone = _score(
        [
            12 <= len(reading.headline.split()) <= 18,
            any(word in all_text for word in ["truth", "clear", "evidence", "precise", "receipts"]),
            "you are doomed" not in all_text,
        ],
        "tone",
        notes,
    )

    return QualityScore(
        profileLabel=profile_label,
        specificity=specificity,
        evidence=evidence,
        safety=safety,
        tone=tone,
        total=specificity + evidence + safety + tone,
        notes=notes or ["passes MVP quality gates"],
    )


def _score(checks: list[bool], label: str, notes: list[str]) -> int:
    value = sum(1 for check in checks if check)
    if value < len(checks):
        notes.append(f"{label}: {value}/{len(checks)}")
    return value
