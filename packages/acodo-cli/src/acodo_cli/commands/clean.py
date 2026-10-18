"""Limpieza de cachés y artefactos generados.

Elimina los `__pycache__` de las rutas de `[all]` y, en la raíz, `.ruff_cache`,
`.pytest_cache`, `.coverage`, `htmlcov`, `build` y `dist`. Lista lo que va a
borrar y pide confirmación. Nunca toca `.venv`.

Uso:
    uv run acodo clean
"""

import shutil
from pathlib import Path

import typer
from rich.table import Table

from acodo_cli.commands_service import console, find_pycache, get_config

ROOT_TARGETS = (".ruff_cache", ".pytest_cache", ".coverage", "htmlcov", "build", "dist")
"""Elementos en la raíz del proyecto que se eliminan si existen."""


def _remove(path: Path) -> None:
    """Elimina un fichero o directorio."""
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def main() -> None:
    """Elimina cachés y artefactos generados del proyecto, previa confirmación."""
    cfg = get_config()
    root = cfg.root

    targets = find_pycache(cfg)
    targets += [root / name for name in ROOT_TARGETS if (root / name).exists()]

    if not targets:
        console.print("[ok]✓[/] Nada que limpiar")
        return

    table = Table(show_header=False, border_style="border")
    table.add_column(style="label")
    table.add_column(overflow="fold")
    for target in targets:
        table.add_row("Se eliminará", target.relative_to(root).as_posix())
    console.print(table)

    if not typer.confirm(f"¿Eliminar {len(targets)} elementos?", default=True):
        console.print("[muted]·[/] Sin cambios")
        return

    for target in targets:
        _remove(target)
    console.print(f"[ok]✓[/] {len(targets)} elementos eliminados")
