"""Documentación de la API generada a partir de los docstrings.

Recorre los `.py` de las rutas de `[api]` y `[all]` con `ast` (sin importar el
código) y escribe en el `target` de `[api]` de `acodo.toml` los módulos,
clases, funciones y métodos públicos que tengan docstring.

Uso:
    uv run acodo api
"""

import ast

from acodo_cli.commands_service import (
    console,
    fail,
    get_config,
    output_path,
    scope_files,
)

SUPPORTED_SUFFIXES = (".md",)
"""Formatos de salida disponibles, según la extensión de `target`."""

_Definition = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


def _signature(node: _Definition) -> str:
    """Firma de una función (`def nombre(args) -> ret`) o `class nombre`."""
    if isinstance(node, ast.ClassDef):
        bases = ", ".join(ast.unparse(base) for base in node.bases)
        return f"class {node.name}({bases})" if bases else f"class {node.name}"
    keyword = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{keyword} {node.name}({ast.unparse(node.args)}){returns}"


def _public_definitions(body: list[ast.stmt]) -> list[_Definition]:
    """Clases y funciones públicas (sin `_` inicial) con docstring."""
    return [
        node
        for node in body
        if isinstance(node, _Definition)
        and not node.name.startswith("_")
        and ast.get_docstring(node)
    ]


def _render_definition(node: _Definition, level: int) -> list[str]:
    """Markdown de una definición y, si es una clase, de sus métodos públicos."""
    lines = [f"{'#' * level} `{node.name}`", "", f"```python\n{_signature(node)}\n```"]
    lines += ["", ast.get_docstring(node) or "", ""]
    if isinstance(node, ast.ClassDef):
        for method in _public_definitions(node.body):
            lines += _render_definition(method, level + 1)
    return lines


def render_module(source: str, title: str) -> str:
    """Markdown de un módulo; vacío si no tiene nada público que documentar.

    Args:
        source: Código fuente del módulo.
        title: Título de la sección (ruta del módulo).

    Returns:
        Texto Markdown, o cadena vacía si el código no se puede analizar o no
        tiene docstrings públicos.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ""
    definitions = _public_definitions(tree.body)
    module_doc = ast.get_docstring(tree)
    if not definitions and not module_doc:
        return ""
    lines = [f"## `{title}`", ""]
    if module_doc:
        lines += [module_doc, ""]
    for node in definitions:
        lines += _render_definition(node, 3)
    return "\n".join(lines)


def main() -> None:
    """Genera la documentación de la API en el `target` de `[api]`."""
    cfg = get_config()
    output = output_path(cfg, cfg.api)
    if not output.name.endswith(SUPPORTED_SUFFIXES):
        formats = ", ".join(SUPPORTED_SUFFIXES)
        fail(f"El `target` de [api] debe acabar en {formats}: {output.name}")

    sections = [
        render_module(
            path.read_text(encoding="utf-8"), path.relative_to(cfg.root).as_posix()
        )
        for path in scope_files(cfg, "api", ".py")
    ]
    sections = [section for section in sections if section]
    if not sections:
        fail("No hay nada que documentar: ningún módulo público con docstring.")

    output.parent.mkdir(parents=True, exist_ok=True)
    text = f"# API de {cfg.project_name}\n\n" + "\n".join(sections)
    output.write_text(text.rstrip() + "\n", encoding="utf-8")
    console.print(f"[ok]✓[/] Documentación generada en {output}")
