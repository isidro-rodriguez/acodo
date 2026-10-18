"""Copia de seguridad manual.

Limpia las cachés `__pycache__` y comprime los ficheros de las rutas de
`[backup]` y `[all]` (más los de configuración de la raíz) en el `target` de
`[backup]` de `acodo.toml`. El formato (zip o tar.gz) sale de su extensión.

Uso:
    uv run acodo backup
"""

import shutil
import tarfile
import zipfile
from pathlib import Path

from rich.table import Table

from acodo.utils import parse_size
from acodo_cli.commands_service import (
    console,
    fail,
    find_pycache,
    get_config,
    output_path,
    scope_files,
)
from acodo_cli.models import AcodoConfig, Archiver

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


def archiver_for(output: Path) -> Archiver:
    """Deduce el formato de compresión de la extensión de `output`.

    Examples:
        >>> archiver_for(Path("copia.tar.gz"))
        <Archiver.TAR_GZ: 'tar.gz'>
    """
    for archiver in Archiver:
        if output.name.endswith(f".{archiver.value}"):
            return archiver
    formats = ", ".join(f".{archiver.value}" for archiver in Archiver)
    fail(f"El `target` de [backup] debe acabar en {formats}: {output.name}")


def _collect_files(cfg: AcodoConfig) -> list[Path]:
    """Devuelve, ordenados y sin duplicados, los ficheros a incluir (relativos)."""
    found = set(scope_files(cfg, "backup"))
    for pattern in ROOT_PATTERNS:
        found.update(f for f in cfg.root.glob(pattern) if f.is_file())
    return sorted(f.relative_to(cfg.root) for f in found)


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


def main() -> None:
    """Limpia las cachés y crea una copia de seguridad."""
    cfg = get_config()
    root = cfg.root
    output = output_path(cfg, cfg.backup).resolve()
    archiver = archiver_for(output)

    with console.status("Limpiando cachés __pycache__..."):
        caches = find_pycache(cfg)
        for cache_dir in caches:
            shutil.rmtree(cache_dir)
    console.print(f"[ok]✓[/] {len(caches)} directorios __pycache__ eliminados")

    files = _collect_files(cfg)
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
