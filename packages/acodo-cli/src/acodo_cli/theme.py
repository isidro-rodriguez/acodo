"""Tema de color del framework Acodo para Rich y para la ayuda de Typer.

Todo el color de la CLI sale de `ACODO_THEME`. Los estilos con significado
(`ok`, `error`, `warning`, `label`, `muted`, `title`...) se definen a partir de
esa paleta y son los únicos que debe usar el markup de Rich.
"""

import typer.rich_utils as typer_styles
from rich.theme import Theme

ACODO_THEME: dict[str, str] = {
    "white": "#FFFFFF",
    "green": "#2E7D32",
    "light_green": "#66BB6A",
    "dark_brown": "#5D4037",
    "light_brown": "#8C6E63",
    "orange": "#E65100",
}
"""Paleta del framework Acodo (también disponible como nombres de estilo)."""

_C = ACODO_THEME

SEMANTIC_STYLES: dict[str, str] = {
    "ok": f"bold {_C['light_green']}",
    "warning": _C["orange"],
    "error": f"bold {_C['orange']}",
    "label": _C["light_green"],
    "muted": _C["light_brown"],
    "title": f"bold {_C['light_green']}",
    "border": _C["light_brown"],
    "total": f"bold {_C['white']}",
    "lines.code": _C["light_green"],
    "lines.docs": _C["light_brown"],
    "lines.total": _C["white"],
    # Estilos internos de Rich que por defecto usan colores ajenos a la paleta.
    "rule.line": _C["green"],
    "tree.line": _C["light_brown"],
    "status.spinner": _C["light_green"],
}
"""Estilos con significado, construidos con colores de la paleta."""

THEME = Theme({**ACODO_THEME, **SEMANTIC_STYLES})
"""Tema de Rich: paleta y estilos con significado."""

TYPER_STYLES: dict[str, str] = {
    "STYLE_ABORTED": _C["orange"],
    "STYLE_COMMANDS_PANEL_BORDER": _C["light_brown"],
    "STYLE_COMMANDS_TABLE_FIRST_COLUMN": f"bold {_C['light_green']}",
    "STYLE_DEPRECATED": _C["orange"],
    "STYLE_DEPRECATED_COMMAND": _C["light_brown"],
    "STYLE_ERRORS_PANEL_BORDER": _C["orange"],
    "STYLE_ERRORS_SUGGESTION": _C["light_brown"],
    "STYLE_HELPTEXT": _C["light_brown"],
    "STYLE_NEGATIVE_OPTION": f"bold {_C['orange']}",
    "STYLE_NEGATIVE_SWITCH": f"bold {_C['orange']}",
    "STYLE_OPTION": f"bold {_C['light_green']}",
    "STYLE_OPTIONS_PANEL_BORDER": _C["light_brown"],
    "STYLE_OPTION_DEFAULT": _C["light_brown"],
    "STYLE_OPTION_ENVVAR": _C["light_brown"],
    "STYLE_REQUIRED_LONG": _C["orange"],
    "STYLE_REQUIRED_SHORT": _C["orange"],
    "STYLE_SWITCH": f"bold {_C['light_green']}",
    "STYLE_TYPES": _C["light_brown"],
    "STYLE_TYPES_SEPARATOR": _C["light_brown"],
    "STYLE_USAGE": _C["light_green"],
}
"""Estilos de la ayuda de Typer (`typer.rich_utils.STYLE_*`) con la paleta."""

TYPER_TEXTS: dict[str, str] = {
    # La consola de Typer no usa nuestro tema: el markup lleva el hex directamente.
    "RICH_HELP": (
        f"Try [{_C['light_green']}]'{{command_path}} {{help_option}}'[/] for help."
    ),
}
"""Textos de Typer con color incrustado (`typer.rich_utils`)."""


def apply_typer_styles() -> None:
    """Aplica la paleta Acodo a la ayuda y a los errores de uso de Typer."""
    for name, value in {**TYPER_STYLES, **TYPER_TEXTS}.items():
        setattr(typer_styles, name, value)
