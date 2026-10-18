from collections.abc import Sequence
from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands import check


def write_acodo_toml(directory: Path, content: str) -> Path:
    path = directory / "acodo.toml"
    path.write_text(content, encoding="utf-8")
    return path


def tool(command: Sequence[str]) -> str:
    """Nombre de la herramienta de un comando `python -m <tool> ...`."""
    name, *rest = command[2:]
    return f"{name} {rest[0]}" if name in {"ruff", "ty"} else name


class FakeRun:
    """Sustituto de `run`: registra los comandos y simula sus códigos."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.cwds: list[Path] = []
        self.codes: dict[str, int] = {}

    def __call__(self, command: Sequence[str], cwd: Path) -> int:
        self.calls.append(tuple(command))
        self.cwds.append(cwd)
        return self.codes.get(tool(command), 0)

    @property
    def tools(self) -> list[str]:
        """Herramientas ejecutadas, en orden."""
        return [tool(command) for command in self.calls]

    def args(self, name: str) -> tuple[str, ...]:
        """Argumentos (sin `python -m`) del comando de la herramienta `name`."""
        return next(cmd[2:] for cmd in self.calls if tool(cmd) == name)


@pytest.fixture
def fake_run(project: Path, monkeypatch: pytest.MonkeyPatch) -> FakeRun:
    fake = FakeRun()
    monkeypatch.setattr(check, "run", fake)
    return fake


def test_check_runs_every_step_in_project_root(
    fake_run: FakeRun, project: Path, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["check"])

    assert result.exit_code == 0
    assert fake_run.tools == ["ruff format", "ruff check", "ty check", "pytest"]
    assert set(fake_run.cwds) == {project.resolve()}


def test_each_command_runs_only_its_step(fake_run: FakeRun, runner: CliRunner) -> None:
    for command, expected in [
        ("format", "ruff format"),
        ("lint", "ruff check"),
        ("types", "ty check"),
        ("tests", "pytest"),
        ("tests-cov", "pytest"),
    ]:
        fake_run.calls.clear()

        result = runner.invoke(app, [command])

        assert result.exit_code == 0
        assert fake_run.tools == [expected]


def test_steps_receive_the_scope_paths_and_excludes(
    fake_run: FakeRun, runner: CliRunner
) -> None:
    runner.invoke(app, ["check"])

    assert fake_run.args("ruff format")[:3] == ("ruff", "format", "src")
    assert fake_run.args("ruff check")[:4] == ("ruff", "check", "--fix", "src")
    for name in ("ruff format", "ruff check"):
        assert next(
            pair
            for pair in zip(fake_run.args(name), fake_run.args(name)[1:], strict=False)
            if pair[0] == "--extend-exclude" and pair[1] == ".venv"
        ) == ("--extend-exclude", ".venv")
    assert fake_run.args("ty check")[:3] == ("ty", "check", "src")
    assert "--exclude" in fake_run.args("ty check")
    assert "--ignore-glob=*/.venv/*" in fake_run.args("pytest")


def test_trailing_slash_is_removed_from_excludes(
    fake_run: FakeRun, runner: CliRunner
) -> None:
    runner.invoke(app, ["types"])

    args = fake_run.args("ty check")
    assert ".cache" in args
    assert ".cache/" not in args


def test_section_include_adds_to_all(
    fake_run: FakeRun, project: Path, runner: CliRunner
) -> None:
    (project / "scripts").mkdir()
    write_acodo_toml(
        project, '[all]\ninclude = ["src/"]\n[lint]\ninclude = ["scripts/"]\n'
    )

    runner.invoke(app, ["lint"])

    assert fake_run.args("ruff check")[3:5] == ("src", "scripts")


def test_tests_cov_measures_coverage(fake_run: FakeRun, runner: CliRunner) -> None:
    runner.invoke(app, ["tests-cov"])

    assert fake_run.args("pytest")[-2:] == ("--cov", "--cov-report=term-missing")


def test_fails_but_still_runs_remaining_steps(
    fake_run: FakeRun, runner: CliRunner
) -> None:
    fake_run.codes["ruff check"] = 1

    result = runner.invoke(app, ["check"])

    assert result.exit_code == 1
    assert fake_run.tools == ["ruff format", "ruff check", "ty check", "pytest"]
    assert "código 1" in result.output


def test_summary_is_printed_on_success(fake_run: FakeRun, runner: CliRunner) -> None:
    result = runner.invoke(app, ["format"])

    assert "Resultado" in result.output
    assert "ruff format" in result.output


def test_fails_without_paths(
    fake_run: FakeRun, project: Path, runner: CliRunner
) -> None:
    write_acodo_toml(project, '[all]\ninclude = ["no_existe/"]\n')

    result = runner.invoke(app, ["lint"])

    assert result.exit_code == 1
    assert "No hay rutas que procesar" in result.output
    assert fake_run.calls == []
