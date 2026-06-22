from datetime import date

from astro_core import BirthProfile, build_chart_snapshot, build_fallback_reading


def test_umarga_birth_chart_core_signatures():
    profile = BirthProfile.model_validate(
        {
            "birthDate": "2002-03-07",
            "birthTime": "22:44",
            "birthplaceText": "Umarga, Maharashtra, India",
            "latitude": 17.8367,
            "longitude": 76.6206,
            "timezone": "Asia/Kolkata",
            "language": "en-IN",
            "consent": {
                "privacyAccepted": True,
                "aiPersonalization": True,
                "marketingOptIn": False,
            },
        }
    )

    chart = build_chart_snapshot(profile, for_date=date(2026, 6, 22))

    assert chart.ascendant.sign == "Libra"
    assert chart.moon.sign == "Sagittarius"
    assert chart.calculation_engine
    assert chart.numerology.birth_number == 7
    assert chart.numerology.life_path_number == 5
    assert chart.dasha.mahadasha
    assert len(chart.planets) == 9
    assert len(chart.transits) == 9


def test_fallback_reading_has_evidence_and_guardrails():
    profile = BirthProfile.model_validate(
        {
            "birthDate": "2002-03-07",
            "birthTime": "22:44",
            "birthplaceText": "Umarga, Maharashtra, India",
            "latitude": 17.8367,
            "longitude": 76.6206,
            "timezone": "Asia/Kolkata",
            "language": "en-IN",
            "consent": {"privacyAccepted": True},
        }
    )
    chart = build_chart_snapshot(profile, for_date=date(2026, 6, 22))
    reading = build_fallback_reading(chart)

    assert reading.headline
    assert len(reading.astro_evidence) >= 3
    assert "not medical" in reading.safety_disclaimer
