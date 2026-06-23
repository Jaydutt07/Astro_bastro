from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from .constants import PLANET_ORDER, SIGNS
from .dasha import vimshottari_dasha
from .ephemeris import active_ephemeris_engine, ascendant_sidereal, lahiri_ayanamsa, sidereal_longitude, sign_parts
from .models import (
    BirthProfile,
    ChartSnapshot,
    DashaSnapshot,
    HarmonyPerson,
    HarmonyResponse,
    LuckySupports,
    NumerologySnapshot,
    PlanetPosition,
    ProblemInsightResponse,
    ReadingResponse,
    SolutionStep,
    ZodiacPoint,
)
from .numerology import birth_number, life_path_number, name_number, personal_day_number, personal_year_number
from .timeutils import julian_day, parse_birth_datetime


SIGN_ELEMENTS = {
    "Aries": "fire",
    "Leo": "fire",
    "Sagittarius": "fire",
    "Taurus": "earth",
    "Virgo": "earth",
    "Capricorn": "earth",
    "Gemini": "air",
    "Libra": "air",
    "Aquarius": "air",
    "Cancer": "water",
    "Scorpio": "water",
    "Pisces": "water",
}
COMPLEMENTARY_ELEMENTS = {
    "fire": {"air", "fire"},
    "air": {"fire", "air"},
    "earth": {"water", "earth"},
    "water": {"earth", "water"},
}
NUMBER_COMPATIBILITY = {
    1: {1, 3, 5, 9},
    2: {2, 4, 6},
    3: {1, 3, 5, 6},
    4: {2, 4, 8},
    5: {1, 3, 5, 7},
    6: {2, 3, 6, 9},
    7: {5, 7, 9},
    8: {2, 4, 8},
    9: {1, 6, 7, 9},
}


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
    period = intent if intent in {"daily", "weekly", "monthly", "yearly"} else "daily"
    headline = _headline(chart, moon_transit.house, intent)
    period_focus = {
        "daily": "today's Moon",
        "weekly": "this week's Moon rhythm",
        "monthly": "this month's transit pressure",
        "yearly": "this year's dasha and Saturn lessons",
    }[period]
    summary = (
        f"{chart.profile.full_name}, your {chart.moon.nakshatra} Moon wants truth, but {period_focus} in "
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
            f"Birth place: {chart.profile.birthplace_text}; time confidence: {chart.profile.birth_time_confidence}.",
            f"Moon: {chart.moon.sign}/{chart.moon.nakshatra}; dasha: {chart.dasha.mahadasha}-{chart.dasha.antardasha}.",
            f"Transit Moon: {moon_transit.point.sign} in house {moon_transit.house}; Saturn in house {saturn_transit.house}.",
            f"Numbers: birth {chart.numerology.birth_number}, life path {chart.numerology.life_path_number}, personal day {personal_day}.",
        ],
        safetyDisclaimer=DEFAULT_DISCLAIMER,
    )


def build_fallback_problem_insight(chart: ChartSnapshot, problem_text: str, category: str = "shani") -> ProblemInsightResponse:
    saturn_transit = next((item for item in chart.transits if item.planet == "Saturn"), chart.transits[0])
    moon_transit = next((item for item in chart.transits if item.planet == "Moon"), chart.transits[0])
    sade_sati = _sade_sati_status(chart, saturn_transit)
    category_label = category.replace("-", " ").title()
    compressed_problem = " ".join(problem_text.strip().split())
    if len(compressed_problem) > 110:
        compressed_problem = f"{compressed_problem[:107].rstrip()}..."

    if sade_sati:
        astro_pattern = (
            f"Saturn is moving through {saturn_transit.point.sign}, which is a classic Saade Saati zone from your "
            f"{chart.moon.sign} Moon. Treat this as a discipline-and-delay period: pressure rises where life needs structure."
        )
        timeline = (
            "Saade Saati is traditionally treated as a long Saturn cycle, so expect themes to unfold in phases rather than vanish overnight. "
            "Use this month for repair, consistency, and reducing avoidable karmic load."
        )
    else:
        astro_pattern = (
            f"Saturn is not in a classic Saade Saati position from your {chart.moon.sign} Moon, but it is activating your "
            f"{saturn_transit.house}th house. The pressure is real, yet it is more about that house's lessons than doom."
        )
        timeline = (
            "The next useful window is the current monthly transit cycle. Watch whether the issue softens when routines, boundaries, "
            "and delayed decisions become clearer."
        )

    return ProblemInsightResponse(
        problemTitle=f"{category_label} pattern: {compressed_problem or 'the issue you are carrying'}",
        reassurance=(
            f"{chart.profile.full_name}, the chart does not describe you as broken. It shows a pressure pattern that can be worked with "
            "through steadiness, honest choices, and spiritual discipline."
        ),
        astroPattern=astro_pattern,
        timeline=timeline,
        watchouts=[
            "turning a temporary Saturn delay into a permanent self-belief",
            "mixing fear-based decisions with money, commitment, or family pressure",
            "seeking too many opinions instead of following one clean practice for a full cycle",
        ],
        freeSolution=SolutionStep(
            title="Free remedy: Hanuman Chalisa listening practice",
            practice=(
                "Listen to or recite Hanuman Chalisa once with full attention, then write one practical action you will complete today. "
                "Keep the ritual simple and repeatable."
            ),
            duration="1 day starter practice",
            why="Hanuman devotion is commonly used for courage, Shani pressure, fear reduction, and disciplined action.",
            isFree=True,
        ),
        premiumSolutions=[
            SolutionStep(
                title="7-day Shani discipline plan",
                practice="Daily Saturn-focused reflection, Saturday seva prompt, boundary audit, and evening audio practice.",
                duration="7 days",
                why="Saturn problems respond best to repetition, humility, service, and cleaned-up commitments.",
                isFree=False,
            ),
            SolutionStep(
                title="21-day courage and consistency audio pack",
                practice="Guided Hanuman Chalisa, breath reset, and small-action tracker for fear, delay, and overthinking.",
                duration="21 days",
                why="A longer cycle helps convert emotional reassurance into visible behavior change.",
                isFree=False,
            ),
            SolutionStep(
                title="Premium problem report",
                practice="A deeper reading across dasha, Saturn transit, Moon nakshatra, and practical next steps.",
                duration="one detailed report",
                why="Users with complex problems need a fuller map than a single daily remedy can provide.",
                isFree=False,
            ),
        ],
        astroEvidence=[
            f"Natal Moon: {chart.moon.sign} / {chart.moon.nakshatra}; Saturn transit: {saturn_transit.point.sign} in house {saturn_transit.house}.",
            f"Current dasha: {chart.dasha.mahadasha}-{chart.dasha.antardasha}; Moon transit today: {moon_transit.point.nakshatra}.",
            f"Ascendant: {chart.ascendant.sign}; life path number: {chart.numerology.life_path_number}; personal day: {chart.numerology.personal_day_number}.",
        ],
        safetyDisclaimer=DEFAULT_DISCLAIMER,
    )


def build_harmony_insight(
    chart: ChartSnapshot,
    partner_name: str,
    partner_birth_date: date | None = None,
    relationship_focus: str = "relationship",
) -> HarmonyResponse:
    user_name_number = name_number(chart.profile.full_name)
    partner_name_number = name_number(partner_name)
    partner_sign = _date_sign(partner_birth_date) if partner_birth_date else "Birth date needed"
    partner_birth_number = birth_number(partner_birth_date) if partner_birth_date else None
    partner_life_path = life_path_number(partner_birth_date) if partner_birth_date else None
    score = _compatibility_score(chart.moon.sign, partner_sign, chart.numerology.life_path_number, partner_life_path, user_name_number, partner_name_number)
    best_relationship = _best_sign_matches(chart.moon.sign, count=4)
    best_marriage = _best_sign_matches(chart.sun.sign, count=4)
    challenging = _challenging_signs(chart.moon.sign)
    focus_label = "marriage" if relationship_focus == "marriage" else "relationship peace" if relationship_focus == "peace" else "long-term stability"

    if partner_birth_date:
        relationship_lens = (
            f"Your Moon sign is {chart.moon.sign}, while {partner_name}'s birth-date sign is {partner_sign}. "
            f"This gives the bond a {SIGN_ELEMENTS.get(chart.moon.sign, 'personal')} and {SIGN_ELEMENTS.get(partner_sign, 'personal')} rhythm: "
            f"{_sign_pair_guidance(chart.moon.sign, partner_sign)}"
        )
    else:
        relationship_lens = (
            f"Your Moon sign is {chart.moon.sign}. Add your partner's birth date later for a sharper sign match; for now, "
            "the name-number layer can still show how to keep the bond calm."
        )

    marriage_lens = (
        f"For {focus_label}, your {chart.sun.sign} Sun and {chart.ascendant.sign} ascendant need respect, consistency, and clear roles. "
        "A strong match should not only create attraction; it should reduce confusion during family, money, and timing decisions."
    )
    numerology_lens = _numerology_lens(chart, user_name_number, partner_name, partner_birth_number, partner_life_path, partner_name_number)

    return HarmonyResponse(
        title=f"Harmony map for {chart.profile.full_name} and {partner_name}",
        compatibilityScore=score,
        user=HarmonyPerson(
            name=chart.profile.full_name,
            sign=chart.moon.sign,
            birthNumber=chart.numerology.birth_number,
            lifePathNumber=chart.numerology.life_path_number,
            nameNumber=user_name_number,
        ),
        partner=HarmonyPerson(
            name=partner_name,
            sign=partner_sign,
            birthNumber=partner_birth_number,
            lifePathNumber=partner_life_path,
            nameNumber=partner_name_number,
        ),
        bestRelationshipMatches=best_relationship,
        bestMarriageMatches=best_marriage,
        challengingMatches=challenging,
        relationshipLens=relationship_lens,
        marriageLens=marriage_lens,
        numerologyLens=numerology_lens,
        peacePractice=(
            "For the next 7 days, do one 12-minute calm conversation after sunset: one person speaks, the other repeats back the meaning, "
            "then both agree on one small action. End with 3 minutes of silent breathing or a short prayer."
        ),
        watchouts=[
            "Do not use compatibility as a verdict; use it to understand timing, temperament, and repair needs.",
            "Avoid discussing family, money, or commitment when either person is already emotionally flooded.",
            "If the same conflict repeats, track the pattern for one week before making a major decision.",
        ],
        remedies=[
            "Friday: offer a simple gratitude prayer for harmony and speak one appreciation clearly.",
            "Monday: keep speech gentle, reduce blame, and drink water before difficult conversations.",
            "For Shani pressure: do one service act on Saturday without announcing it.",
        ],
        astroEvidence=[
            f"User Moon sign: {chart.moon.sign}; Sun sign: {chart.sun.sign}; ascendant: {chart.ascendant.sign}.",
            f"User numbers: birth {chart.numerology.birth_number}, life path {chart.numerology.life_path_number}, name {user_name_number}.",
            f"Partner signals: sign {partner_sign}, birth {partner_birth_number or 'pending'}, life path {partner_life_path or 'pending'}, name {partner_name_number}.",
            f"Current dasha: {chart.dasha.mahadasha}-{chart.dasha.antardasha}; use compatibility as reflective guidance, not fixed fate.",
        ],
        safetyDisclaimer=DEFAULT_DISCLAIMER,
    )


def _headline(chart: ChartSnapshot, moon_house: int, intent: str) -> str:
    if intent == "weekly":
        return "This week asks for one clean promise and seven honest follow-throughs."
    if intent == "monthly":
        return "The month is testing your systems, not your worth."
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


def _sade_sati_status(chart: ChartSnapshot, saturn_transit: PlanetPosition) -> bool:
    moon_index = SIGNS.index(chart.moon.sign)
    saturn_index = SIGNS.index(saturn_transit.point.sign)
    return (saturn_index - moon_index) % 12 in {11, 0, 1}


def _date_sign(value: date) -> str:
    month_day = (value.month, value.day)
    if month_day >= (3, 21) and month_day <= (4, 19):
        return "Aries"
    if month_day >= (4, 20) and month_day <= (5, 20):
        return "Taurus"
    if month_day >= (5, 21) and month_day <= (6, 20):
        return "Gemini"
    if month_day >= (6, 21) and month_day <= (7, 22):
        return "Cancer"
    if month_day >= (7, 23) and month_day <= (8, 22):
        return "Leo"
    if month_day >= (8, 23) and month_day <= (9, 22):
        return "Virgo"
    if month_day >= (9, 23) and month_day <= (10, 22):
        return "Libra"
    if month_day >= (10, 23) and month_day <= (11, 21):
        return "Scorpio"
    if month_day >= (11, 22) and month_day <= (12, 21):
        return "Sagittarius"
    if month_day >= (12, 22) or month_day <= (1, 19):
        return "Capricorn"
    if month_day >= (1, 20) and month_day <= (2, 18):
        return "Aquarius"
    return "Pisces"


def _best_sign_matches(sign: str, count: int) -> list[str]:
    element = SIGN_ELEMENTS.get(sign, "fire")
    allowed = COMPLEMENTARY_ELEMENTS.get(element, {element})
    matches = [candidate for candidate in SIGNS if candidate != sign and SIGN_ELEMENTS.get(candidate) == element]
    matches.extend(candidate for candidate in SIGNS if candidate != sign and SIGN_ELEMENTS.get(candidate) in allowed and candidate not in matches)
    return [f"{candidate} - {_match_reason(sign, candidate)}" for candidate in matches[:count]]


def _challenging_signs(sign: str) -> list[str]:
    index = SIGNS.index(sign)
    candidates = [SIGNS[(index + 3) % 12], SIGNS[(index + 6) % 12], SIGNS[(index + 9) % 12]]
    return [f"{candidate} - strong chemistry needs patience and clear boundaries" for candidate in candidates]


def _match_reason(user_sign: str, match_sign: str) -> str:
    user_element = SIGN_ELEMENTS.get(user_sign)
    match_element = SIGN_ELEMENTS.get(match_sign)
    if user_element == match_element:
        return "natural emotional rhythm and shared instinct"
    if match_element in COMPLEMENTARY_ELEMENTS.get(user_element or "", set()):
        return "good balance between emotion, thinking, and movement"
    return "growth match if communication stays honest"


def _sign_pair_guidance(user_sign: str, partner_sign: str) -> str:
    if partner_sign not in SIGN_ELEMENTS:
        return "add the partner birth date for a clearer sign rhythm."
    user_element = SIGN_ELEMENTS[user_sign]
    partner_element = SIGN_ELEMENTS[partner_sign]
    if user_element == partner_element:
        return "easy emotional recognition, but both people must avoid reacting in the same old pattern."
    if partner_element in COMPLEMENTARY_ELEMENTS[user_element]:
        return "strong attraction can become stable when both people respect each other's pace."
    return "the bond can teach maturity, but peace needs direct communication and fewer assumptions."


def _compatibility_score(
    user_sign: str,
    partner_sign: str,
    user_life_path: int,
    partner_life_path: int | None,
    user_name_number: int,
    partner_name_number: int,
) -> int:
    score = 54
    if partner_sign in SIGN_ELEMENTS:
        if SIGN_ELEMENTS[user_sign] == SIGN_ELEMENTS[partner_sign]:
            score += 18
        elif SIGN_ELEMENTS[partner_sign] in COMPLEMENTARY_ELEMENTS[SIGN_ELEMENTS[user_sign]]:
            score += 13
        else:
            score += 5
    if partner_life_path:
        score += 10 if partner_life_path in NUMBER_COMPATIBILITY.get(user_life_path, set()) else 3
    score += 7 if partner_name_number in NUMBER_COMPATIBILITY.get(user_name_number, set()) else 2
    return max(45, min(94, score))


def _numerology_lens(
    chart: ChartSnapshot,
    user_name_number: int,
    partner_name: str,
    partner_birth_number: int | None,
    partner_life_path: int | None,
    partner_name_number: int,
) -> str:
    partner_birth = partner_birth_number or "pending"
    partner_life = partner_life_path or "pending"
    return (
        f"Your birth number {chart.numerology.birth_number}, life path {chart.numerology.life_path_number}, and name number {user_name_number} "
        f"show how you seek rhythm and reassurance. {partner_name}'s birth number {partner_birth}, life path {partner_life}, and name number "
        f"{partner_name_number} show their outer style. When numbers clash, use slower conversations; when they support, turn the ease into shared routines."
    )


DEFAULT_DISCLAIMER = (
    "Astrology is reflective spiritual guidance, not medical, legal, financial, or crisis advice. "
    "Remedies are devotional and behavioral supports, not guaranteed fixes."
)
