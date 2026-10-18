"""Copia de seguridad manual.

Limpia cachés `__pycache__` y comprime el código fuente en
`.local/backup.<extensión>` (zip por defecto; también tar.gz).

Uso:
    uv run acodo backup
    uv run acodo backup --archiver tar.gz
    uv run acodo backup -f ~/copias/proyecto.zip
"""

import shutil
import tarfile
import zipfile
from pathlib import Path

from rich.table import Table

from acodo.utils import parse_size
from acodo_cli.commands_service import console, fail, find_pycache, get_config
from acodo_cli.models import AcodoConfig, Archiver
from acodo_cli.typer_options import ArchiverOption, BackupFileOption

BACKUP_DIR_NAME = ".local"
"""Directorio de salida por defecto, relativo a la raíz del proyecto."""

ROOT_PATTERNS = [
    "*.toml",
    "*.md",
    "*.lock",
    "*.py",
    "*.yaml",
    "LICENSE",
    ".gitignore",
    ".gitattributes",
    ".python-version",
]
"""Ficheros en raíz a incluir."""


def _directories(cfg: AcodoConfig) -> list[str]:
    """Directorios cuya estructura se incluye completa."""
    return [".github", "scripts", cfg.src_dir, cfg.test_dir]


def _clean_pycache(root: Path, dirs: list[str]) -> int:
    """Borra los `__pycache__` de `dirs` (sin tocar `.venv`). Devuelve el total."""
    caches = find_pycache(root, dirs)
    for cache_dir in caches:
        shutil.rmtree(cache_dir)
    return len(caches)


def _collect_files(root: Path, dirs: list[str]) -> list[Path]:
    """Devuelve, ordenados y sin duplicados, los ficheros a incluir (relativos)."""
    found: set[Path] = set()
    for dir_name in dirs:
        found.update(f for f in (root / dir_name).rglob("*") if f.is_file())
    for pattern in ROOT_PATTERNS:
        found.update(f for f in root.glob(pattern) if f.is_file())
    return sorted(f.relative_to(root) for f in found)


def _write_zip(root: Path, output: Path, files: list[Path]) -> None:
    """Crea un zip con `files` (rutas relativas a `root`)."""
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            zf.write(root / file, file)


def _write_tar_gz(root: Path, output: Path, files: list[Path]) -> None:
    """Crea un tar.gz con `files` (rutas relativas a `root`)."""
    with tarfile.open(output, "w:gz") as tf:
        for file in files:
            tf.add(root / file, arcname=file.as_posix(), recursive=False)


def _write_archive(
    archiver: Archiver, root: Path, output: Path, files: list[Path]
) -> None:
    """Crea el archivo comprimido en el formato elegido."""
    match archiver:
        case Archiver.ZIP:
            _write_zip(root, output, files)
        case Archiver.TAR_GZ:
            _write_tar_gz(root, output, files)


def main(
    file: BackupFileOption = None,
    archiver: ArchiverOption = Archiver.ZIP,
) -> None:
    """Limpia las cachés y crea una copia de seguridad."""
    cfg = get_config()
    root = cfg.root
    dirs = _directories(cfg)
    output = (file or root / BACKUP_DIR_NAME / f"backup.{archiver.value}").resolve()

    with console.status("Limpiando cachés __pycache__..."):
        removed = _clean_pycache(root, dirs)
    console.print(f"[ok]✓[/] {removed} directorios __pycache__ eliminados")

    files = _collect_files(root, dirs)
    if output in {(root / f).resolve() for f in files}:
        fail(f"La ruta de salida coincide con un fichero del proyecto: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    with console.status(f"Comprimiendo {len(files)} ficheros ({archiver.value})..."):
        _write_archive(archiver, root, output, files)

    table = Table(
        title="Copia de seguridad creada",
        title_style="title",
        show_header=False,
        border_style="border",
    )
    table.add_column(style="label")
    table.add_column(overflow="fold")
    table.add_row("Formato", archiver.value)
    table.add_row("Ficheros", str(len(files)))
    table.add_row("Tamaño", parse_size(output.stat().st_size))
    table.add_row("Ruta", str(output))
    console.print(table)
