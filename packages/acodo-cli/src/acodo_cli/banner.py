"""Banner de Acodo: ASCII art con degradado y panel de versión."""

import platform
from collections.abc import Sequence

import typer
from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from acodo_cli import __version__
from acodo_cli.commands_service import console
from acodo_cli.theme import ACODO_THEME

ASCII_ART = """\
 █████╗  ██████╗ ██████╗ ██████╗  ██████╗
██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔═══██╗
███████║██║     ██║   ██║██║  ██║██║   ██║
██╔══██║██║     ██║   ██║██║  ██║██║   ██║
██║  ██║╚██████╗╚██████╔╝██████╔╝╚██████╔╝
╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝
"""
"""«Acodo» en figlet con la fuente `ansi_shadow` (pyfiglet 1.0.4)."""

GRADIENT_STOPS = ("light_green", "green", "orange")
"""Colores de la paleta entre los que se reparte el degradado (izquierda a derecha)."""

_RGB = tuple[int, int, int]


def _hex_to_rgb(color: str) -> _RGB:
    """Convierte `#RRGGBB` a una tupla `(r, g, b)`."""
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def gradient_color(position: float, stops: Sequence[_RGB]) -> _RGB:
    """Color del degradado en `position` (0.0 al inicio, 1.0 al final).

    Args:
        position: Posición relativa, entre 0 y 1.
        stops: Colores extremos e intermedios, repartidos a partes iguales.

    Returns:
        Color interpolado linealmente entre los dos `stops` vecinos.

    Examples:
        >>> gradient_color(0.5, [(0, 0, 0), (100, 200, 50)])
        (50, 100, 25)
    """
    position = min(max(position, 0.0), 1.0)
    scaled = position * (len(stops) - 1)
    index = min(int(scaled), len(stops) - 2)
    ratio = scaled - index
    start, end = stops[index], stops[index + 1]
    r, g, b = (round(s + (e - s) * ratio) for s, e in zip(start, end, strict=True))
    return r, g, b


def render_art() -> Text:
    """Devuelve el ASCII art con el degradado de la paleta aplicado por columnas."""
    stops = [_hex_to_rgb(ACODO_THEME[name]) for name in GRADIENT_STOPS]
    lines = ASCII_ART.splitlines()
    last_column = max(max(len(line) for line in lines) - 1, 1)

    text = Text(no_wrap=True)
    for number, line in enumerate(lines):
        for column, char in enumerate(line):
            if char == " ":
                text.append(char)
                continue
            r, g, b = gradient_color(column / last_column, stops)
            text.append(char, style=Style(color=f"#{r:02X}{g:02X}{b:02X}"))
        if number < len(lines) - 1:
            text.append("\n")
    return text


def build_version_panel() -> Panel:
    """Construye el panel con el logo, la versión y datos del entorno."""
    info = Group(
        Text(f"Acodo CLI  v{__version__}", style="total", justify="center"),
        Text(
            "Acodo Framework · herramientas de desarrollo",
            style="muted",
            justify="center",
        ),
        Text(
            f"Python {platform.python_version()} · {platform.system()}",
            style="muted",
            justify="center",
        ),
    )
    return Panel(
        Group(Align.center(render_art()), Text(""), info),
        border_style="border",
        padding=(1, 4),
        expand=False,
    )


def show_banner() -> None:
    """Imprime el panel de versión."""
    console.print(build_version_panel())


def version_callback(value: bool) -> None:
    """Callback de `--version`: muestra el panel y termina."""
    if value:
        show_banner()
        raise typer.Exit
