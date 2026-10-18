from collections.abc import Sequence
from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands import check

ALL_STEPS = [
    ("ruff", "format"),
    ("ruff", "check", "--fix"),
    ("ty", "check"),
    ("pytest",),
]


class FakeRun:
    """Sustituto de `run`: registra los comandos y simula sus códigos."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.cwds: list[Path] = []
        self.codes: dict[tuple[str, ...], int] = {}

    def __call__(self, command: Sequence[str], cwd: Path) -> int:
        cmd = tuple(command)
        self.calls.append(cmd)
        self.cwds.append(cwd)
        return self.codes.get(cmd[2:], 0)

    @property
    def steps(self) -> list[tuple[str, ...]]:
        """Comandos de calidad ejecutados, sin `python -m`."""
        return [cmd[2:] for cmd in self.calls]


@pytest.fixture
def fake_run(project: Path, monkeypatch: pytest.MonkeyPatch) -> FakeRun:
    fake = FakeRun()
    monkeypatch.setattr(check, "run", fake)
    return fake


def test_runs_every_step_by_default_in_project_root(
    fake_run: FakeRun, project: Path, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["check"])

    assert result.exit_code == 0
    assert fake_run.steps == ALL_STEPS
    assert set(fake_run.cwds) == {project.resolve()}


def test_flags_select_steps_in_fixed_order(
    fake_run: FakeRun, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["check", "--types", "--lint"])

    assert result.exit_code == 0
    assert fake_run.steps == [("ruff", "check", "--fix"), ("ty", "check")]


def test_fails_but_still_runs_remaining_steps(
    fake_run: FakeRun, runner: CliRunner
) -> None:
    fake_run.codes[("ruff", "check", "--fix")] = 1

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 1
    assert fake_run.steps == ALL_STEPS
    assert "código 1" in result.output


def test_summary_is_printed_on_success(fake_run: FakeRun, runner: CliRunner) -> None:
    result = runner.invoke(app, ["check", "--format"])

    assert "Resultado" in result.output
    assert "ruff format" in result.output


def test_ci_only_verifies(fake_run: FakeRun, runner: CliRunner) -> None:
    result = runner.invoke(app, ["check", "--ci", "--format", "--lint"])

    assert result.exit_code == 0
    assert fake_run.steps == [("ruff", "format", "--check"), ("ruff", "check")]


def test_cov_measures_the_source_dir(fake_run: FakeRun, runner: CliRunner) -> None:
    result = runner.invoke(app, ["check", "--tests", "--cov"])

    assert result.exit_code == 0
    assert fake_run.steps == [("pytest", "--cov=src", "--cov-report=term-missing")]
