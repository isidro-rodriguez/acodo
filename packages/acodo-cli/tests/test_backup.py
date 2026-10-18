import tarfile
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app

EXPECTED = {
    "pyproject.toml",
    "src/pkg/__init__.py",
    "src/pkg/main.py",
    "src/pkg/mod.py",
}


@pytest.fixture
def backup_project(project: Path) -> Path:
    cache = project / "src" / "pkg" / "__pycache__"
    cache.mkdir()
    (project / "src" / "pkg" / "mod.py").write_bytes(b"x = 1\n")
    (cache / "mod.pyc").write_bytes(b"\x00")
    (project / "ignored.txt").write_bytes(b"no se incluye\n")
    return project


def test_default_is_zip_in_local(backup_project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 0
    with zipfile.ZipFile(backup_project / ".local" / "backup.zip") as zf:
        assert set(zf.namelist()) == EXPECTED


def test_tar_gz_with_custom_file(backup_project: Path, runner: CliRunner) -> None:
    output = backup_project / "out" / "copia.tar.gz"

    result = runner.invoke(app, ["backup", "-a", "tar.gz", "-f", str(output)])

    assert result.exit_code == 0
    with tarfile.open(output) as tf:
        assert set(tf.getnames()) == EXPECTED


def test_invalid_archiver_is_rejected(backup_project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["backup", "-a", "rar"])

    assert result.exit_code == 2


def test_removes_pycache_dirs(backup_project: Path, runner: CliRunner) -> None:
    runner.invoke(app, ["backup"])

    assert not (backup_project / "src" / "pkg" / "__pycache__").exists()


def test_rerun_replaces_previous_archive(
    backup_project: Path, runner: CliRunner
) -> None:
    runner.invoke(app, ["backup"])
    (backup_project / "src" / "pkg" / "mod.py").write_bytes(b"x = 2\n")

    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 0
    with zipfile.ZipFile(backup_project / ".local" / "backup.zip") as zf:
        assert zf.read("src/pkg/mod.py") == b"x = 2\n"


def test_output_cannot_overwrite_project_file(
    backup_project: Path, runner: CliRunner
) -> None:
    original = (backup_project / "pyproject.toml").read_bytes()

    result = runner.invoke(
        app, ["backup", "-f", str(backup_project / "pyproject.toml")]
    )

    assert result.exit_code == 1
    assert (backup_project / "pyproject.toml").read_bytes() == original


def test_honors_custom_src_dir(project: Path, runner: CliRunner) -> None:
    (project / "pyproject.toml").write_text(
        '[tool.acodo-cli]\nsrc-dir = "lib"\n', encoding="utf-8"
    )
    (project / "lib").mkdir()
    (project / "lib" / "a.py").write_bytes(b"x = 1\n")

    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 0
    with zipfile.ZipFile(project / ".local" / "backup.zip") as zf:
        assert "lib/a.py" in zf.namelist()
