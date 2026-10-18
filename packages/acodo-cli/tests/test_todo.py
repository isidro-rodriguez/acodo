from pathlib import Path

from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands.todo import find_markers


def write_acodo_toml(directory: Path, content: str) -> Path:
    path = directory / "acodo.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_find_markers_only_in_comments(tmp_path: Path) -> None:
    path = tmp_path / "m.py"
    path.write_text(
        'x = "TODO: en una cadena, no cuenta"\n'
        "# TODO: documentar\n"
        "y = 1  # FIXME(ana): corregir\n"
        "# comentario normal\n",
        encoding="utf-8",
    )

    assert find_markers(path) == [
        (2, "TODO", "documentar"),
        (3, "FIXME", "ana): corregir"),
    ]


def test_find_markers_ignores_broken_files(tmp_path: Path) -> None:
    path = tmp_path / "roto.py"
    path.write_text('x = """sin cerrar\n', encoding="utf-8")

    assert find_markers(path) == []


def test_command_lists_markers(project: Path, runner: CliRunner) -> None:
    (project / "src" / "pkg" / "main.py").write_text(
        "# TODO: añadir validación\nx = 1\n", encoding="utf-8"
    )

    result = runner.invoke(app, ["todo"])

    assert result.exit_code == 0
    assert "src/pkg/main.py:1" in result.output
    assert "añadir validación" in result.output


def test_marker_without_context_fails(project: Path, runner: CliRunner) -> None:
    (project / "src" / "pkg" / "main.py").write_text(
        "# TODO\nx = 1\n", encoding="utf-8"
    )

    result = runner.invoke(app, ["todo"])

    assert result.exit_code == 1
    assert "sin contexto" in result.output


def test_clean_project_reports_nothing(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["todo"])

    assert result.exit_code == 0
    assert "Sin marcadores" in result.output


def test_section_exclude_skips_files(project: Path, runner: CliRunner) -> None:
    (project / "src" / "pkg" / "main.py").write_text("# TODO\n", encoding="utf-8")
    write_acodo_toml(
        project, '[all]\ninclude = ["src/"]\n[todo]\nexclude = ["main.py"]\n'
    )

    result = runner.invoke(app, ["todo"])

    assert result.exit_code == 0
    assert "Sin marcadores" in result.output
