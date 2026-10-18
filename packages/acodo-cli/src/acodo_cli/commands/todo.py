"""Lista los comentarios TODO, FIXME, XXX y HACK del proyecto.

Solo mira comentarios reales de ficheros `.py` (no cadenas) de las rutas de
`[todo]` y `[all]`. Sale con código 1 si algún marcador no tiene texto de contexto.

Uso:
    uv run acodo todo
"""

import io
import re
import tokenize
from pathlib import Path

import typer
from rich.table import Table

from acodo_cli.commands_service import console, get_config, scope_files

MARKER_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b[:\s(]*(.*)")


def find_markers(path: Path) -> list[tuple[int, str, str]]:
    """Devuelve `(línea, marcador, texto)` de cada marcador en comentarios."""
    try:
        source = path.read_text(encoding="utf-8")
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (OSError, UnicodeDecodeError, tokenize.TokenError, SyntaxError):
        return []

    found = []
    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        match = MARKER_RE.search(token.string)
        if match:
            found.append((token.start[0], match.group(1), match.group(2).strip(" )")))
    return found


def main() -> None:
    """Muestra los marcadores pendientes del código."""
    cfg = get_config()

    rows = [
        (path.relative_to(cfg.root).as_posix(), line, marker, text)
        for path in scope_files(cfg, "todo", ".py")
        for line, marker, text in find_markers(path)
    ]

    if not rows:
        console.print("[ok]✓[/] Sin marcadores pendientes")
        return

    table = Table(
        title="Marcadores pendientes", title_style="title", border_style="border"
    )
    table.add_column("Ubicación", style="label", overflow="fold")
    table.add_column("Marcador", style="warning")
    table.add_column("Texto", overflow="fold")
    for relative, line, marker, text in rows:
        table.add_row(f"{relative}:{line}", marker, text or "[error](sin contexto)[/]")
    console.print(table)

    if any(not text for *_, text in rows):
        raise typer.Exit(code=1)
