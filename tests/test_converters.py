"""Tests de los conversores (`to_*`)."""

import pathlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

import acodo.utils as iu


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (2, None),
        (-1, None),
        ("Sí", True),
        ("1", True),
        (" OFF ", False),
        ("no", False),
        ("quizá", None),
        ("", None),
        (None, None),
    ],
)
def test_to_bool(raw: object, expected: bool | None) -> None:
    assert iu.to_bool(raw) is expected  # ty: ignore[invalid-argument-type]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1,5 GiB", 1610612736),
        ("1.5 MiB", 1572864),
        ("2 kB", 2048),
        ("2 KB", 2048),
        ("1 MB", 1024**2),
        ("1 MiB", 1024**2),
        ("1 GB", 1024**3),
        ("512", 512),
        ("512 bytes", 512),
        ("1.234,5 KB", 1264128),
        ("1,234.5 kB", 1264128),
        (" 1 PiB ", 1024**5),
        ("1 furlong", None),
        ("abc", None),
        ("", None),
        ("-1 KiB", None),
        ("1.2.3 KiB", None),
        ("9" * 400, None),
        (None, None),
    ],
)
def test_to_bytes(raw: str | None, expected: int | None) -> None:
    assert iu.to_bytes(raw) == expected


def test_to_date() -> None:
    assert iu.to_date("31/01/2024") == date(2024, 1, 31)
    assert iu.to_date("basura") is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # ISO 8601
        ("2024-01-31", datetime(2024, 1, 31)),
        ("2024-01-31T10:30:00", datetime(2024, 1, 31)),
        ("2024-01-31T10:30:00Z", datetime(2024, 1, 31)),
        ("2024-01-31T10:30:00z", datetime(2024, 1, 31)),
        ("2024-01-31T10:30:00+02:00", datetime(2024, 1, 31)),
        (" 2024-01-31 ", datetime(2024, 1, 31)),
        # Unix timestamp
        ("1700000000", datetime(2023, 11, 14)),
        ("100000000", datetime(1973, 3, 3)),
        ("99999999999", None),
        # Nombres de mes
        ("Wed Jan 31 10:30:00 2024", datetime(2024, 1, 31)),
        ("Jan 31 10:30:00 2024", datetime(2024, 1, 31)),
        ("Jan 31 2024", datetime(2024, 1, 31)),
        ("31 Jan 2024", datetime(2024, 1, 31)),
        ("31 January 2024", datetime(2024, 1, 31)),
        ("January 31 2024", datetime(2024, 1, 31)),
        # Numéricos no ISO (día primero)
        ("2024/01/31", datetime(2024, 1, 31)),
        ("2024.01.31", datetime(2024, 1, 31)),
        ("31-01-2024", datetime(2024, 1, 31)),
        ("31/01/2024", datetime(2024, 1, 31)),
        ("31.01.2024", datetime(2024, 1, 31)),
        # RFC 2822
        ("Wed, 31 Jan 2024 10:30:00 +0000", datetime(2024, 1, 31)),
        # Inválidos
        ("basura", None),
        ("", None),
        ("32/01/2024", None),
    ],
)
def test_to_datetime(raw: str, expected: datetime | None) -> None:
    assert iu.to_datetime(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0.10", Decimal("0.10")),
        (0.1, Decimal("0.1")),
        (1, Decimal(1)),
        (" 1.5 ", Decimal("1.5")),
        ("nan", None),
        ("inf", None),
        (float("nan"), None),
        ("1_0", None),
        ("", None),
        ("abc", None),
        (True, None),
        (None, None),
    ],
)
def test_to_decimal(raw: object, expected: Decimal | None) -> None:
    assert iu.to_decimal(raw) == expected  # ty: ignore[invalid-argument-type]


@dataclass
class _Child:
    city: str


@dataclass
class _Parent:
    name: str
    child: _Child


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"a": 1}, {"a": 1}),
        ([("a", 1), ("b", 2)], {"a": 1, "b": 2}),
        ({"a": {"b": 1}}, {"a": {"b": 1}}),
        (
            {"p": _Parent("ana", _Child("Madrid"))},
            {"p": {"name": "ana", "child": {"city": "Madrid"}}},
        ),
        (
            _Parent("ana", _Child("Madrid")),
            {"name": "ana", "child": {"city": "Madrid"}},
        ),
        (None, None),
        ({}, None),
        ("", None),
        (42, None),
        ([1, 2], None),
        ([("a", 1, 2)], None),
        (["ab", "cd"], None),
    ],
)
def test_to_dict(raw: object, expected: dict | None) -> None:
    assert iu.to_dict(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1.5", 1.5),
        (" 2 ", 2.0),
        (2, 2.0),
        ("nan", None),
        ("inf", None),
        ("1_000", None),
        ("abc", None),
        (10**400, None),
        ([], None),
        (True, None),
        (None, None),
    ],
)
def test_to_float(raw: object, expected: float | None) -> None:
    assert iu.to_float(raw) == expected  # ty: ignore[invalid-argument-type]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("42", 42),
        (42, 42),
        (3.0, 3),
        (3.7, None),
        (float("inf"), None),
        (float("nan"), None),
        ("1_000", None),
        ("3.0", None),
        ("abc", None),
        ([], None),
        (True, None),
        (None, None),
    ],
)
def test_to_int(raw: object, expected: int | None) -> None:
    assert iu.to_int(raw) == expected  # ty: ignore[invalid-argument-type]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ([1, [2, 3]], [1, 2, 3]),
        ((1, (2, (3, 4))), [1, 2, 3, 4]),
        ([], None),
        ([[], ()], None),
        ([None, 1], [1]),
        ("abc", ["abc"]),
        (b"xy", [b"xy"]),
        (5, [5]),
        (None, None),
    ],
)
def test_to_list(raw: object, expected: list | None) -> None:
    assert iu.to_list(raw) == expected


class TestToPath:
    def test_valid(self) -> None:
        expected = pathlib.Path("carpeta/fichero.txt")
        assert iu.to_path("carpeta/fichero.txt") == expected
        assert iu.to_path(expected) == expected

    def test_expands_user(self) -> None:
        assert iu.to_path("~") == pathlib.Path.home()

    @pytest.mark.parametrize("raw", [None, "", "   ", "a\0b", 123, b"abc"])
    def test_invalid(self, raw: object) -> None:
        assert iu.to_path(raw) is None  # ty: ignore[invalid-argument-type]

    def test_expanduser_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def boom(self: pathlib.Path) -> pathlib.Path:
            raise RuntimeError("sin home")

        monkeypatch.setattr(pathlib.Path, "expanduser", boom)
        assert iu.to_path("~") is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("8080", 8080),
        (80, 80),
        (" 443 ", 443),
        ("1", 1),
        ("65535", 65535),
        ("0", None),
        (0, None),
        ("65536", None),
        (70000, None),
        ("-1", None),
        ("3.5", None),
        ("abc", None),
        (True, None),
        (None, None),
    ],
)
def test_to_port(raw: object, expected: int | None) -> None:
    assert iu.to_port(raw) == expected  # ty: ignore[invalid-argument-type]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("a", "a"), (" a ", " a "), ("", None), ("   ", None), (1, None), (None, None)],
)
def test_to_str(raw: object, expected: str | None) -> None:
    assert iu.to_str(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (90, timedelta(seconds=90)),
        (-5, timedelta(seconds=-5)),
        (1.5, timedelta(seconds=1.5)),
        (None, None),
        (True, None),
        (float("nan"), None),
        (float("inf"), None),
        (1e13, None),
        (-1e13, None),
        ("1h 30m", timedelta(hours=1, minutes=30)),
        ("1 min 30 s", timedelta(seconds=90)),
        ("2d", timedelta(days=2)),
        ("45s", timedelta(seconds=45)),
        ("1,5h", timedelta(minutes=90)),
        (" 1H ", timedelta(hours=1)),
        ("1h30x", None),
        ("1m30", None),
        ("5", None),
        ("", None),
        ("99999999999999d", None),
    ],
)
def test_to_timedelta(raw: str | float | None, expected: timedelta | None) -> None:
    assert iu.to_timedelta(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('{"a": [1, 2]}', {"a": [1, 2]}),
        (b"[1, 2]", [1, 2]),
        ("true", True),
        ("null", None),
        ("{'a': 1}", None),
        ("NaN", None),
        ("Infinity", None),
        ("", None),
        (None, None),
        ("[" * 100_000, None),
    ],
    ids=[
        "object",
        "bytes",
        "true",
        "null",
        "single-quotes",
        "nan",
        "infinity",
        "empty",
        "none",
        "deeply-nested",
    ],
)
def test_to_json(raw: str | bytes | None, expected: object) -> None:
    assert iu.to_json(raw) == expected
