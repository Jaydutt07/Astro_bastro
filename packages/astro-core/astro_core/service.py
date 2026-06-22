from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from .constants import PLANET_ORDER
from .dasha import vimshottari_dasha
from .ephemeris import active_ephemeris_engine, ascendant_sidereal, lahiri_ayanamsa, sidereal_longitude, sign_parts
from .models import (
    BirthProfile,
    ChartSnapshot,
    DashaSnapshot,
    LuckySupports,
    NumerologySnapshot,
    PlanetPosition,
    ReadingResponse,
    ZodiacPoint,
)
from .numerology import birth_number, life_path_number, personal_day_number, personal_year_number
from .timeutils import julian_day, parse_birth_datetime


def point_model(absolute_degree: float) -> ZodiacPoint:
    parts = sign_parts(absolute_degree)
    return ZodiacPoint(
        sign=parts.sign,
        degree=parts.degree,
        absoluteDegree=parts.absolute_degree,
        nakshatra=parts.nakshatra,
        pada=parts.pada,
    )


def house_for(planet_degree: float, ascendant_degree: float) -> int:
    asc_sign = int((ascendant_degree % 360) // 30)
    planet_sign = int((planet_degree % 360) // 30)
    return ((planet_sign - asc_sign) % 12) + 1


def build_chart_snapshot(profile: BirthProfile, for_date: date | None = None) -> ChartSnapshot:
    target_date = for_date or datetime.now(ZoneInfo(profile.timezone)).date()
    birth_moment = parse_birth_datetime(profile.birth_date, profile.birth_time, profile.timezone)
    birth_jd = julian_day(birth_moment)
    noon_target = datetime.combine(target_date, datetime.min.time(), tzinfo=ZoneInfo(profile.timezone)).replace(hour=12)
    transit_jd = julian_day(noon_target)

    asc_degree = ascendant_sidereal(birth_jd, profile.latitude, profile.longitude)
    planet_degrees = {planet: sidereal_longitude(planet, birth_jd) for planet in PLANET_ORDER}
    transit_degrees = {planet: sidereal_longitude(planet, transit_jd) for planet in PLANET_ORDER}
    maha, antar, balance = vimshottari_dasha(planet_degrees["Moon"], profile.birth_date, target_date)

    planets = [
        PlanetPosition(
            planet=planet,
            point=point_model(degree),
            house=house_for(degree, asc_degree),
        )
        for planet, degree in planet_degrees.items()
    ]
    transits = [
        PlanetPosition(
            planet=planet,
            point=point_model(degree),
            house=house_for(degree, asc_degree),
        )
        for planet, degree in transit_degrees.items()
    ]

    return ChartSnapshot(
        profile=profile,
        generatedFor=target_date,
        ayanamsa=f"Lahiri approx {lahiri_ayanamsa(birth_jd):.4f}",
        calculationEngine=active_ephemeris_engine(),
        ascendant=point_model(asc_degree),
        moon=point_model(planet_degrees["Moon"]),
        sun=point_model(planet_degrees["Sun"]),
        planets=planets,
        dasha=DashaSnapshot(mahadasha=maha, antardasha=antar, balanceYearsAtBirth=balance),
        numerology=NumerologySnapshot(
            birthNumber=birth_number(profile.birth_date),
            lifePathNumber=life_path_number(profile.birth_date),
            personalYearNumber=personal_year_number(profile.birth_date, target_date),
            personalDayNumber=personal_day_number(profile.birth_date, target_date),
        ),
        transits=transits,
    )


def build_fallback_reading(chart: ChartSnapshot, intent: str = "daily") -> ReadingResponse:
    moon_transit = next((item for item in chart.transits if item.planet == "Moon"), chart.transits[0])
    jupiter_transit = next((item for item in chart.transits if item.planet == "Jupiter"), chart.transits[0])
    saturn_transit = next((item for item in chart.transits if item.planet == "Saturn"), chart.transits[0])
    personal_day = chart.numerology.personal_day_number
    headline = _headline(chart, moon_transit.house, intent)
    summary = (
        f"Your {chart.moon.nakshatra} Moon wants truth, but today's Moon in "
        f"{moon_transit.point.nakshatra} asks for evidence. The mood is not anti-you; "
        "it is anti-vague. Pick the one thing you keep circling and make it measurable."
    )
    return ReadingResponse(
        headline=headline,
        summary=summary,
        love=(
            "Love works better when you stop auditioning for certainty. Ask for the real signal, "
            "then believe the answer people show you."
        ),
        career=(
            f"Career gets a serious push from Jupiter moving through your {jupiter_transit.house}th house. "
            "Use it for one visible, competent move: send the proposal, update the profile, or ask the senior person."
        ),
        money=(
            "Money wants boring discipline today. No panic spending, no heroic risk. Check the numbers and let the drama leave first."
        ),
        mind=(
            f"Personal day {personal_day} rewards expression, but Saturn in the {saturn_transit.house}th house asks for structure. "
            "Write it down before you turn it into a personality crisis."
        ),
        doActions=["finish one pending task", "send one honest message", "clean up a money detail"],
        dontActions=["make a permanent decision from a temporary mood", "lend money casually", "confuse intensity with proof"],
        luckySupports=LuckySupports(
            colors=["white", "forest green", "coral"],
            numbers=[personal_day, chart.numerology.life_path_number],
            mantra="I trust what is clear, not what is loud.",
        ),
        astroEvidence=[
            f"Engine: {chart.calculation_engine}; birth time confidence: {chart.profile.birth_time_confidence}.",
            f"Ascendant: {chart.ascendant.sign} {chart.ascendant.degree:.1f} deg, {chart.ascendant.nakshatra} pada {chart.ascendant.pada}.",
            f"Natal Moon: {chart.moon.sign} / {chart.moon.nakshatra}; current dasha: {chart.dasha.mahadasha}-{chart.dasha.antardasha}.",
            f"Transit Moon: {moon_transit.point.sign} in whole-sign house {moon_transit.house}; Jupiter in house {jupiter_transit.house}.",
            f"Numerology: birth {chart.numerology.birth_number}, life path {chart.numerology.life_path_number}, personal day {personal_day}.",
        ],
        safetyDisclaimer="Astrology is reflective guidance, not medical, legal, financial, or crisis advice.",
    )


def _headline(chart: ChartSnapshot, moon_house: int, intent: str) -> str:
    if intent == "love":
        return "Your heart is not confused. It is waiting for behavior to catch up."
    if intent == "career":
        return "Be seen for the work, not the over-explanation."
    if intent == "yearly":
        return "This year rewards the version of you that keeps receipts."
    if moon_house in {10, 11}:
        return "The room is watching. Good. Give it something precise."
    if moon_house in {1, 5, 9}:
        return "Your instinct is loud today. Make it useful, not theatrical."
    return "The chart is not being subtle: clean up the thing you keep postponing."
