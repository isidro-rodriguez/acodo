from pathlib import Path

from typer.testing import CliRunner

from acodo_cli.cli import app


def make_artifacts(project: Path) -> list[Path]:
    paths = [
        project / "src" / "pkg" / "__pycache__",
        project / ".ruff_cache",
        project / ".pytest_cache",
        project / "build",
        project / "dist",
        project / "htmlcov",
        project / ".coverage",
    ]
    for path in paths:
        if path.name == ".coverage":
            path.write_text("")
        else:
            path.mkdir(parents=True)
            (path / "x").write_text("")
    return paths


def test_removes_caches_and_artifacts(project: Path, runner: CliRunner) -> None:
    artifacts = make_artifacts(project)
    venv_cache = project / ".venv" / "lib" / "__pycache__"
    venv_cache.mkdir(parents=True)

    result = runner.invoke(app, ["clean"])

    assert result.exit_code == 0
    assert not any(path.exists() for path in artifacts)
    assert venv_cache.exists()  # `.venv` nunca se toca
    assert (project / "src" / "pkg" / "main.py").exists()
    assert "7 elementos eliminados" in result.output


def test_dry_run_keeps_everything(project: Path, runner: CliRunner) -> None:
    artifacts = make_artifacts(project)

    result = runner.invoke(app, ["clean", "--dry-run"])

    assert result.exit_code == 0
    assert all(path.exists() for path in artifacts)
    assert "Se eliminaría" in result.output
    assert "7 elementos se eliminarían" in result.output


def test_nothing_to_clean(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["clean"])

    assert result.exit_code == 0
    assert "Nada que limpiar" in result.output
