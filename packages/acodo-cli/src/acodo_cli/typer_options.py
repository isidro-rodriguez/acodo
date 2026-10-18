"""Opciones de Typer reutilizadas por la aplicación."""

from typing import Annotated

import typer

from acodo_cli.banner import version_callback

VersionOption = Annotated[
    bool,
    typer.Option(
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Muestra la versión de acodo y sale.",
    ),
]
