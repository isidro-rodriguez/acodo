import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands import init
from acodo_cli.config import default_acodo_toml, load_config


def test_init_creates_everything(bare_dir: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert (bare_dir / "acodo.toml").read_text("utf-8") == default_acodo_toml()
    template = json.loads((bare_dir / ".local" / "gh_app.json").read_text("utf-8"))
    assert template["repository"] == "owner/repo"
    assert ".local/" in (bare_dir / ".gitignore").read_text("utf-8").splitlines()
    assert load_config(bare_dir).scopes["all"].include == ("scripts/", "src/", "tests/")


def test_init_keeps_existing_gitignore_content(
    bare_dir: Path, runner: CliRunner
) -> None:
    (bare_dir / ".gitignore").write_text(".venv/", encoding="utf-8")

    runner.invoke(app, ["init"])

    lines = (bare_dir / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines == [".venv/", ".local/"]


def test_init_never_overwrites_the_gh_template(
    bare_dir: Path, runner: CliRunner
) -> None:
    gh_config = bare_dir / ".local" / "gh_app.json"
    gh_config.parent.mkdir()
    gh_config.write_text('{"repository": "mio/mio"}', encoding="utf-8")

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert gh_config.read_text(encoding="utf-8") == '{"repository": "mio/mio"}'
    assert "ya existe" in result.output


def test_init_in_an_initialized_project_changes_nothing(
    project: Path, runner: CliRunner
) -> None:
    before = (project / "acodo.toml").read_text(encoding="utf-8")

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "ya está inicializado" in result.output
    assert (project / "acodo.toml").read_text(encoding="utf-8") == before
    assert not (project / ".local").exists()
    assert not (project / ".gitignore").exists()


class FakeClone:
    """Sustituto de `run`: registra el comando de `git clone` y simula su código."""

    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.code = 0

    def __call__(self, command: list[str], cwd: Path) -> int:
        self.commands.append(command)
        return self.code


@pytest.fixture
def outside_project(
    bare_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, FakeClone]:
    fake = FakeClone()
    monkeypatch.setattr(init, "is_global_install", lambda prefix, base_prefix: True)
    monkeypatch.setattr(init.shutil, "which", lambda name: "git")
    monkeypatch.setattr(init, "run", fake)
    return bare_dir, fake


def test_outside_a_project_offers_to_clone_the_template(
    outside_project: tuple[Path, FakeClone], runner: CliRunner
) -> None:
    bare_dir, fake = outside_project

    result = runner.invoke(app, ["init"], input="y\n\n")

    assert result.exit_code == 0
    assert fake.commands == [
        ["git", "clone", "--depth", "1", init.TEMPLATE_URL, "acodo"]
    ]
    assert "Plantilla clonada en acodo" in result.output
    assert not (bare_dir / "acodo.toml").exists()


def test_clone_uses_the_given_path(
    outside_project: tuple[Path, FakeClone], runner: CliRunner
) -> None:
    _, fake = outside_project

    runner.invoke(app, ["init"], input="y\nmi_proyecto\n")

    assert fake.commands[0][-1] == "mi_proyecto"


def test_declining_does_not_clone(
    outside_project: tuple[Path, FakeClone], runner: CliRunner
) -> None:
    _, fake = outside_project

    result = runner.invoke(app, ["init"], input="n\n")

    assert result.exit_code == 0
    assert fake.commands == []


def test_clone_refuses_a_non_empty_target(
    outside_project: tuple[Path, FakeClone], runner: CliRunner
) -> None:
    bare_dir, fake = outside_project
    (bare_dir / "acodo").mkdir()
    (bare_dir / "acodo" / "x.txt").write_text("")

    result = runner.invoke(app, ["init"], input="y\n\n")

    assert result.exit_code == 1
    assert "no está vacía" in result.output
    assert fake.commands == []


def test_clone_requires_git(
    outside_project: tuple[Path, FakeClone],
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(init.shutil, "which", lambda name: None)

    result = runner.invoke(app, ["init"], input="y\n\n")

    assert result.exit_code == 1
    assert "git" in result.output


def test_clone_failure_exits_with_one(
    outside_project: tuple[Path, FakeClone], runner: CliRunner
) -> None:
    _, fake = outside_project
    fake.code = 128

    result = runner.invoke(app, ["init"], input="y\n\n")

    assert result.exit_code == 1
    assert "No se pudo clonar" in result.output
