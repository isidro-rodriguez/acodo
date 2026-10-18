"""Banner de Acodo: ASCII art con degradado y panel de `--version`."""

import platform
import sys
from importlib.metadata import PackageNotFoundError, version

import typer
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from acodo_cli import __version__
from acodo_cli.commands_service import console
from acodo_cli.theme import PALETTE

ASCII_ART = """\
 █████╗  ██████╗ ██████╗ ██████╗  ██████╗
██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔═══██╗
███████║██║     ██║   ██║██║  ██║██║   ██║
██╔══██║██║     ██║   ██║██║  ██║██║   ██║
██║  ██║╚██████╗╚██████╔╝██████╔╝╚██████╔╝
╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝"""
"""Logo «ACODO» en la fuente figlet `ansi_shadow`."""


def _rgb(color: str) -> tuple[int, int, int]:
    """Convierte `#RRGGBB` en una tupla `(r, g, b)`."""
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def gradient_art(start: str, end: str) -> Text:
    """Devuelve el ASCII art con un degradado horizontal entre dos colores.

    Args:
        start: Color inicial en hexadecimal (`#RRGGBB`).
        end: Color final en hexadecimal (`#RRGGBB`).

    Returns:
        Texto de Rich con el color de cada columna interpolado.
    """
    lines = ASCII_ART.splitlines()
    width = max(len(line) for line in lines)
    (r1, g1, b1), (r2, g2, b2) = _rgb(start), _rgb(end)
    text = Text(no_wrap=True)
    for line in lines:
        for column, char in enumerate(line.ljust(width)):
            ratio = column / max(width - 1, 1)
            color = (
                f"#{round(r1 + (r2 - r1) * ratio):02X}"
                f"{round(g1 + (g2 - g1) * ratio):02X}"
                f"{round(b1 + (b2 - b1) * ratio):02X}"
            )
            text.append(char, style=color)
        text.append("\n")
    text.rstrip()
    return text


def show_banner() -> None:
    """Imprime el logo de Acodo con degradado."""
    console.print(gradient_art(PALETTE["green"], PALETTE["light_green"]))
    console.print()


def _framework_version() -> str:
    """Versión instalada de `acodo-framework`, o un guion si no está."""
    try:
        return version("acodo-framework")
    except PackageNotFoundError:
        return "—"


def version_callback(value: bool) -> None:
    """Muestra el panel de versión y termina si se pasó `--version`."""
    if not value:
        return
    info = Table(show_header=False, box=None, padding=(0, 2))
    info.add_column(style="label")
    info.add_column()
    info.add_row("acodo-cli", __version__)
    info.add_row("acodo-framework", _framework_version())
    info.add_row("Python", platform.python_version())
    info.add_row("Plataforma", sys.platform)
    console.print(
        Panel(
            gradient_art(PALETTE["green"], PALETTE["light_green"]),
            border_style="border",
            expand=False,
        )
    )
    console.print(info)
    raise typer.Exit
