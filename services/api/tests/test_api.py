import os
import tempfile
from pathlib import Path

import pytest

TEST_DB = Path(tempfile.gettempdir()) / "trust_astro_pytest.db"
TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient

from app.main import app
from app.reading import _normalize_payload, _reject_draft_artifacts, _reject_incomplete_strings
from app.safety import reading_guardrail


client = TestClient(app)

PROFILE = {
    "fullName": "Jay Kulkarni",
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


def test_profile_chart_daily_purchase_and_delete_flow():
    headers = {"X-User-Id": "pytest-user"}
    assert client.post("/profile", json=PROFILE, headers=headers).status_code == 200

    chart_response = client.get("/chart/natal", headers=headers)
    assert chart_response.status_code == 200
    assert chart_response.json()["ascendant"]["sign"] == "Libra"

    reading_response = client.get("/reading/daily", headers=headers)
    assert reading_response.status_code == 200
    reading = reading_response.json()
    assert reading["headline"]
    assert len(reading["astroEvidence"]) >= 3
    assert reading["entitlement"]["freeLimit"] == 1
    assert reading["entitlement"]["freeRemaining"] == 0

    weekly_response = client.get("/reading/weekly", headers=headers)
    assert weekly_response.status_code == 402
    assert "free reading" in weekly_response.json()["detail"].lower()

    problem_response = client.post(
        "/problem/insight",
        headers=headers,
        json={
            "category": "shani",
            "problemDetails": "I feel blocked in career and worried this is connected to Saade Saati.",
        },
    )
    assert problem_response.status_code == 200
    problem = problem_response.json()
    assert problem["freeSolution"]["isFree"] is True
    assert len(problem["premiumSolutions"]) == 3
    assert problem["entitlement"]["freeRemaining"] == 1

    harmony_response = client.post(
        "/harmony/insight",
        headers=headers,
        json={
            "partnerName": "Aarohi Sharma",
            "partnerBirthDate": "2001-08-14",
            "relationshipFocus": "marriage",
        },
    )
    assert harmony_response.status_code == 200
    harmony = harmony_response.json()
    assert harmony["compatibilityScore"] >= 45
    assert harmony["user"]["lifePathNumber"] == 5
    assert harmony["partner"]["birthNumber"] == 5
    assert len(harmony["bestMarriageMatches"]) >= 3

    second_problem_response = client.post(
        "/problem/insight",
        headers=headers,
        json={
            "category": "career",
            "problemDetails": "I keep facing delays in work decisions and need a clearer path.",
        },
    )
    assert second_problem_response.status_code == 200
    assert second_problem_response.json()["entitlement"]["freeRemaining"] == 0

    third_problem_response = client.post(
        "/problem/insight",
        headers=headers,
        json={
            "category": "money",
            "problemDetails": "I feel anxious about money and want a deeper pattern check.",
        },
    )
    assert third_problem_response.status_code == 402
    assert "two free problem analyses" in third_problem_response.json()["detail"]

    memory_response = client.get("/memory/context", headers=headers)
    assert memory_response.status_code == 200
    memory = memory_response.json()["memory"]
    assert memory["problemCount"] == 2
    assert memory["recentProblems"][0]["category"] == "shani"

    purchase_response = client.post(
        "/reports/purchase",
        headers=headers,
        json={
            "reportKind": "career",
            "productId": "trustastro_career_report",
            "appUserId": "pytest-user",
            "receiptToken": "local-demo",
        },
    )
    assert purchase_response.status_code == 200
    assert purchase_response.json()["unlocked"] is True

    solution_response = client.post(
        "/solutions/unlock",
        headers=headers,
        json={
            "productId": "astrosolves_solution_subscription",
            "appUserId": "pytest-user",
            "receiptToken": "local-demo",
            "category": "shani",
            "problemDetails": "I need deeper remedy support for repeated delays.",
        },
    )
    assert solution_response.status_code == 200
    assert solution_response.json()["unlocked"] is True

    assert client.delete("/account", headers=headers).status_code == 200
    assert client.get("/memory/context", headers=headers).json()["memory"]["problemCount"] == 0
    assert client.get("/chart/natal", headers=headers).status_code == 404


def test_weekly_can_be_the_one_free_period_choice():
    headers = {"X-User-Id": "pytest-weekly-choice"}
    assert client.post("/profile", json=PROFILE, headers=headers).status_code == 200

    weekly_response = client.get("/reading/weekly", headers=headers)
    assert weekly_response.status_code == 200
    assert weekly_response.json()["entitlement"]["freeRemaining"] == 0

    daily_response = client.get("/reading/daily", headers=headers)
    assert daily_response.status_code == 402


def test_unsafe_ask_is_rejected():
    headers = {"X-User-Id": "pytest-unsafe"}
    client.post("/profile", json=PROFILE, headers=headers)
    response = client.post("/ask", headers=headers, json={"question": "which stock will definitely make money?"})
    assert response.status_code == 400


def test_places_and_quality_endpoints():
    places = client.get("/places/search?q=Umarga")
    assert places.status_code == 200
    first_place = places.json()["results"][0]
    assert first_place["timezone"] == "Asia/Kolkata"

    quality = client.get("/quality/evaluate")
    assert quality.status_code == 200
    payload = quality.json()
    assert payload["average"] >= 10
    assert len(payload["scores"]) >= 3


def test_web_cors_preflight_for_profile_and_place_search():
    headers = {
        "Origin": "http://127.0.0.1:19006",
        "Access-Control-Request-Headers": "content-type,x-user-id",
    }
    place_preflight = client.options(
        "/places/search?q=Pune&limit=6",
        headers={**headers, "Access-Control-Request-Method": "GET"},
    )
    assert place_preflight.status_code == 200
    assert place_preflight.headers["access-control-allow-origin"] == "http://127.0.0.1:19006"

    profile_preflight = client.options(
        "/profile",
        headers={**headers, "Access-Control-Request-Method": "POST"},
    )
    assert profile_preflight.status_code == 200
    assert profile_preflight.headers["access-control-allow-origin"] == "http://127.0.0.1:19006"


def test_reading_guardrail_strips_markdown_and_stray_unicode():
    cleaned = reading_guardrail("**Power day** — guaranteed result.Next step.田")
    assert cleaned == "Power day - not guaranteed result. Next step."


def test_draft_artifact_detector_rejects_model_self_corrections():
    with pytest.raises(ValueError):
        _reject_draft_artifacts(
            {
                "doActions": [
                    "Keep routine clean; scale pe nahi, effort-wise zaroor stable. Rephrase? Wait final JSON cannot have analysis."
                ]
            }
        )


def test_incomplete_sentence_detector_rejects_clipped_outputs():
    with pytest.raises(ValueError):
        _reject_incomplete_strings({"reassurance": "The chart points to a Saturn discipline-and-"})
    with pytest.raises(ValueError):
        _reject_incomplete_strings({"why": "This can help convert anxiety while"})


def test_action_normalizer_removes_duplicate_do_avoid_prefixes_only_from_actions():
    payload = _normalize_payload(
        {
            "doActions": ["Do: Keep routine simple"],
            "dontActions": ["Avoid late-night overthinking"],
            "watchouts": ["Avoid assuming every delay is Saade Saati."],
        }
    )
    assert payload["doActions"] == ["Keep routine simple"]
    assert payload["dontActions"] == ["late-night overthinking"]
    assert payload["watchouts"] == ["Avoid assuming every delay is Saade Saati."]
