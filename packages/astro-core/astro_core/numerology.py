from __future__ import annotations

from datetime import date


def digital_root(value: int) -> int:
    while value > 9:
        value = sum(int(digit) for digit in str(value))
    return value


def life_path_number(birth_date: date) -> int:
    return digital_root(sum(int(digit) for digit in birth_date.strftime("%Y%m%d")))


def birth_number(birth_date: date) -> int:
    return digital_root(birth_date.day)


def personal_year_number(birth_date: date, for_date: date) -> int:
    return digital_root(birth_date.month + birth_date.day + for_date.year)


def personal_day_number(birth_date: date, for_date: date) -> int:
    return digital_root(personal_year_number(birth_date, for_date) + for_date.month + for_date.day)
