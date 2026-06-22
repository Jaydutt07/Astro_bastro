import os
import tempfile
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / "trust_astro_pytest.db"
TEST_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

PROFILE = {
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

    assert client.delete("/account", headers=headers).status_code == 200
    assert client.get("/chart/natal", headers=headers).status_code == 404


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
