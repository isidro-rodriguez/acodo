from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.commands_service import console, err_console


@pytest.fixture(autouse=True)
def wide_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fija un ancho grande para que Rich no parta rutas ni mensajes en los tests."""
    monkeypatch.setattr(console, "width", 300)
    monkeypatch.setattr(err_console, "width", 300)


@pytest.fixture
def runner() -> CliRunner:
    """Ejecutor de comandos Typer para los tests de CLI."""
    return CliRunner()


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Proyecto mínimo en un directorio temporal, que pasa a ser el actual."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n', encoding="utf-8"
    )
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Paquete."""\n', encoding="utf-8")
    (package / "main.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path
