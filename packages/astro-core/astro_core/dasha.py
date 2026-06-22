from __future__ import annotations

from datetime import date

from .constants import NAKSHATRA_LORDS, VIMSHOTTARI_YEARS

DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
TOTAL_YEARS = 120


def vimshottari_dasha(moon_absolute_degree: float, birth_date: date, for_date: date) -> tuple[str, str, float]:
    nak_span = 360 / 27
    nak_index = int((moon_absolute_degree % 360) // nak_span)
    lord = NAKSHATRA_LORDS[nak_index]
    lord_years = VIMSHOTTARI_YEARS[lord]
    elapsed_fraction = ((moon_absolute_degree % nak_span) / nak_span)
    balance_at_birth = lord_years * (1 - elapsed_fraction)
    age_days = max((for_date - birth_date).days, 0)
    age_years = age_days / 365.2425
    dasha_clock = (lord_years - balance_at_birth + age_years) % TOTAL_YEARS

    cursor = 0.0
    maha = lord
    for planet in DASHA_SEQUENCE[DASHA_SEQUENCE.index(lord) :] + DASHA_SEQUENCE[: DASHA_SEQUENCE.index(lord)]:
        span = VIMSHOTTARI_YEARS[planet]
        if cursor <= dasha_clock < cursor + span:
            maha = planet
            inner_elapsed = dasha_clock - cursor
            antardasha = _antardasha(planet, inner_elapsed)
            return maha, antardasha, round(balance_at_birth, 2)
        cursor += span

    return maha, maha, round(balance_at_birth, 2)


def _antardasha(mahadasha: str, elapsed_years: float) -> str:
    cursor = 0.0
    order = DASHA_SEQUENCE[DASHA_SEQUENCE.index(mahadasha) :] + DASHA_SEQUENCE[: DASHA_SEQUENCE.index(mahadasha)]
    for planet in order:
        span = VIMSHOTTARI_YEARS[mahadasha] * VIMSHOTTARI_YEARS[planet] / TOTAL_YEARS
        if cursor <= elapsed_years < cursor + span:
            return planet
        cursor += span
    return mahadasha
