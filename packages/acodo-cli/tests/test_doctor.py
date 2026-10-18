from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands import doctor


def make_dirs(project: Path) -> None:
    for name in ("scripts", "tests"):
        (project / name).mkdir()


@pytest.fixture
def all_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor, "_has_module", lambda name: True)


@pytest.mark.parametrize(
    ("version", "spec", "expected"),
    [
        ((3, 13, 1), ">=3.13", True),
        ((3, 12, 4), ">=3.13", False),
        ((3, 14, 0), ">=3.12,<3.15", True),
        ((3, 15, 0), ">=3.12,<3.15", False),
        ((3, 13, 2), "==3.13", True),
        ((3, 12, 0), "!=3.12", False),
        ((3, 13, 0), "3.13", None),
        ((3, 13, 0), ">=abc", None),
    ],
)
def test_satisfies(version: tuple[int, ...], spec: str, expected: bool | None) -> None:
    assert doctor.satisfies(version, spec) is expected


def test_everything_ready(project: Path, all_tools: None, runner: CliRunner) -> None:
    make_dirs(project)
    (project / ".gitignore").write_text(".local/\n", encoding="utf-8")

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "✗" not in result.output
    assert "Diagnóstico de demo" in result.output


def test_missing_required_module_fails(
    project: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    monkeypatch.setattr(doctor, "_has_module", lambda name: name != "ty")
    make_dirs(project)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "uv add --dev ty" in result.output


def test_missing_include_dir_fails(
    project: Path, all_tools: None, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "No existe tests" in result.output
    assert "No existe scripts" in result.output


def test_optional_problems_only_warn(
    project: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    monkeypatch.setattr(
        doctor, "_has_module", lambda name: name in {"ruff", "ty", "pytest"}
    )
    make_dirs(project)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "aviso" in result.output


def test_unreadable_requires_python_fails(
    project: Path, all_tools: None, runner: CliRunner
) -> None:
    make_dirs(project)
    (project / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nrequires-python = "3.13"\n', encoding="utf-8"
    )

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "No se entiende" in result.output


def test_missing_requires_python_only_warns(
    project: Path, all_tools: None, runner: CliRunner
) -> None:
    make_dirs(project)
    (project / "pyproject.toml").write_text('[project]\nname = "demo"\n', "utf-8")

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Sin requires-python" in result.output
