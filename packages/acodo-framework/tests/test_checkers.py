"""Tests de las comprobaciones (`has_*`)."""

import acodo.utils as iu


def test_has_required_attrs() -> None:
    assert iu.has_required_attrs("texto", ["upper", "lower"])
    assert iu.has_required_attrs("texto", [])
    assert not iu.has_required_attrs("texto", ["upper", "append"])


def test_has_required_fields() -> None:
    assert iu.has_required_fields([1, 2, 3], [1, 3])
    assert iu.has_required_fields([1], [])
    assert not iu.has_required_fields([1, 2], [1, 5])


def test_has_required_keys() -> None:
    assert iu.has_required_keys({"a": 1, "b": 2}, ["a", "b"])
    assert iu.has_required_keys({}, [])
    assert not iu.has_required_keys({"a": 1}, ["a", "b"])
