"""Documentación de la API con pdoc.

Uso:
    uv run acodo api
    uv run acodo api --path src/paquete/modulo.py
    uv run acodo api --output docs
"""

import shutil

import typer

from acodo_cli.commands_service import (
    console,
    discover_package_name,
    fail,
    get_config,
    run,
)
from acodo_cli.typer_options import ApiOutputOption, ApiPathOption


def main(
    path: ApiPathOption = None,
    output: ApiOutputOption = None,
) -> None:
    """Muestra la documentación de la API con pdoc (docstrings estilo Google)."""
    uv = shutil.which("uv")
    if uv is None:
        fail("No se encontró `uv` en el PATH.")

    cfg = get_config()
    target = path or cfg.src / discover_package_name(cfg.src)
    command = [uv, "run", "--with", "pdoc", "pdoc", "-d", "google"]
    if output is not None:
        command += ["-o", str(output)]
    command.append(str(target))

    try:
        code = run(command, cfg.root)
    except KeyboardInterrupt:  # Ctrl-C cierra el servidor de pdoc.
        raise typer.Exit(code=0) from None
    if code != 0:
        raise typer.Exit(code=code)
    if output is not None:
        console.print(f"[ok]✓[/] Documentación generada en {output}")
