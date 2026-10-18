"""Tests de los getters (`get_*`)."""

import pathlib
import sys
from typing import assert_type

import pytest

import acodo.utils as iu
from acodo.utils import to_bool, to_float, to_int


def test_get_env_returns_str_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IRG_PORT", "8080")
    assert iu.get_env("IRG_PORT") == "8080"


def test_get_env_converts_with_to_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IRG_PORT", "8080")
    assert iu.get_env("IRG_PORT", cast=to_int) == 8080


def test_get_env_with_custom_cast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IRG_RATIO", "0.5")
    assert iu.get_env("IRG_RATIO", cast=to_float) == 0.5
    monkeypatch.setenv("IRG_FLAG", "1")
    assert iu.get_env("IRG_FLAG", cast=to_bool) is True


def test_get_env_missing_returns_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IRG_AUSENTE", raising=False)
    assert iu.get_env("IRG_AUSENTE", default="x") == "x"
    assert iu.get_env("IRG_AUSENTE", cast=to_bool, default=False) is False


def test_get_env_unconvertible_returns_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IRG_PORT", "no-es-numero")
    assert iu.get_env("IRG_PORT", cast=to_int, default=-1) == -1
    assert iu.get_env("IRG_PORT", cast=to_bool, default=False) is False


def test_get_env_required_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IRG_PORT", "8080")
    assert iu.get_env("IRG_PORT", required=True) == "8080"
    assert iu.get_env("IRG_PORT", to_int, required=True) == 8080


@pytest.mark.parametrize("value", [None, "", "   ", "no-es-numero"])
def test_get_env_required_fails_when_missing_or_invalid(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv("IRG_PORT", raising=False)
    else:
        monkeypatch.setenv("IRG_PORT", value)
    with pytest.raises(ValueError, match="IRG_PORT"):
        iu.get_env("IRG_PORT", to_int, required=True)


def test_get_env_required_and_default_are_incompatible() -> None:
    with pytest.raises(ValueError, match="incompatibles"):
        iu.get_env("IRG_PORT", to_int, 1, required=True)  # ty: ignore[invalid-argument-type]


def test_get_env_return_types(monkeypatch: pytest.MonkeyPatch) -> None:
    # Comprobación estática de las sobrecargas (`ty` falla si no coinciden).
    monkeypatch.setenv("IRG_PORT", "8080")
    assert_type(iu.get_env("IRG_PORT"), str | None)
    assert_type(iu.get_env("IRG_PORT", default="x"), str)
    assert_type(iu.get_env("IRG_PORT", required=True), str)
    assert_type(iu.get_env("IRG_PORT", to_int), int | None)
    assert_type(iu.get_env("IRG_PORT", to_int, 1), int)
    assert_type(iu.get_env("IRG_PORT", to_int, required=True), int)


def test_get_hash_text() -> None:
    assert iu.get_hash("abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_get_hash_bytes_and_algorithm() -> None:
    assert iu.get_hash(b"abc", "sha1") == "a9993e364706816aba3e25717850c26c9cd0d89d"
    assert iu.get_hash("abc", "sha256") == iu.get_hash(b"abc")


def test_get_hash_does_not_read_files(tmp_path: pathlib.Path) -> None:
    file = tmp_path / "datos.bin"
    file.write_bytes(b"contenido")
    assert iu.get_hash(str(file)) != iu.get_hash(b"contenido")


def test_get_file_hash_matches_bytes(tmp_path: pathlib.Path) -> None:
    file = tmp_path / "datos.bin"
    content = b"contenido de prueba " * 5000
    file.write_bytes(content)
    assert iu.get_file_hash(file) == iu.get_hash(content)
    assert iu.get_file_hash(str(file), "sha1") == iu.get_hash(content, "sha1")


def test_get_file_hash_invalid_algorithm(tmp_path: pathlib.Path) -> None:
    file = tmp_path / "datos.bin"
    file.write_bytes(b"x")
    with pytest.raises(ValueError, match="no soportado"):
        iu.get_file_hash(file, "algoritmo-inexistente")


def test_get_file_hash_missing_file(tmp_path: pathlib.Path) -> None:
    with pytest.raises(FileNotFoundError):
        iu.get_file_hash(tmp_path / "no-existe")


def test_get_hash_invalid_algorithm() -> None:
    with pytest.raises(ValueError, match="no soportado"):
        iu.get_hash("abc", "algoritmo-inexistente")


def test_get_hmac_known_vector() -> None:
    # Vector de prueba RFC 4231 (caso 2).
    assert iu.get_hmac("Jefe", "what do ya want for nothing?") == (
        "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
    )


def test_get_hmac_str_and_bytes_equivalent() -> None:
    assert iu.get_hmac("clave", "mensaje") == iu.get_hmac(b"clave", b"mensaje")


def test_get_hmac_depends_on_key() -> None:
    assert iu.get_hmac("clave-a", "mensaje") != iu.get_hmac("clave-b", "mensaje")


def test_get_hmac_invalid_algorithm() -> None:
    with pytest.raises(ValueError, match="no soportado"):
        iu.get_hmac("clave", "mensaje", "algoritmo-inexistente")


def test_get_now_is_aware_utc() -> None:
    from datetime import UTC

    now = iu.get_now()
    assert now.tzinfo is not None
    assert now.utcoffset() == UTC.utcoffset(None)


def test_get_now_within_call_window() -> None:
    from datetime import UTC, datetime

    before = datetime.now(UTC)
    now = iu.get_now()
    after = datetime.now(UTC)
    assert before <= now <= after


def test_get_otp_format() -> None:
    assert len(iu.get_otp()) == 6
    assert iu.get_otp().isdigit()
    assert len(iu.get_otp(8)) == 8


def test_get_otp_invalid_digits() -> None:
    with pytest.raises(ValueError, match="digits"):
        iu.get_otp(0)
    with pytest.raises(ValueError, match="digits"):
        iu.get_otp(True)


def test_get_password_hash_deterministic() -> None:
    first = iu.get_password_hash("secreto", "sal", iterations=1000)
    second = iu.get_password_hash("secreto", "sal", iterations=1000)
    assert first == second
    assert len(first) == 64  # SHA-256 -> 32 bytes -> 64 hex.


def test_get_password_hash_str_and_bytes_equivalent() -> None:
    assert iu.get_password_hash("sec", "sal", iterations=10) == iu.get_password_hash(
        b"sec", b"sal", iterations=10
    )


def test_get_password_hash_depends_on_salt() -> None:
    assert iu.get_password_hash("sec", "sal-a", iterations=10) != iu.get_password_hash(
        "sec", "sal-b", iterations=10
    )


def test_get_password_hash_invalid_args() -> None:
    with pytest.raises(ValueError, match="iterations"):
        iu.get_password_hash("sec", "sal", iterations=0)
    with pytest.raises(ValueError, match="no soportado"):
        iu.get_password_hash("sec", "sal", algorithm="algoritmo-inexistente")


def test_get_random_choice_returns_element() -> None:
    options = ["a", "b", "c"]
    for _ in range(20):
        assert iu.get_random_choice(options) in options


def test_get_random_choice_single_element() -> None:
    assert iu.get_random_choice([42]) == 42


def test_get_random_choice_empty_raises() -> None:
    with pytest.raises(ValueError, match="vacía"):
        iu.get_random_choice([])


def test_get_random_int_within_range() -> None:
    for _ in range(50):
        assert 1 <= iu.get_random_int(1, 6) <= 6


def test_get_random_int_inclusive_bounds() -> None:
    seen = {iu.get_random_int(0, 1) for _ in range(100)}
    assert seen == {0, 1}


def test_get_random_int_single_value() -> None:
    assert iu.get_random_int(7, 7) == 7


def test_get_random_int_invalid_range() -> None:
    with pytest.raises(ValueError, match="mínimo"):
        iu.get_random_int(10, 4)


def test_get_uuid_is_version_4() -> None:
    assert iu.get_uuid().version == 4


def test_get_uuid_is_valid_canonical() -> None:
    from acodo.utils import valid_uuid

    assert valid_uuid(str(iu.get_uuid()))


def test_get_uuid_is_unique() -> None:
    assert iu.get_uuid() != iu.get_uuid()


def test_get_random_password_passes_validation() -> None:
    from acodo.utils import valid_password

    for _ in range(50):
        password = iu.get_random_password()
        assert valid_password(password, (8, 16))


def test_get_random_password_length_range() -> None:
    password = iu.get_random_password((12, 12))
    assert len(password) == 12


def test_get_random_password_only_digits() -> None:
    password = iu.get_random_password((10, 10), only_digits=True)
    assert password.isdigit()


def test_get_random_password_special_and_no_upper() -> None:
    password = iu.get_random_password(
        (20, 20), special_characters="#@", allow_uppercase=False
    )
    assert set(password) <= set("abcdefghijklmnñopqrstuvwxyz0123456789#@")


def test_get_random_password_invalid_args() -> None:
    with pytest.raises(ValueError, match="incoherente"):
        iu.get_random_password((10, 4))
    with pytest.raises(ValueError, match="ambiguos"):
        iu.get_random_password(only_digits=True, special_characters="#")


def test_get_random_token_url_safe() -> None:
    token = iu.get_random_token()
    assert len(token) >= 40
    assert all(char.isalnum() or char in "-_" for char in token)


def test_get_random_token_hex() -> None:
    token = iu.get_random_token(16, url_safe=False)
    assert len(token) == 32
    assert all(char in "0123456789abcdef" for char in token)


def test_get_random_token_unique() -> None:
    assert iu.get_random_token() != iu.get_random_token()


def test_get_random_token_invalid_nbytes() -> None:
    with pytest.raises(ValueError, match="nbytes"):
        iu.get_random_token(0)
    with pytest.raises(ValueError, match="nbytes"):
        iu.get_random_token(-5)
    with pytest.raises(ValueError, match="nbytes"):
        iu.get_random_token(True)


def test_get_config_dir_linux(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert iu.get_config_dir("miapp") == tmp_path / "miapp"


def test_get_config_dir_linux_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
    assert iu.get_config_dir("miapp") == tmp_path / ".config" / "miapp"


def test_get_config_dir_macos(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
    expected = tmp_path / "Library" / "Application Support" / "miapp"
    assert iu.get_config_dir("miapp") == expected


def test_get_config_dir_windows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert iu.get_config_dir("miapp") == tmp_path / "miapp"


def test_get_config_dir_windows_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
    assert iu.get_config_dir("miapp") == tmp_path / "AppData" / "Roaming" / "miapp"


@pytest.mark.parametrize("app_name", ["", "bad/name", "bad?"])
def test_get_config_dir_rejects_invalid_name(app_name: str) -> None:
    with pytest.raises(ValueError, match="no válido"):
        iu.get_config_dir(app_name)
