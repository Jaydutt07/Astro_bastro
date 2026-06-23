from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Consent(BaseModel):
    privacy_accepted: bool = Field(default=True, alias="privacyAccepted")
    ai_personalization: bool = Field(default=True, alias="aiPersonalization")
    marketing_opt_in: bool = Field(default=False, alias="marketingOptIn")


class BirthProfile(BaseModel):
    full_name: str = Field(default="Astro Solves Seeker", alias="fullName", max_length=120)
    birth_date: date = Field(alias="birthDate")
    birth_time: str = Field(alias="birthTime", examples=["22:44"])
    birth_time_confidence: str = Field(default="exact", alias="birthTimeConfidence")
    birthplace_text: str = Field(alias="birthplaceText")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str = Field(default="Asia/Kolkata")
    language: str = Field(default="en-IN")
    consent: Consent = Field(default_factory=Consent)


class ZodiacPoint(BaseModel):
    sign: str
    degree: float
    absolute_degree: float = Field(alias="absoluteDegree")
    nakshatra: str
    pada: int


class PlanetPosition(BaseModel):
    planet: str
    point: ZodiacPoint
    house: int


class DashaSnapshot(BaseModel):
    mahadasha: str
    antardasha: str
    balance_years_at_birth: float = Field(alias="balanceYearsAtBirth")


class NumerologySnapshot(BaseModel):
    birth_number: int = Field(alias="birthNumber")
    life_path_number: int = Field(alias="lifePathNumber")
    personal_year_number: int = Field(alias="personalYearNumber")
    personal_day_number: int = Field(alias="personalDayNumber")


class ChartSnapshot(BaseModel):
    profile: BirthProfile
    generated_for: date = Field(alias="generatedFor")
    ayanamsa: str
    calculation_engine: str = Field(alias="calculationEngine")
    ascendant: ZodiacPoint
    moon: ZodiacPoint
    sun: ZodiacPoint
    planets: list[PlanetPosition]
    dasha: DashaSnapshot
    numerology: NumerologySnapshot
    transits: list[PlanetPosition]


class LuckySupports(BaseModel):
    colors: list[str]
    numbers: list[int]
    mantra: str


class EntitlementStatus(BaseModel):
    access: str = "free"
    free_limit: int = Field(alias="freeLimit")
    free_used: int = Field(alias="freeUsed")
    free_remaining: int = Field(alias="freeRemaining")
    message: str


class HarmonyPerson(BaseModel):
    name: str
    sign: str
    birth_number: int | None = Field(default=None, alias="birthNumber")
    life_path_number: int | None = Field(default=None, alias="lifePathNumber")
    name_number: int = Field(alias="nameNumber")


class HarmonyResponse(BaseModel):
    title: str
    compatibility_score: int = Field(alias="compatibilityScore")
    user: HarmonyPerson
    partner: HarmonyPerson
    best_relationship_matches: list[str] = Field(alias="bestRelationshipMatches")
    best_marriage_matches: list[str] = Field(alias="bestMarriageMatches")
    challenging_matches: list[str] = Field(alias="challengingMatches")
    relationship_lens: str = Field(alias="relationshipLens")
    marriage_lens: str = Field(alias="marriageLens")
    numerology_lens: str = Field(alias="numerologyLens")
    peace_practice: str = Field(alias="peacePractice")
    watchouts: list[str]
    remedies: list[str]
    astro_evidence: list[str] = Field(alias="astroEvidence")
    safety_disclaimer: str = Field(alias="safetyDisclaimer")


class ReadingResponse(BaseModel):
    headline: str
    summary: str
    love: str
    career: str
    money: str
    mind: str
    do_actions: list[str] = Field(alias="doActions")
    dont_actions: list[str] = Field(alias="dontActions")
    lucky_supports: LuckySupports = Field(alias="luckySupports")
    astro_evidence: list[str] = Field(alias="astroEvidence")
    safety_disclaimer: str = Field(alias="safetyDisclaimer")
    entitlement: EntitlementStatus | None = None


class SolutionStep(BaseModel):
    title: str
    practice: str
    duration: str
    why: str
    is_free: bool = Field(alias="isFree")


class ProblemInsightResponse(BaseModel):
    problem_title: str = Field(alias="problemTitle")
    reassurance: str
    astro_pattern: str = Field(alias="astroPattern")
    timeline: str
    watchouts: list[str]
    free_solution: SolutionStep = Field(alias="freeSolution")
    premium_solutions: list[SolutionStep] = Field(alias="premiumSolutions")
    astro_evidence: list[str] = Field(alias="astroEvidence")
    safety_disclaimer: str = Field(alias="safetyDisclaimer")
    entitlement: EntitlementStatus | None = None


ReportKind = Literal["love", "career", "yearly"]
ReadingPeriod = Literal["daily", "weekly", "monthly", "yearly"]
