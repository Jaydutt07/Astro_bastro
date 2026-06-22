from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo


def parse_birth_datetime(birth_date, birth_time: str, timezone_name: str) -> datetime:
    hour_text, minute_text, *_ = birth_time.split(":")
    local_time = time(hour=int(hour_text), minute=int(minute_text))
    return datetime.combine(birth_date, local_time, tzinfo=ZoneInfo(timezone_name))


def julian_day(moment_utc: datetime) -> float:
    moment = moment_utc.astimezone(ZoneInfo("UTC"))
    year = moment.year
    month = moment.month
    day = moment.day + (
        moment.hour
        + moment.minute / 60
        + moment.second / 3600
        + moment.microsecond / 3_600_000_000
    ) / 24

    if month <= 2:
        year -= 1
        month += 12

    correction_a = int(year / 100)
    correction_b = 2 - correction_a + int(correction_a / 4)
    return (
        int(365.25 * (year + 4716))
        + int(30.6001 * (month + 1))
        + day
        + correction_b
        - 1524.5
    )
