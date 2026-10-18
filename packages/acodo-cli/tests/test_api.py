from pathlib import Path

from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands.api import render_module

SOURCE = '''"""Módulo de ejemplo."""


def public(a: int, *, b: str = "x") -> bool:
    """Hace algo público."""
    return True


def undocumented() -> None:
    pass


def _private() -> None:
    """Privada: no aparece."""


class Shape(Base):
    """Una figura."""

    def area(self) -> float:
        """Calcula el área."""
        return 0.0

    def _hidden(self) -> None:
        """No aparece."""
'''


def write_acodo_toml(directory: Path, content: str) -> Path:
    path = directory / "acodo.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_render_module_documents_public_items_with_docstring() -> None:
    text = render_module(SOURCE, "pkg/mod.py")

    assert "## `pkg/mod.py`" in text
    assert "Módulo de ejemplo." in text
    assert "def public(a: int, *, b: str='x') -> bool" in text
    assert "class Shape(Base)" in text
    assert "def area(self) -> float" in text
    assert "undocumented" not in text
    assert "_private" not in text
    assert "_hidden" not in text


def test_render_module_is_empty_without_docs_or_on_syntax_error() -> None:
    assert render_module("x = 1\n", "a.py") == ""
    assert render_module("def f(:\n", "a.py") == ""


def test_command_writes_the_target(project: Path, runner: CliRunner) -> None:
    (project / "src" / "pkg" / "mod.py").write_text(SOURCE, encoding="utf-8")

    result = runner.invoke(app, ["api"])

    assert result.exit_code == 0
    text = (project / ".local" / "api.md").read_text(encoding="utf-8")
    assert text.startswith("# API de demo")
    assert "src/pkg/mod.py" in text
    assert "src/pkg/__init__.py" in text  # Su docstring de módulo es público.
    assert "main.py" not in text  # Sin docstring: no hay nada que documentar.


def test_command_adds_the_version_to_the_file_name(
    project: Path, runner: CliRunner
) -> None:
    (project / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.2.0"\n', encoding="utf-8"
    )

    result = runner.invoke(app, ["api"])

    assert result.exit_code == 0
    assert (project / ".local" / "api-1.2.0.md").is_file()


def test_command_honors_section_exclude(project: Path, runner: CliRunner) -> None:
    (project / "src" / "pkg" / "mod.py").write_text(SOURCE, encoding="utf-8")
    write_acodo_toml(
        project, '[all]\ninclude = ["src/"]\n[api]\nexclude = ["__init__.py"]\n'
    )

    runner.invoke(app, ["api"])

    generated = (project / ".local" / "api.md").read_text(encoding="utf-8")
    assert "mod.py" in generated
    assert "__init__.py" not in generated


def test_unsupported_format_fails(project: Path, runner: CliRunner) -> None:
    write_acodo_toml(project, '[api]\ntarget = "api.html"\n')

    result = runner.invoke(app, ["api"])

    assert result.exit_code == 1
    assert ".md" in result.output


def test_nothing_to_document_fails(project: Path, runner: CliRunner) -> None:
    (project / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")

    result = runner.invoke(app, ["api"])

    assert result.exit_code == 1
    assert "nada que documentar" in result.output
