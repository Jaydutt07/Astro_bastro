from __future__ import annotations

import math
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .constants import NAKSHATRAS, SIGNS

J2000 = 2451545.0
SKYFIELD_TARGETS = {
    "Sun": ["sun"],
    "Moon": ["moon"],
    "Mercury": ["mercury"],
    "Venus": ["venus"],
    "Mars": ["mars", "mars barycenter"],
    "Jupiter": ["jupiter barycenter", "jupiter"],
    "Saturn": ["saturn barycenter", "saturn"],
}


@dataclass(frozen=True)
class PointParts:
    sign: str
    degree: float
    absolute_degree: float
    nakshatra: str
    pada: int


def normalize(degrees: float) -> float:
    return degrees % 360


def sind(degrees: float) -> float:
    return math.sin(math.radians(degrees))


def cosd(degrees: float) -> float:
    return math.cos(math.radians(degrees))


def atan2d(y: float, x: float) -> float:
    return math.degrees(math.atan2(y, x))


def lahiri_ayanamsa(jd: float) -> float:
    # Compact Lahiri approximation, good enough for MVP display and fixture-stable tests.
    return normalize(23.85675 + 0.013968 * ((jd - J2000) / 365.2425))


def obliquity(jd: float) -> float:
    t = (jd - J2000) / 36525
    return 23.439291 - 0.0130042 * t


def gmst(jd: float) -> float:
    t = (jd - J2000) / 36525
    return normalize(280.46061837 + 360.98564736629 * (jd - J2000) + 0.000387933 * t * t - t**3 / 38710000)


def sign_parts(absolute_degree: float) -> PointParts:
    absolute = normalize(absolute_degree)
    sign_index = int(absolute // 30)
    nak_span = 360 / 27
    nak_index = int(absolute // nak_span)
    nak_within = absolute % nak_span
    pada = int(nak_within // (nak_span / 4)) + 1
    return PointParts(
        sign=SIGNS[sign_index],
        degree=round(absolute % 30, 4),
        absolute_degree=round(absolute, 4),
        nakshatra=NAKSHATRAS[nak_index],
        pada=pada,
    )


def eccentric_anomaly(mean_anomaly: float, eccentricity: float) -> float:
    mean_rad = math.radians(normalize(mean_anomaly))
    anomaly = mean_rad
    for _ in range(8):
        anomaly = anomaly - (anomaly - eccentricity * math.sin(anomaly) - mean_rad) / (1 - eccentricity * math.cos(anomaly))
    return math.degrees(anomaly)


def sun_tropical_longitude(jd: float) -> tuple[float, float, float]:
    d = jd - 2451543.5
    perihelion = normalize(282.9404 + 4.70935e-5 * d)
    eccentricity = 0.016709 - 1.151e-9 * d
    mean_anomaly = normalize(356.0470 + 0.9856002585 * d)
    anomaly = eccentric_anomaly(mean_anomaly, eccentricity)
    xv = cosd(anomaly) - eccentricity
    yv = math.sqrt(1 - eccentricity * eccentricity) * sind(anomaly)
    true_anomaly = atan2d(yv, xv)
    radius = math.sqrt(xv * xv + yv * yv)
    longitude = normalize(true_anomaly + perihelion)
    return longitude, radius, true_anomaly


def planet_elements(name: str, d: float) -> tuple[float, float, float, float, float, float]:
    elements = {
        "Mercury": (
            48.3313 + 3.24587e-5 * d,
            7.0047 + 5e-8 * d,
            29.1241 + 1.01444e-5 * d,
            0.387098,
            0.205635 + 5.59e-10 * d,
            168.6562 + 4.0923344368 * d,
        ),
        "Venus": (
            76.6799 + 2.46590e-5 * d,
            3.3946 + 2.75e-8 * d,
            54.8910 + 1.38374e-5 * d,
            0.723330,
            0.006773 - 1.302e-9 * d,
            48.0052 + 1.6021302244 * d,
        ),
        "Mars": (
            49.5574 + 2.11081e-5 * d,
            1.8497 - 1.78e-8 * d,
            286.5016 + 2.92961e-5 * d,
            1.523688,
            0.093405 + 2.516e-9 * d,
            18.6021 + 0.5240207766 * d,
        ),
        "Jupiter": (
            100.4542 + 2.76854e-5 * d,
            1.3030 - 1.557e-7 * d,
            273.8777 + 1.64505e-5 * d,
            5.20256,
            0.048498 + 4.469e-9 * d,
            19.8950 + 0.0830853001 * d,
        ),
        "Saturn": (
            113.6634 + 2.38980e-5 * d,
            2.4886 - 1.081e-7 * d,
            339.3939 + 2.97661e-5 * d,
            9.55475,
            0.055546 - 9.499e-9 * d,
            316.9670 + 0.0334442282 * d,
        ),
    }
    return elements[name]


def planet_tropical_longitude(name: str, jd: float) -> float:
    skyfield_longitude = skyfield_tropical_longitude(name, jd)
    if skyfield_longitude is not None:
        return skyfield_longitude

    if name == "Sun":
        longitude, _, _ = sun_tropical_longitude(jd)
        return longitude
    if name == "Moon":
        return moon_tropical_longitude(jd)
    if name == "Rahu":
        return mean_lunar_node(jd)
    if name == "Ketu":
        return normalize(mean_lunar_node(jd) + 180)

    d = jd - 2451543.5
    node, inclination, perihelion, semi_major, eccentricity, mean_anomaly = planet_elements(name, d)
    anomaly = eccentric_anomaly(mean_anomaly, eccentricity)
    xv = semi_major * (cosd(anomaly) - eccentricity)
    yv = semi_major * math.sqrt(1 - eccentricity * eccentricity) * sind(anomaly)
    true_anomaly = atan2d(yv, xv)
    radius = math.sqrt(xv * xv + yv * yv)

    xh = radius * (cosd(node) * cosd(true_anomaly + perihelion) - sind(node) * sind(true_anomaly + perihelion) * cosd(inclination))
    yh = radius * (sind(node) * cosd(true_anomaly + perihelion) + cosd(node) * sind(true_anomaly + perihelion) * cosd(inclination))
    zh = radius * sind(true_anomaly + perihelion) * sind(inclination)

    sun_lon, sun_radius, _ = sun_tropical_longitude(jd)
    xs = sun_radius * cosd(sun_lon)
    ys = sun_radius * sind(sun_lon)

    xg = xh + xs
    yg = yh + ys
    zg = zh
    return normalize(atan2d(yg, xg + zg * 0))


def moon_tropical_longitude(jd: float) -> float:
    d = jd - 2451543.5
    node = normalize(125.1228 - 0.0529538083 * d)
    inclination = 5.1454
    perihelion = normalize(318.0634 + 0.1643573223 * d)
    semi_major = 60.2666
    eccentricity = 0.054900
    mean_anomaly = normalize(115.3654 + 13.0649929509 * d)
    anomaly = eccentric_anomaly(mean_anomaly, eccentricity)
    xv = semi_major * (cosd(anomaly) - eccentricity)
    yv = semi_major * math.sqrt(1 - eccentricity * eccentricity) * sind(anomaly)
    true_anomaly = atan2d(yv, xv)
    radius = math.sqrt(xv * xv + yv * yv)
    xh = radius * (cosd(node) * cosd(true_anomaly + perihelion) - sind(node) * sind(true_anomaly + perihelion) * cosd(inclination))
    yh = radius * (sind(node) * cosd(true_anomaly + perihelion) + cosd(node) * sind(true_anomaly + perihelion) * cosd(inclination))
    return normalize(atan2d(yh, xh))


def mean_lunar_node(jd: float) -> float:
    t = (jd - J2000) / 36525
    return normalize(125.04452 - 1934.136261 * t + 0.0020708 * t * t + (t**3) / 450000)


def active_ephemeris_engine() -> str:
    if _skyfield_bundle() is not None:
        return "Skyfield/JPL DE421 geocentric ecliptic longitude + Lahiri approximation"
    return "Compact orbital fallback + Lahiri approximation"


def skyfield_tropical_longitude(name: str, jd: float) -> float | None:
    if name not in SKYFIELD_TARGETS:
        return None
    bundle = _skyfield_bundle()
    if bundle is None:
        return None

    try:
        eph, timescale, ecliptic_frame = bundle
        time = timescale.ut1_jd(jd)
        earth = eph["earth"]
        target = _skyfield_target(eph, name)
        apparent = earth.at(time).observe(target).apparent()
        _, longitude, _ = apparent.frame_latlon(ecliptic_frame)
        return normalize(longitude.degrees)
    except Exception:
        return None


def _skyfield_target(ephemeris, name: str):
    for target_name in SKYFIELD_TARGETS[name]:
        try:
            return ephemeris[target_name]
        except Exception:
            continue
    raise KeyError(name)


@lru_cache(maxsize=1)
def _skyfield_bundle():
    if os.getenv("TRUST_ASTRO_DISABLE_SKYFIELD") == "1":
        return None
    try:
        from skyfield.api import Loader
        from skyfield.framelib import ecliptic_frame

        cache_dir = Path(os.getenv("TRUST_ASTRO_EPHEMERIS_DIR", Path.home() / ".trust-astro" / "ephemeris"))
        loader = Loader(str(cache_dir))
        ephemeris_name = os.getenv("TRUST_ASTRO_EPHEMERIS_FILE", "de421.bsp")
        ephemeris = loader(ephemeris_name)
        return ephemeris, loader.timescale(), ecliptic_frame
    except Exception:
        return None


def sidereal_longitude(name: str, jd: float) -> float:
    return normalize(planet_tropical_longitude(name, jd) - lahiri_ayanamsa(jd))


def ascendant_sidereal(jd: float, latitude: float, longitude: float) -> float:
    theta = math.radians(normalize(gmst(jd) + longitude))
    eps = math.radians(obliquity(jd))
    phi = math.radians(latitude)
    numerator = -math.cos(theta)
    denominator = math.sin(theta) * math.cos(eps) + math.tan(phi) * math.sin(eps)
    tropical_asc = normalize(math.degrees(math.atan2(numerator, denominator)) + 180)
    return normalize(tropical_asc - lahiri_ayanamsa(jd))
