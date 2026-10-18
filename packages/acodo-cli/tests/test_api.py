from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands import api


class FakeRun:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.code = 0

    def __call__(self, command: list[str], cwd: Path) -> int:
        self.calls.append(tuple(command))
        return self.code


@pytest.fixture
def fake_run(project: Path, monkeypatch: pytest.MonkeyPatch) -> FakeRun:
    fake = FakeRun()
    monkeypatch.setattr(api, "run", fake)
    monkeypatch.setattr(api.shutil, "which", lambda _name: "uv")
    return fake


def test_defaults_to_the_discovered_package(
    fake_run: FakeRun, project: Path, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["api"])

    assert result.exit_code == 0
    (command,) = fake_run.calls
    assert command[-1] == str(project.resolve() / "src" / "pkg")
    assert command[:7] == ("uv", "run", "--with", "pdoc", "pdoc", "-d", "google")
    assert "-o" not in command


def test_accepts_custom_path_and_output(
    fake_run: FakeRun, project: Path, runner: CliRunner
) -> None:
    module = project / "mod.py"
    module.write_text("")
    output = project / "docs"

    result = runner.invoke(app, ["api", "-p", str(module), "-o", str(output)])

    assert result.exit_code == 0
    (command,) = fake_run.calls
    assert command[-1] == str(module.resolve())
    assert command[command.index("-o") + 1] == str(output.resolve())


def test_propagates_pdoc_failure(
    fake_run: FakeRun, project: Path, runner: CliRunner
) -> None:
    fake_run.code = 3

    result = runner.invoke(app, ["api"])

    assert result.exit_code == 3


def test_requires_uv(
    fake_run: FakeRun, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(api.shutil, "which", lambda _name: None)

    result = runner.invoke(app, ["api"])

    assert result.exit_code == 1
    assert fake_run.calls == []
    assert "uv" in result.output


def test_rejects_missing_path(fake_run: FakeRun, runner: CliRunner) -> None:
    result = runner.invoke(app, ["api", "-p", "no_existe"])

    assert result.exit_code == 2
