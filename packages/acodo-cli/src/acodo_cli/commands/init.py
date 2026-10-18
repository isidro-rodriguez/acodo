"""Prepara un proyecto para usar `acodo`.

Según dónde se ejecute:

- Con `acodo.toml` (aquí o en un directorio superior): avisa de que el proyecto
  ya está inicializado y no toca nada.
- En el entorno de un proyecto sin `acodo.toml`: copia el `acodo.toml` por
  defecto, crea la plantilla del JSON de la GitHub App y asegura que `.local/`
  está en `.gitignore`.
- Fuera de un proyecto (instalación global): ofrece clonar la plantilla de
  Acodo en la ruta que se indique (por defecto `./acodo/`).

Uso:
    uv run acodo init
"""

import json
import shutil
import sys
from pathlib import Path

import typer
from rich.markup import escape

from acodo_cli.commands_service import (
    GH_CONFIG_TEMPLATE,
    console,
    fail,
    is_global_install,
    run,
)
from acodo_cli.config import (
    ACODO_TOML,
    DEFAULT_GH_CONFIG_FILE,
    ConfigError,
    default_acodo_toml,
    find_acodo_toml,
)

TEMPLATE_URL = "https://github.com/isidro-rodriguez/acodo-template"
"""Repositorio de la plantilla de proyecto."""

DEFAULT_TEMPLATE_DIR = "acodo"
"""Directorio por defecto donde se clona la plantilla."""


def is_initialized(start: Path) -> bool:
    """Indica si `start` o alguno de sus superiores contiene `acodo.toml`."""
    try:
        find_acodo_toml(start)
    except ConfigError:
        return False
    return True


def _done(message: str) -> None:
    console.print(f"[ok]✓[/] {escape(message)}")


def _skipped(message: str) -> None:
    console.print(f"[muted]·[/] {escape(message)}")


def _create_acodo_toml(root: Path) -> None:
    (root / ACODO_TOML).write_text(default_acodo_toml(), encoding="utf-8")
    _done(f"Creado {ACODO_TOML}")


def _create_gh_template(root: Path) -> None:
    gh_config = root / DEFAULT_GH_CONFIG_FILE
    if gh_config.exists():
        _skipped(f"{DEFAULT_GH_CONFIG_FILE} ya existe")
        return
    gh_config.parent.mkdir(parents=True, exist_ok=True)
    gh_config.write_text(
        json.dumps(GH_CONFIG_TEMPLATE, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _done(f"Creada la plantilla {DEFAULT_GH_CONFIG_FILE}")


def _ignore_local(root: Path) -> None:
    gitignore = root / ".gitignore"
    lines = (
        gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    )
    if any(line.strip().strip("/") == ".local" for line in lines):
        _skipped(".local/ ya está en .gitignore")
        return
    lines.append(".local/")
    gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _done("Añadido .local/ a .gitignore")


def clone_template() -> None:
    """Ofrece clonar la plantilla de Acodo en la ruta que elija el usuario."""
    if not typer.confirm("Esto no es un proyecto Acodo. ¿Clonar la plantilla?"):
        _skipped("Sin cambios")
        return
    target = Path(typer.prompt("Ruta de destino", default=DEFAULT_TEMPLATE_DIR))
    if target.is_file() or (target.is_dir() and any(target.iterdir())):
        fail(f"La ruta de destino ya existe y no está vacía: {target}")
    git = shutil.which("git")
    if git is None:
        fail("No se encontró `git` en el PATH.")
    command = [git, "clone", "--depth", "1", TEMPLATE_URL, str(target)]
    if run(command, Path.cwd()) != 0:
        fail(f"No se pudo clonar {TEMPLATE_URL}.")
    _done(f"Plantilla clonada en {target}")


def main() -> None:
    """Inicializa `acodo` según el contexto (ver la documentación del módulo)."""
    root = Path.cwd()
    if is_initialized(root):
        _skipped(f"El proyecto ya está inicializado ({ACODO_TOML})")
        return
    if is_global_install(Path(sys.prefix), Path(sys.base_prefix)):
        clone_template()
        return
    _create_acodo_toml(root)
    _create_gh_template(root)
    _ignore_local(root)
