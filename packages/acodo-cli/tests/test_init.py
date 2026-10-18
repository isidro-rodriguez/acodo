import json
import tomllib
from pathlib import Path

from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.config import load_config


def test_init_creates_everything(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Añadida [tool.acodo-cli] a pyproject.toml" in result.output
    data = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["tool"]["acodo-cli"] == {
        "src-dir": "src",
        "test-dir": "tests",
        "python-version": ">=3.13",
    }
    assert data["project"]["name"] == "demo"
    template = json.loads((project / ".local" / "gh_app.json").read_text("utf-8"))
    assert template["repository"] == "owner/repo"
    assert ".local/" in (project / ".gitignore").read_text("utf-8").splitlines()
    assert load_config(project).src_dir == "src"


def test_init_is_idempotent_and_never_overwrites(
    project: Path, runner: CliRunner
) -> None:
    runner.invoke(app, ["init"])
    gh_config = project / ".local" / "gh_app.json"
    gh_config.write_text('{"repository": "mio/mio"}', encoding="utf-8")
    before = (project / "pyproject.toml").read_text(encoding="utf-8")
    gitignore = (project / ".gitignore").read_text(encoding="utf-8")

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert (project / "pyproject.toml").read_text(encoding="utf-8") == before
    assert gh_config.read_text(encoding="utf-8") == '{"repository": "mio/mio"}'
    assert (project / ".gitignore").read_text(encoding="utf-8") == gitignore
    assert "ya existe" in result.output


def test_init_keeps_existing_gitignore_content(
    project: Path, runner: CliRunner
) -> None:
    (project / ".gitignore").write_text(".venv/", encoding="utf-8")

    runner.invoke(app, ["init"])

    lines = (project / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines == [".venv/", ".local/"]


def test_init_respects_existing_section(project: Path, runner: CliRunner) -> None:
    content = '[tool.acodo-cli]\nsrc-dir = "lib"\n'
    (project / "pyproject.toml").write_text(content, encoding="utf-8")

    runner.invoke(app, ["init"])

    assert (project / "pyproject.toml").read_text(encoding="utf-8") == content
