"""Tests del logger (`acodo.logger`)."""

import logging
import pathlib
from collections.abc import Iterator

import pytest

from acodo.logger import Logger, get_logger


@pytest.fixture
def name(tmp_path: pathlib.Path) -> Iterator[str]:
    """Nombre de logger único por test; cierra sus handlers al terminar."""
    logger_name = f"test-{tmp_path.name}"
    yield logger_name
    logger = logging.getLogger(logger_name)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def test_get_logger_is_idempotent(name: str) -> None:
    get_logger(name)
    handlers = list(logging.getLogger(name).handlers)
    get_logger(name, debug=True)
    assert logging.getLogger(name).handlers == handlers
    assert logging.getLogger(name).level == logging.INFO


def test_get_logger_does_not_touch_root(
    name: str, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    get_logger(name, file=tmp_path / "a.log")
    logging.getLogger("tercero").warning("ruido ajeno")
    assert (list(root.handlers), root.level) == (handlers, level)
    assert capsys.readouterr().out == ""
    assert (tmp_path / "a.log").read_text(encoding="utf-8") == ""


def test_get_logger_without_file_only_has_console(name: str) -> None:
    get_logger(name)
    assert len(logging.getLogger(name).handlers) == 1


@pytest.mark.parametrize("bad_name", ["", "   "])
def test_get_logger_rejects_blank_name(bad_name: str) -> None:
    with pytest.raises(ValueError, match="nombre del logger"):
        get_logger(bad_name)


def test_get_logger_rejects_invalid_file(name: str, tmp_path: pathlib.Path) -> None:
    with pytest.raises(ValueError, match="no válido"):
        get_logger(name, file=tmp_path / "bad?.log")
    assert logging.getLogger(name).handlers == []


def test_writes_to_console_and_file(
    name: str, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "sub" / "out.log"
    get_logger(name, file=path).info("hola")
    assert capsys.readouterr().out == "hola\n"
    content = path.read_text(encoding="utf-8")
    assert "INFO" in content
    assert content.endswith("hola\n")


def test_destination_flags(
    name: str, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "out.log"
    log = get_logger(name, file=path)
    log.info("solo fichero", console=False)
    log.info("solo consola", file=False)
    assert capsys.readouterr().out == "solo consola\n"
    content = path.read_text(encoding="utf-8")
    assert "solo fichero" in content
    assert "solo consola" not in content


def test_record_without_flags_reaches_all_destinations(
    name: str, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "out.log"
    get_logger(name, file=path)
    logging.getLogger(name).info("directo")
    assert capsys.readouterr().out == "directo\n"
    assert "directo" in path.read_text(encoding="utf-8")


def test_levels(name: str, capsys: pytest.CaptureFixture[str]) -> None:
    log = get_logger(name)
    log.debug("depuración")
    log.warning("aviso")
    assert capsys.readouterr().out == "aviso\n"


def test_debug_level_and_prettified_values(
    name: str, capsys: pytest.CaptureFixture[str]
) -> None:
    log = get_logger(name, debug=True)
    log.debug("datos %(d)s y %(t)s", d={"a": 1}, t="texto")
    assert capsys.readouterr().out == "datos {'a': 1} y texto\n"


def test_interpolation_and_literal_percent(
    name: str, capsys: pytest.CaptureFixture[str]
) -> None:
    log = get_logger(name)
    log.info("procesados %(n)s", n=3)
    log.info("100% listo")
    log.info("100%% de %(n)s", n=3)
    assert capsys.readouterr().out == "procesados 3\n100% listo\n100% de 3\n"


def test_error_with_exc_info(name: str, tmp_path: pathlib.Path) -> None:
    path = tmp_path / "err.log"
    log = get_logger(name, file=path)
    try:
        raise ValueError("boom")
    except ValueError:
        log.error("fallo", exc_info=True)
    content = path.read_text(encoding="utf-8")
    assert "ERROR" in content
    assert "Traceback" in content
    assert "ValueError: boom" in content


def test_get_logger_returns_logger_wrapper(name: str) -> None:
    assert isinstance(get_logger(name), Logger)
