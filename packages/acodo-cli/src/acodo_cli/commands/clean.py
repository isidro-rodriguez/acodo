"""Limpieza de cachés y artefactos generados.

Elimina `__pycache__` (en código, tests y scripts), `.ruff_cache`,
`.pytest_cache`, `.coverage`, `htmlcov`, `build` y `dist`. Nunca toca `.venv`.

Uso:
    uv run acodo clean
    uv run acodo clean --dry-run
"""

import shutil
from pathlib import Path

from rich.table import Table

from acodo_cli.commands_service import console, find_pycache, get_config
from acodo_cli.typer_options import DryRunOption

ROOT_TARGETS = (".ruff_cache", ".pytest_cache", ".coverage", "htmlcov", "build", "dist")
"""Elementos en la raíz del proyecto que se eliminan si existen."""


def _remove(path: Path) -> None:
    """Elimina un fichero o directorio."""
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def main(dry_run: DryRunOption = False) -> None:
    """Elimina cachés y artefactos generados del proyecto."""
    cfg = get_config()
    root = cfg.root

    targets = find_pycache(root, [cfg.src_dir, cfg.test_dir, "scripts"])
    targets += [root / name for name in ROOT_TARGETS if (root / name).exists()]

    if not targets:
        console.print("[ok]✓[/] Nada que limpiar")
        return

    verb = "Se eliminaría" if dry_run else "Eliminado"
    table = Table(show_header=False, border_style="border")
    table.add_column(style="label")
    table.add_column(overflow="fold")
    for target in targets:
        if not dry_run:
            _remove(target)
        table.add_row(verb, target.relative_to(root).as_posix())
    console.print(table)

    summary = "se eliminarían" if dry_run else "eliminados"
    console.print(f"[ok]✓[/] {len(targets)} elementos {summary}")
