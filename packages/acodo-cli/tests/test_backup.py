import tarfile
import zipfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands.backup import archiver_for
from acodo_cli.models import Archiver

EXPECTED = {
    "acodo.toml",
    "pyproject.toml",
    "src/pkg/__init__.py",
    "src/pkg/main.py",
    "src/pkg/mod.py",
}


def write_acodo_toml(directory: Path, content: str) -> Path:
    path = directory / "acodo.toml"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def backup_project(project: Path) -> Path:
    cache = project / "src" / "pkg" / "__pycache__"
    cache.mkdir()
    (project / "src" / "pkg" / "mod.py").write_bytes(b"x = 1\n")
    (cache / "mod.pyc").write_bytes(b"\x00")
    (project / "ignored.txt").write_bytes(b"no se incluye\n")
    return project


def test_archiver_is_deduced_from_the_extension() -> None:
    assert archiver_for(Path("a.zip")) is Archiver.ZIP
    assert archiver_for(Path("a.tar.gz")) is Archiver.TAR_GZ


def test_default_is_zip_in_local(backup_project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 0
    with zipfile.ZipFile(backup_project / ".local" / "backup.zip") as zf:
        assert set(zf.namelist()) == EXPECTED


def test_tar_gz_target(backup_project: Path, runner: CliRunner) -> None:
    write_acodo_toml(
        backup_project,
        '[all]\ninclude = ["src/"]\n[backup]\ntarget = "out/copia.tar.gz"\n',
    )

    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 0
    with tarfile.open(backup_project / "out" / "copia.tar.gz") as tf:
        assert set(tf.getnames()) == EXPECTED


def test_unknown_extension_is_rejected(backup_project: Path, runner: CliRunner) -> None:
    write_acodo_toml(backup_project, '[backup]\ntarget = "copia.rar"\n')

    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 1
    assert ".tar.gz" in result.output


def test_version_suffix_is_added_to_the_name(
    backup_project: Path, runner: CliRunner
) -> None:
    (backup_project / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.2.0"\n', encoding="utf-8"
    )
    write_acodo_toml(
        backup_project, '[backup]\ntarget = "b.tar.gz"\nversion_suffix = true\n'
    )

    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 0
    assert (backup_project / "b-1.2.0.tar.gz").is_file()


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
    existing = backup_project / "src" / "pkg" / "datos.zip"
    existing.write_bytes(b"original")
    write_acodo_toml(
        backup_project,
        '[all]\ninclude = ["src/"]\n[backup]\ntarget = "src/pkg/datos.zip"\n',
    )

    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 1
    assert existing.read_bytes() == b"original"


def test_section_include_and_exclude(project: Path, runner: CliRunner) -> None:
    (project / "lib").mkdir()
    (project / "lib" / "a.py").write_bytes(b"x = 1\n")
    (project / "lib" / "secreto.py").write_bytes(b"x = 2\n")
    write_acodo_toml(
        project,
        '[all]\ninclude = ["src/"]\n[backup]\ninclude = ["lib/"]\n'
        'exclude = ["secreto.py"]\n',
    )

    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 0
    with zipfile.ZipFile(project / ".local" / "backup.zip") as zf:
        assert "lib/a.py" in zf.namelist()
        assert "lib/secreto.py" not in zf.namelist()
