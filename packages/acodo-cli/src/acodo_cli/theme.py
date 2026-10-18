"""Paleta de colores de Acodo y estilos de Rich y de Typer derivados de ella."""

from rich.theme import Theme
from typer import rich_utils

PALETTE: dict[str, str] = {
    "white": "#FFFFFF",
    "green": "#2E7D32",
    "light_green": "#66BB6A",
    "dark_brown": "#5D4037",
    "light_brown": "#8C6E63",
    "orange": "#E65100",
}
"""Colores del logo de Acodo (nombre -> hexadecimal)."""

ACODO_STYLES: dict[str, str] = {
    "ok": f"bold {PALETTE['light_green']}",
    "error": f"bold {PALETTE['orange']}",
    "warning": PALETTE["orange"],
    "title": f"bold {PALETTE['light_green']}",
    "label": f"bold {PALETTE['light_brown']}",
    "muted": f"dim {PALETTE['light_brown']}",
    "border": PALETTE["green"],
    "total": f"bold {PALETTE['white']}",
    "lines.code": PALETTE["light_green"],
    "lines.docs": PALETTE["light_brown"],
    "lines.total": f"bold {PALETTE['white']}",
}
"""Estilos con nombre: el markup y los `style=` de los comandos usan solo estos."""

ACODO_THEME = Theme(ACODO_STYLES)
"""Tema de Rich construido con `ACODO_STYLES` (hereda los estilos por defecto)."""

_TYPER_STYLES: dict[str, str] = {
    "STYLE_OPTION": PALETTE["light_green"],
    "STYLE_SWITCH": PALETTE["light_green"],
    "STYLE_NEGATIVE_OPTION": PALETTE["orange"],
    "STYLE_NEGATIVE_SWITCH": PALETTE["orange"],
    "STYLE_USAGE": PALETTE["light_green"],
    "STYLE_USAGE_COMMAND": f"bold {PALETTE['white']}",
    "STYLE_COMMANDS_TABLE_FIRST_COLUMN": f"bold {PALETTE['light_green']}",
    "STYLE_REQUIRED_SHORT": PALETTE["orange"],
    "STYLE_REQUIRED_LONG": f"dim {PALETTE['orange']}",
    "STYLE_OPTION_ENVVAR": f"dim {PALETTE['light_brown']}",
    "STYLE_OPTION_DEFAULT": f"dim {PALETTE['light_brown']}",
    "STYLE_ERRORS_SUGGESTION": f"italic {PALETTE['light_brown']}",
    "STYLE_OPTIONS_PANEL_BORDER": PALETTE["green"],
    "STYLE_COMMANDS_PANEL_BORDER": PALETTE["green"],
    "STYLE_ERRORS_PANEL_BORDER": PALETTE["orange"],
    "STYLE_ABORTED": PALETTE["orange"],
}


def apply_typer_styles() -> None:
    """Aplica la paleta de Acodo a la ayuda y a los errores que pinta Typer.

    Solo toca las constantes que existan en la versión instalada de Typer.
    """
    for name, style in _TYPER_STYLES.items():
        if hasattr(rich_utils, name):
            setattr(rich_utils, name, style)
