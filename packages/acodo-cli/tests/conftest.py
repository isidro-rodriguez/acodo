from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.commands_service import console, err_console
from acodo_cli.config import default_acodo_toml


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
def bare_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Directorio vacío, sin `acodo.toml`, que pasa a ser el actual."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def project(bare_dir: Path) -> Path:
    """Proyecto mínimo con el `acodo.toml` por defecto, que pasa a ser el actual."""
    (bare_dir / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nrequires-python = ">=3.13"\n', encoding="utf-8"
    )
    (bare_dir / "acodo.toml").write_text(default_acodo_toml(), encoding="utf-8")
    package = bare_dir / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('"""Paquete."""\n', encoding="utf-8")
    (package / "main.py").write_text("x = 1\n", encoding="utf-8")
    return bare_dir
