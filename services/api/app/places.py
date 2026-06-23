from __future__ import annotations

from functools import lru_cache

import httpx
from pydantic import BaseModel


class PlaceResult(BaseModel):
    id: str
    label: str
    latitude: float
    longitude: float
    timezone: str
    source: str


SEED_PLACES = [
    PlaceResult(id="seed-umarga", label="Umarga, Maharashtra, India", latitude=17.8367, longitude=76.6206, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-mumbai", label="Mumbai, Maharashtra, India", latitude=19.0760, longitude=72.8777, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-pune", label="Pune, Maharashtra, India", latitude=18.5204, longitude=73.8567, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-hyderabad", label="Hyderabad, Telangana, India", latitude=17.3850, longitude=78.4867, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-bengaluru", label="Bengaluru, Karnataka, India", latitude=12.9716, longitude=77.5946, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-delhi", label="Delhi, India", latitude=28.6139, longitude=77.2090, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-kolkata", label="Kolkata, West Bengal, India", latitude=22.5726, longitude=88.3639, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-chennai", label="Chennai, Tamil Nadu, India", latitude=13.0827, longitude=80.2707, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-jaipur", label="Jaipur, Rajasthan, India", latitude=26.9124, longitude=75.7873, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-ahmedabad", label="Ahmedabad, Gujarat, India", latitude=23.0225, longitude=72.5714, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-lucknow", label="Lucknow, Uttar Pradesh, India", latitude=26.8467, longitude=80.9462, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-kochi", label="Kochi, Kerala, India", latitude=9.9312, longitude=76.2673, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-chandigarh", label="Chandigarh, India", latitude=30.7333, longitude=76.7794, timezone="Asia/Kolkata", source="seed"),
    PlaceResult(id="seed-indore", label="Indore, Madhya Pradesh, India", latitude=22.7196, longitude=75.8577, timezone="Asia/Kolkata", source="seed"),
]


async def search_places(query: str, limit: int = 6) -> list[PlaceResult]:
    clean_query = " ".join(query.strip().split())
    if len(clean_query) < 2:
        return []

    seeded = _search_seed(clean_query, limit)
    remote = await _search_nominatim(clean_query, max(limit - len(seeded), 0))
    seen: set[str] = set()
    merged: list[PlaceResult] = []
    for place in seeded + remote:
        key = f"{place.label.lower()}:{round(place.latitude, 3)}:{round(place.longitude, 3)}"
        if key not in seen:
            seen.add(key)
            merged.append(place)
    return merged[:limit]


def _search_seed(query: str, limit: int) -> list[PlaceResult]:
    lowered = query.lower()
    matches = [place for place in SEED_PLACES if lowered in place.label.lower()]
    starts = [place for place in SEED_PLACES if place.label.lower().startswith(lowered)]
    ordered = starts + [place for place in matches if place not in starts]
    return ordered[:limit]


async def _search_nominatim(query: str, limit: int) -> list[PlaceResult]:
    if limit <= 0:
        return []
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "jsonv2", "limit": limit, "addressdetails": 1},
                headers={"User-Agent": "TrustAstroMVP/0.1 contact=local-dev"},
            )
            response.raise_for_status()
            rows = response.json()
    except Exception:
        return []

    places: list[PlaceResult] = []
    for index, row in enumerate(rows):
        latitude = float(row["lat"])
        longitude = float(row["lon"])
        places.append(
            PlaceResult(
                id=f"osm-{row.get('osm_type', 'place')}-{row.get('osm_id', index)}",
                label=row.get("display_name", query),
                latitude=latitude,
                longitude=longitude,
                timezone=infer_timezone(latitude, longitude),
                source="openstreetmap",
            )
        )
    return places


def infer_timezone(latitude: float, longitude: float) -> str:
    timezone = _timezonefinder_lookup(latitude, longitude)
    if timezone:
        return timezone
    if 6 <= latitude <= 37 and 68 <= longitude <= 98:
        return "Asia/Kolkata"
    return "UTC"


@lru_cache(maxsize=1)
def _timezonefinder():
    try:
        from timezonefinder import TimezoneFinder

        return TimezoneFinder()
    except Exception:
        return None


def _timezonefinder_lookup(latitude: float, longitude: float) -> str | None:
    finder = _timezonefinder()
    if not finder:
        return None
    try:
        return finder.timezone_at(lat=latitude, lng=longitude) or finder.closest_timezone_at(lat=latitude, lng=longitude)
    except Exception:
        return None
