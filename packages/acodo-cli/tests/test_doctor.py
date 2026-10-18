from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands import doctor


@pytest.fixture
def all_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor, "_has_module", lambda name: True)
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/uv")


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
    (project / "tests").mkdir()
    (project / ".gitignore").write_text(".local/\n", encoding="utf-8")

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "✗" not in result.output
    assert "Diagnóstico de demo" in result.output


def test_missing_required_module_fails(
    project: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    monkeypatch.setattr(doctor, "_has_module", lambda name: name != "ty")
    (project / "tests").mkdir()

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "uv add --dev ty" in result.output


def test_missing_tests_dir_fails(
    project: Path, all_tools: None, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "No existe tests" in result.output


def test_optional_problems_only_warn(
    project: Path, monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> None:
    monkeypatch.setattr(
        doctor, "_has_module", lambda name: name in {"ruff", "ty", "pytest"}
    )
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    (project / "tests").mkdir()

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "aviso" in result.output


def test_unreadable_python_version_fails(
    project: Path, all_tools: None, runner: CliRunner
) -> None:
    (project / "tests").mkdir()
    (project / "pyproject.toml").write_text(
        '[tool.acodo-cli]\npython-version = "3.13"\n', encoding="utf-8"
    )

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "No se entiende" in result.output
