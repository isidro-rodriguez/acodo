import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands import gh_token

VALID_CONFIG = {
    "repository": "https://github.com/owner/repo.git",
    "app-id": "123456",
    "private-key": "private-key.pem",
    "installation-id": "12345678",
}


@pytest.fixture
def config_file(project: Path) -> Path:
    path = project / ".local" / "gh_app.json"
    path.parent.mkdir()
    path.write_text(json.dumps(VALID_CONFIG), encoding="utf-8")
    return path


@pytest.fixture
def fake_token(monkeypatch: pytest.MonkeyPatch) -> None:
    def generate(cfg: dict[str, Any], config_path: Path) -> dict[str, Any]:
        return {"token": "ghs_abc", "expires_at": "2030-01-01T00:00:00Z"}

    monkeypatch.setattr(gh_token, "generate_token", generate)


# ---------------------------------------------------------------------------
#  Comando
# ---------------------------------------------------------------------------


def test_missing_default_config_shows_template(
    project: Path, runner: CliRunner
) -> None:
    result = runner.invoke(app, ["gh-token"])

    assert result.exit_code == 1
    # Rich parte las líneas largas (rutas de tmp), así que no se busca la ruta.
    assert "No se encontró el fichero de configuración" in result.output
    assert "installation-id" in result.output


@pytest.mark.usefixtures("config_file", "fake_token")
def test_only_token_prints_just_the_token(runner: CliRunner) -> None:
    result = runner.invoke(app, ["gh-token", "--only-token", "--no-clipboard"])

    assert result.exit_code == 0
    assert result.output.strip() == "ghs_abc"


@pytest.mark.usefixtures("config_file", "fake_token")
def test_full_output_includes_normalized_repository(runner: CliRunner) -> None:
    result = runner.invoke(app, ["gh-token", "--no-clipboard"])

    assert result.exit_code == 0
    assert '"repository": "owner/repo"' in result.output
    assert '"token": "ghs_abc"' in result.output


@pytest.mark.usefixtures("config_file", "fake_token")
def test_no_print_hides_the_output(runner: CliRunner) -> None:
    result = runner.invoke(app, ["gh-token", "--no-print", "--no-clipboard"])

    assert result.exit_code == 0
    assert "ghs_abc" not in result.output


@pytest.mark.usefixtures("config_file", "fake_token")
def test_clipboard_failure_is_only_a_warning(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(text: str) -> None:
        raise RuntimeError("sin portapapeles")

    monkeypatch.setattr(gh_token, "_copy_to_clipboard", broken)

    result = runner.invoke(app, ["gh-token", "--only-token"])

    assert result.exit_code == 0
    assert "sin portapapeles" in result.output


def test_custom_file_option(project: Path, fake_token: None, runner: CliRunner) -> None:
    other = project / "otro.json"
    other.write_text(json.dumps(VALID_CONFIG), encoding="utf-8")

    result = runner.invoke(
        app, ["gh-token", "-f", str(other), "--only-token", "--no-clipboard"]
    )

    assert result.exit_code == 0


@pytest.mark.usefixtures("config_file")
def test_generation_error_exits_with_one(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(cfg: dict[str, Any], config_path: Path) -> dict[str, Any]:
        raise ValueError("GitHub devolvió 401")

    monkeypatch.setattr(gh_token, "generate_token", broken)

    result = runner.invoke(app, ["gh-token", "--no-clipboard"])

    assert result.exit_code == 1
    assert "401" in result.output


# ---------------------------------------------------------------------------
#  Portapapeles
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("platform", "wayland", "available", "expected"),
    [
        ("darwin", False, [], ["pbcopy"]),
        ("linux", True, ["wl-copy", "xclip"], ["wl-copy"]),
        ("linux", False, ["xclip", "wl-copy"], ["xclip", "-selection", "clipboard"]),
        ("linux", False, ["xsel"], ["xsel", "--clipboard", "--input"]),
    ],
)
def test_copy_posix_picks_command(
    monkeypatch: pytest.MonkeyPatch,
    platform: str,
    wayland: bool,
    available: list[str],
    expected: list[str],
) -> None:
    captured: dict[str, object] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> None:
        captured["cmd"] = cmd
        captured["input"] = kwargs["input"]

    # Se parchean los nombres del módulo, no los módulos globales (`sys`, etc.).
    monkeypatch.setattr(gh_token, "sys", SimpleNamespace(platform=platform))
    monkeypatch.setattr(
        gh_token,
        "get_env",
        lambda name: "wayland-0" if wayland and name == "WAYLAND_DISPLAY" else None,
    )
    monkeypatch.setattr(
        gh_token,
        "shutil",
        SimpleNamespace(which=lambda name: name if name in available else None),
    )
    monkeypatch.setattr(
        gh_token,
        "subprocess",
        SimpleNamespace(
            run=fake_run,
            CalledProcessError=subprocess.CalledProcessError,
            TimeoutExpired=subprocess.TimeoutExpired,
        ),
    )

    gh_token._copy_posix("hola")

    assert captured == {"cmd": expected, "input": b"hola"}


def test_copy_posix_fails_without_clipboard_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gh_token, "sys", SimpleNamespace(platform="linux"))
    monkeypatch.setattr(gh_token, "get_env", lambda name: None)
    monkeypatch.setattr(gh_token, "shutil", SimpleNamespace(which=lambda name: None))

    with pytest.raises(RuntimeError):
        gh_token._copy_posix("hola")
