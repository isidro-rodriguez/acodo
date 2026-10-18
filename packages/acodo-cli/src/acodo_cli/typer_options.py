"""Opciones de Typer reutilizadas por los comandos."""

from pathlib import Path
from typing import Annotated

import typer

from acodo_cli.banner import version_callback
from acodo_cli.models import Archiver

# --- global ------------------------------------------------------------------

VersionOption = Annotated[
    bool,
    typer.Option(
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Muestra la versión de acodo y sale.",
    ),
]

# --- api ---------------------------------------------------------------------

ApiOutputOption = Annotated[
    Path | None,
    typer.Option(
        "--output",
        "-o",
        file_okay=False,
        resolve_path=True,
        help="Genera el HTML en este directorio en vez de abrir el navegador.",
    ),
]

ApiPathOption = Annotated[
    Path | None,
    typer.Option(
        "--path",
        "-p",
        exists=True,
        resolve_path=True,
        help="Paquete o módulo a documentar (por defecto src/<paquete>).",
    ),
]

# --- backup ------------------------------------------------------------------

BackupFileOption = Annotated[
    Path | None,
    typer.Option(
        "--file",
        "-f",
        dir_okay=False,
        resolve_path=True,
        help="Ruta del fichero de salida (por defecto .local/backup.<formato>).",
    ),
]

ArchiverOption = Annotated[
    Archiver,
    typer.Option(
        "--archiver",
        "-a",
        case_sensitive=False,
        help="Formato de compresión.",
    ),
]

# --- build -------------------------------------------------------------------

BuildOutputOption = Annotated[
    Path | None,
    typer.Option(
        "--output",
        "-o",
        file_okay=False,
        resolve_path=True,
        help="Directorio de salida del compilado (por defecto build en la raíz).",
    ),
]

OneFileOption = Annotated[
    bool,
    typer.Option(
        "--onefile",
        help="Empaquetar en un único fichero ejecutable.",
    ),
]

NoIconOption = Annotated[
    bool,
    typer.Option(
        "--no-icon",
        help="Empaquetar sin icono.",
    ),
]

# --- check -------------------------------------------------------------------

FormatOption = Annotated[
    bool,
    typer.Option(
        "--format",
        help="Formatea el código (ruff format).",
    ),
]

LintOption = Annotated[
    bool,
    typer.Option(
        "--lint",
        help="Revisa y autocorrige el lint (ruff check).",
    ),
]

TestOption = Annotated[
    bool,
    typer.Option(
        "--tests",
        help="Ejecuta las pruebas (pytest).",
    ),
]

TypesOption = Annotated[
    bool,
    typer.Option(
        "--types",
        help="Comprueba el tipado (ty check).",
    ),
]

CiOption = Annotated[
    bool,
    typer.Option(
        "--ci",
        help="Solo verifica, sin modificar ficheros (ruff sin --fix).",
    ),
]

CovOption = Annotated[
    bool,
    typer.Option(
        "--cov",
        help="Mide la cobertura de pytest (requiere pytest-cov).",
    ),
]

# --- clean -------------------------------------------------------------------

DryRunOption = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Solo muestra lo que se eliminaría.",
    ),
]

# --- code-count --------------------------------------------------------------

VerboseOption = Annotated[
    bool,
    typer.Option(
        "--verbose",
        "-v",
        help="Lista el resultado de cada fichero.",
    ),
]

JsonOption = Annotated[
    bool,
    typer.Option(
        "--json",
        help="Imprime el resultado como JSON (ignora --verbose y --tree).",
    ),
]

TreeOption = Annotated[
    bool,
    typer.Option(
        "--tree",
        "-t",
        help="Muestra el resultado en árbol de Rich en vez de tabla.",
    ),
]

# --- gh-token / gh-check -----------------------------------------------------

GhConfigFileOption = Annotated[
    Path | None,
    typer.Option(
        "--file",
        "-f",
        help="Fichero JSON de configuración (por defecto .local/gh_app.json).",
    ),
]

OnlyTokenOption = Annotated[
    bool,
    typer.Option(
        "--only-token",
        "-o",
        help="Imprime solo el token en vez del JSON completo.",
    ),
]

NoClipboardOption = Annotated[
    bool,
    typer.Option(
        "--no-clipboard",
        help="No copiar el resultado al portapapeles.",
    ),
]

NoPrintOption = Annotated[
    bool,
    typer.Option(
        "--no-print",
        help="No imprimir el resultado por stdout.",
    ),
]
