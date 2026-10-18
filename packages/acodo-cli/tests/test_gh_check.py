import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands import gh_check

VALID_CONFIG = {
    "repository": "owner/repo",
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


def patch_github(
    monkeypatch: pytest.MonkeyPatch, info: dict[str, Any]
) -> list[tuple[str, str, str | None]]:
    calls: list[tuple[str, str, str | None]] = []

    def request(
        method: str,
        url: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        calls.append((method, url, token))
        return info

    monkeypatch.setattr(gh_check, "generate_token", lambda cfg, path: {"token": "t"})
    monkeypatch.setattr(gh_check, "request", request)
    return calls


@pytest.mark.usefixtures("config_file")
def test_reports_repository_access(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = patch_github(
        monkeypatch,
        {
            "full_name": "owner/repo",
            "private": True,
            "html_url": "https://github.com/owner/repo",
            "default_branch": "main",
            "permissions": {"pull": True, "push": False},
        },
    )

    result = runner.invoke(app, ["gh-check"])

    assert result.exit_code == 0
    assert calls == [("GET", "https://api.github.com/repos/owner/repo", "t")]
    assert "owner/repo (privado)" in result.output
    assert "main" in result.output
    assert "pull=✓" in result.output
    assert "push=✗" in result.output
    assert "admin=·" in result.output


def test_missing_config_shows_template(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["gh-check"])

    assert result.exit_code == 1
    assert "installation-id" in result.output


@pytest.mark.usefixtures("config_file")
def test_api_error_exits_with_one(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*args: object, **kwargs: object) -> dict[str, Any]:
        raise ValueError("GitHub devolvió 404")

    monkeypatch.setattr(gh_check, "generate_token", lambda cfg, path: {"token": "t"})
    monkeypatch.setattr(gh_check, "request", broken)

    result = runner.invoke(app, ["gh-check"])

    assert result.exit_code == 1
    assert "404" in result.output
