"""Tests de los parsers (`parse_*`)."""

from datetime import date, datetime, timedelta
from fractions import Fraction

import pytest

import acodo.utils as iu


@pytest.mark.parametrize(
    ("raw", "lang", "decimals", "expected"),
    [
        (1234.5, None, 2, "1.234,50"),
        (1234.5, "en", 2, "1,234.50"),
        (1234.5, "ENG", 2, "1,234.50"),
        (1234.5678, "es", 3, "1.234,568"),
        (1234, None, 2, "1.234"),
        (1234, "en", 2, "1,234"),
        (Fraction(3), None, 2, "3"),
        (Fraction(1, 4), "en", 2, "0.25"),
    ],
)
def test_parse_amount(
    raw: float | Fraction, lang: str | None, decimals: int, expected: str
) -> None:
    assert iu.parse_amount(raw, lang, decimals) == expected


@pytest.mark.parametrize(
    ("raw", "lang", "expected"),
    [
        (True, None, "Sí"),
        (False, None, "No"),
        (True, "en", "Yes"),
        (False, "ENG", "No"),
        (True, "es", "Sí"),
    ],
)
def test_parse_bool(raw: bool, lang: str | None, expected: str) -> None:
    assert iu.parse_bool(raw, lang) == expected


@pytest.mark.parametrize("lang", ["e", "english", "e1", ""])
def test_invalid_lang(lang: str) -> None:
    with pytest.raises(ValueError, match="lenguaje"):
        iu.parse_amount(1, lang)
    with pytest.raises(ValueError, match="lenguaje"):
        iu.parse_datetime(date(2024, 1, 31), lang)
    with pytest.raises(ValueError, match="lenguaje"):
        iu.parse_percent(1, lang)


@pytest.mark.parametrize(
    ("raw", "lang", "expected"),
    [
        (date(2024, 1, 31), None, "31/01/2024"),
        (datetime(2024, 1, 31), None, "31/01/2024"),
        (datetime(2024, 1, 31, 10, 30), None, "31/01/2024 10:30"),
        (datetime(2024, 1, 31, 10, 30, 5), None, "31/01/2024 10:30:05"),
        (datetime(2024, 1, 31, 0, 0, 5), None, "31/01/2024 00:00:05"),
        (datetime(2024, 1, 31, 10, 30), "en", "2024-01-31 10:30"),
        (date(2024, 1, 31), "eng", "2024-01-31"),
    ],
)
def test_parse_datetime(raw: date, lang: str | None, expected: str) -> None:
    assert iu.parse_datetime(raw, lang) == expected


@pytest.mark.parametrize(
    ("raw", "lang", "decimals", "expected"),
    [
        (0.256, None, 1, "25,6 %"),
        (Fraction(1, 4), None, 1, "25 %"),
        (0.5, "en", 1, "50%"),
        (1 / 3, None, 2, "33,33 %"),
        (1, None, 0, "100 %"),
        (0, "en", 1, "0%"),
        (12.345, None, 1, "1.234,5 %"),
    ],
)
def test_parse_percent(
    raw: float | Fraction, lang: str | None, decimals: int, expected: str
) -> None:
    assert iu.parse_percent(raw, lang, decimals) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (0, "0 bytes"),
        (1, "1 byte"),
        (1023, "1023 bytes"),
        (1024, "1,000 KiB"),
        (1536, "1,500 KiB"),
        (1048575, "1023,999 KiB"),
        (1048576, "1,000 MiB"),
        (1024**3, "1,000 GiB"),
        (1024**4, "1,000 TiB"),
        (1024**5, "1,000 PiB"),
        (1024**6, "1024,000 PiB"),
    ],
)
def test_parse_size(raw: int, expected: str) -> None:
    assert iu.parse_size(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("¡Hola, Mundo! Ñandú", "hola-mundo-nandu"),
        ("  --Foo__Bar--  ", "foo-bar"),
        ("Straße 5", "strae-5"),
        ("€€€", ""),
        ("", ""),
    ],
)
def test_parse_slug(raw: str, expected: str) -> None:
    assert iu.parse_slug(raw) == expected


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "0:00"),
        (65, "1:05"),
        (3725, "1:02:05"),
        (90061, "25:01:01"),
        (-65, "-1:05"),
        (-3725, "-1:02:05"),
    ],
)
def test_parse_timedelta(seconds: int, expected: str) -> None:
    assert iu.parse_timedelta(timedelta(seconds=seconds)) == expected
