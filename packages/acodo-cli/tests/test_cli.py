import subprocess
import sys
from importlib.metadata import entry_points
from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli import cli
from acodo_cli.cli import app
from acodo_cli.commands_service import is_global_install

COMMANDS = (
    "api",
    "backup",
    "build",
    "check",
    "clean",
    "code-count",
    "doctor",
    "gh-check",
    "gh-token",
    "init",
    "todo",
)


def test_help_lists_every_command(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in COMMANDS:
        assert command in result.output


def test_no_args_shows_help(runner: CliRunner) -> None:
    result = runner.invoke(app, [])

    assert "backup" in result.output


@pytest.mark.parametrize("command", COMMANDS)
def test_each_command_has_help(runner: CliRunner, command: str) -> None:
    result = runner.invoke(app, [command, "--help"])

    assert result.exit_code == 0


def test_gh_token_and_gh_check_are_independent_commands(runner: CliRunner) -> None:
    # Los antiguos subcomandos `gh-token access|test` ya no existen.
    assert runner.invoke(app, ["gh-token", "access"]).exit_code == 2
    assert runner.invoke(app, ["gh-token", "test"]).exit_code == 2


def test_python_dash_m_runs_the_cli(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "acodo_cli", "--help"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )

    assert result.returncode == 0
    assert "check" in result.stdout


def test_commands_fail_outside_a_project(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["code-count"])

    assert result.exit_code == 1
    assert "pyproject.toml" in result.output


def test_console_script_points_to_the_app() -> None:
    scripts = {ep.name: ep.value for ep in entry_points(group="console_scripts")}

    assert scripts["acodo"] == "acodo_cli.cli:app"


def test_global_install_is_rejected(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "is_global_install", lambda prefix, base_prefix: True)

    result = runner.invoke(app, ["code-count"])

    assert result.exit_code == 1
    assert "herramienta global" in result.output


def test_help_still_works_in_global_install(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "is_global_install", lambda prefix, base_prefix: True)

    assert runner.invoke(app, ["--help"]).exit_code == 0


def test_is_global_install_without_virtualenv(tmp_path: Path) -> None:
    assert is_global_install(tmp_path, tmp_path)


@pytest.mark.parametrize("marker", ["uv-receipt.toml", "pipx_metadata.json"])
def test_is_global_install_detects_tool_environments(
    tmp_path: Path, marker: str
) -> None:
    venv = tmp_path / "tool-venv"
    venv.mkdir()
    (venv / marker).write_text("")

    assert is_global_install(venv, tmp_path)


def test_is_global_install_accepts_project_virtualenv(tmp_path: Path) -> None:
    venv = tmp_path / ".venv"
    venv.mkdir()

    assert not is_global_install(venv, tmp_path)


def test_config_errors_keep_square_brackets(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.acodo-cli]\nsrc-dir = 3\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["code-count"])

    assert result.exit_code == 1
    assert "[tool.acodo-cli] «src-dir» debe ser una cadena no vacía" in result.output
