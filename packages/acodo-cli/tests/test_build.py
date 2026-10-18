import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands import build


@pytest.fixture
def fake_build(project: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Proyecto con PyInstaller simulado: crea en `--distpath` lo que generaría."""

    def fake_run(cmd: list[str]) -> None:
        prefix = "--distpath="
        dist = Path(next(a[len(prefix) :] for a in cmd if a.startswith(prefix)))
        executable = build._get_executable_name("pkg")
        if "--onefile" in cmd:
            dist.mkdir(parents=True, exist_ok=True)
            (dist / executable).write_text("binario")
        else:
            (dist / "pkg" / "_internal").mkdir(parents=True, exist_ok=True)
            (dist / "pkg" / executable).write_text("binario")

    monkeypatch.setattr(build, "_run_pyinstaller", fake_run)
    return project


def test_run_pyinstaller_reports_failure(capsys: pytest.CaptureFixture[str]) -> None:
    import typer

    with pytest.raises(typer.Exit):
        build._run_pyinstaller([sys.executable, "-c", "raise SystemExit(3)"])

    assert "código 3" in capsys.readouterr().err


def test_default_build_creates_folder_with_executable(
    fake_build: Path, runner: CliRunner
) -> None:
    output = fake_build / "out"

    result = runner.invoke(app, ["build", "-o", str(output), "--no-icon"])

    assert result.exit_code == 0
    assert (output / "pkg" / build._get_executable_name("pkg")).is_file()


def test_default_output_is_build_in_project_root(
    fake_build: Path, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["build", "--no-icon"])

    assert result.exit_code == 0
    assert (fake_build / "build" / "pkg" / build._get_executable_name("pkg")).is_file()


def test_rebuild_replaces_previous_folder(fake_build: Path, runner: CliRunner) -> None:
    args = ["build", "-o", str(fake_build / "out"), "--no-icon"]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == 0
    assert second.exit_code == 0


def test_onefile_build_creates_single_file(fake_build: Path, runner: CliRunner) -> None:
    output = fake_build / "out"

    result = runner.invoke(app, ["build", "-o", str(output), "--no-icon", "--onefile"])

    assert result.exit_code == 0
    assert (output / build._get_executable_name("pkg")).is_file()


def test_missing_icon_fails_unless_no_icon(fake_build: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["build", "-o", str(fake_build / "out")])

    assert result.exit_code == 1
    assert "icono" in result.output


def test_missing_entry_point_fails(fake_build: Path, runner: CliRunner) -> None:
    (fake_build / "src" / "pkg" / "main.py").unlink()

    result = runner.invoke(app, ["build", "--no-icon"])

    assert result.exit_code == 1
    assert "punto de entrada" in result.output
