"""Genera la referencia de la API de ``acodo-framework`` en Markdown.

Analiza el código fuente con ``ast`` (sin importarlo, así que no necesita las
dependencias del paquete) y escribe en ``docs/api/`` una página por paquete y por
módulo, más un índice general. Los docstrings se esperan en estilo Google.

El resultado es un derivado del código: ``docs/api/`` está en ``.gitignore`` y se
regenera antes de construir la documentación (hook ``pre-push``).

Uso:
    uv run python scripts/gen-api.py
"""

from __future__ import annotations

import ast
import re
import shutil
import sys
import textwrap
import tomllib
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
FRAMEWORK = ROOT / "packages" / "acodo-framework"
SOURCE = FRAMEWORK / "src"
PACKAGE = "acodo"
OUTPUT = ROOT / "docs" / "api"
REPO_URL = "https://github.com/isidro-rodriguez/acodo"
MAX_SIGNATURE_WIDTH = 80

FUNCTION_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)
ENUM_BASES = frozenset({"Enum", "StrEnum", "IntEnum", "Flag", "IntFlag"})
PROPERTY_DECORATORS = frozenset({"property", "cached_property"})

# Secciones de los docstrings estilo Google y su título en español.
SECTION_TITLES = {
    "Args": "Parámetros",
    "Arguments": "Parámetros",
    "Attributes": "Atributos",
    "Returns": "Devuelve",
    "Yields": "Produce",
    "Raises": "Lanza",
    "Example": "Ejemplos",
    "Examples": "Ejemplos",
    "Note": "Nota",
    "Notes": "Notas",
    "Warning": "Advertencia",
}
ITEM_SECTIONS = frozenset({"Args", "Arguments", "Attributes", "Raises"})
EXAMPLE_SECTIONS = frozenset({"Example", "Examples"})
ADMONITIONS = {"Note": "note", "Notes": "note", "Warning": "warning"}

SECTION_RE = re.compile(rf"^({'|'.join(SECTION_TITLES)}):\s*$")
ITEM_RE = re.compile(r"^(\*{0,2}[\w.]+)(?: \(([^)]*)\))?:(?: (.*))?$")
ROLE_RE = re.compile(r":(?:class|func|meth|mod|attr|exc|obj):`~?([^`]+)`")


class Entry(NamedTuple):
    """Elemento documentado de un módulo, para construir los resúmenes."""

    anchor: str
    title: str
    summary: str


# -----------------------------------------------------------------------------
# Docstrings
# -----------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Convierte los roles reST (``:class:`X```) en código en línea."""
    return ROLE_RE.sub(r"`\1`", text)


def _summary(doc: str) -> str:
    """Devuelve la primera línea de un docstring."""
    return _clean(doc.splitlines()[0]) if doc else ""


def _split_sections(doc: str) -> tuple[str, list[tuple[str, str]]]:
    """Separa un docstring en el cuerpo y sus secciones (`Args`, `Returns`...)."""
    body: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current = body
    for line in doc.splitlines():
        if match := SECTION_RE.match(line):
            current = []
            sections.append((match[1], current))
        else:
            current.append(line)
    return (
        "\n".join(body).strip(),
        [
            (key, textwrap.dedent("\n".join(lines)).strip("\n"))
            for key, lines in sections
        ],
    )


def _parse_items(text: str) -> list[tuple[str, str, str]]:
    """Extrae los elementos `nombre (tipo): descripción` de una sección."""
    items: list[list[str]] = []
    for line in text.splitlines():
        match = None if line[:1].isspace() else ITEM_RE.match(line)
        if match:
            items.append(list(match.groups(default="")))
        elif items and line.strip():
            items[-1][2] += f" {line.strip()}"
    return [(name, kind, desc.strip()) for name, kind, desc in items]


def _definition_list(items: list[tuple[str, str, str]]) -> list[str]:
    """Renderiza elementos como lista de definiciones de Markdown."""
    lines: list[str] = []
    for name, kind, desc in items:
        label = f"`{name}`" + (f" (`{kind}`)" if kind else "")
        lines += [label, f":   {_clean(desc) or '—'}", ""]
    return lines


def _examples(text: str) -> list[str]:
    """Renderiza los doctests como bloques `pycon` y deja el resto como texto."""
    lines: list[str] = []
    code: list[str] = []

    def flush() -> None:
        if code:
            lines.extend(["```pycon", *code, "```", ""])
            code.clear()

    for line in text.splitlines():
        if (code and line.strip()) or line.lstrip().startswith(">>>"):
            code.append(line)
        else:
            flush()
            lines.append(line)
    flush()
    return lines


def _render_section(key: str, text: str) -> list[str]:
    """Renderiza una sección de docstring."""
    title = SECTION_TITLES[key]
    if key in ITEM_SECTIONS:
        return [f"**{title}**", "", *_definition_list(_parse_items(text))]
    if key in EXAMPLE_SECTIONS:
        return [f"**{title}**", "", *_examples(text), ""]
    if key in ADMONITIONS:
        body = textwrap.indent(_clean(text), "    ")
        return [f'!!! {ADMONITIONS[key]} "{title}"', "", body, ""]
    return [f"**{title}**", "", _clean(text), ""]


# -----------------------------------------------------------------------------
# Firmas
# -----------------------------------------------------------------------------


def _param(arg: ast.arg, default: ast.expr | None) -> str:
    """Formatea un parámetro con su anotación y valor por defecto."""
    text = arg.arg
    if arg.annotation is not None:
        text += f": {ast.unparse(arg.annotation)}"
    if default is not None:
        separator = " = " if arg.annotation is not None else "="
        text += f"{separator}{ast.unparse(default)}"
    return text


def _parameters(args: ast.arguments) -> list[str]:
    """Lista los parámetros de una función tal y como se escriben en su firma."""
    positional = [*args.posonlyargs, *args.args]
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    params: list[str] = []
    for index, (arg, default) in enumerate(zip(positional, defaults, strict=True)):
        params.append(_param(arg, default))
        if index == len(args.posonlyargs) - 1:
            params.append("/")
    if args.vararg is not None:
        params.append(f"*{_param(args.vararg, None)}")
    elif args.kwonlyargs:
        params.append("*")
    params.extend(
        _param(arg, default)
        for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True)
    )
    if args.kwarg is not None:
        params.append(f"**{_param(args.kwarg, None)}")
    return params


def _wrap(head: str, params: list[str], tail: str = "") -> str:
    """Une cabecera y parámetros en una línea o, si es larga, uno por línea."""
    one_line = f"{head}({', '.join(params)}){tail}"
    if len(one_line) <= MAX_SIGNATURE_WIDTH or not params:
        return one_line
    body = "".join(f"    {param},\n" for param in params)
    return f"{head}(\n{body}){tail}"


def _decorator_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Nombres (sin módulo) de los decoradores de una función."""
    names: set[str] = set()
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        names.add(ast.unparse(target).rsplit(".", 1)[-1])
    return names


def _name_with_type_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Nombre de la función con sus parámetros de tipo (`get_env[T]`)."""
    if not node.type_params:
        return node.name
    return f"{node.name}[{', '.join(ast.unparse(p) for p in node.type_params)}]"


def _signature(
    node: ast.FunctionDef | ast.AsyncFunctionDef, *, method: bool = False
) -> str:
    """Firma de una función o método como código Python."""
    params = _parameters(node.args)
    if method and params and params[0] in {"self", "cls"}:
        del params[0]
    keyword = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    tail = f" -> {ast.unparse(node.returns)}" if node.returns is not None else ""
    code = _wrap(f"{keyword} {_name_with_type_params(node)}", params, tail)
    decorators = sorted(_decorator_names(node) & {"classmethod", "staticmethod"})
    return "".join(f"@{name}\n" for name in decorators) + code


# -----------------------------------------------------------------------------
# Símbolos
# -----------------------------------------------------------------------------


def _is_public(name: str) -> bool:
    """Indica si un nombre forma parte de la API pública."""
    return not name.startswith("_")


def _source_url(path: Path, line: int) -> str:
    """Enlace al código fuente en GitHub."""
    return f"{REPO_URL}/blob/main/{path.relative_to(ROOT).as_posix()}#L{line}"


def _render_symbol(
    *,
    level: int,
    title: str,
    anchor: str,
    code: str,
    doc: str,
    url: str,
    extra: list[str] | None = None,
) -> list[str]:
    """Renderiza un símbolo: título, firma, descripción, secciones y fuente."""
    lines = [
        f"{'#' * level} `{title}` {{ #{anchor} }}",
        "",
        "```python",
        code,
        "```",
        "",
    ]
    body, sections = _split_sections(doc)
    if body:
        lines += [_clean(body), ""]
    lines += extra or []
    for key, text in sections:
        lines += _render_section(key, text)
    lines += [f"[Código fuente]({url}){{ .acodo-source }}", ""]
    return lines


def _enum_members(node: ast.ClassDef) -> list[str]:
    """Nombres de los miembros públicos de una enumeración."""
    names: list[str] = []
    for item in node.body:
        if isinstance(item, ast.Assign):
            names.extend(
                t.id
                for t in item.targets
                if isinstance(t, ast.Name) and _is_public(t.id)
            )
        elif (
            isinstance(item, ast.AnnAssign)
            and isinstance(item.target, ast.Name)
            and _is_public(item.target.id)
        ):
            names.append(item.target.id)
    return names


def _render_method(
    path: Path,
    class_name: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[str]:
    """Renderiza un método público, el constructor o una propiedad."""
    doc = ast.get_docstring(node) or ""
    if node.name == "__init__":
        params = _parameters(node.args)[1:]
        code = _wrap(class_name, params)
        anchor = f"{class_name.lower()}-init"
    elif _decorator_names(node) & PROPERTY_DECORATORS:
        returns = f": {ast.unparse(node.returns)}" if node.returns else ""
        code = f"{node.name}{returns}"
        anchor = f"{class_name.lower()}-{node.name}"
    else:
        code = _signature(node, method=True)
        anchor = f"{class_name.lower()}-{node.name}"
    return _render_symbol(
        level=3,
        title=f"{class_name}.{node.name}",
        anchor=anchor,
        code=code,
        doc=doc,
        url=_source_url(path, node.lineno),
    )


def _render_class(path: Path, node: ast.ClassDef) -> list[str]:
    """Renderiza una clase pública con sus métodos."""
    bases = [ast.unparse(base) for base in node.bases]
    code = f"class {node.name}" + (f"({', '.join(bases)})" if bases else "")
    extra: list[str] = []
    if ENUM_BASES & {base.rsplit(".", 1)[-1] for base in bases}:
        members = ", ".join(f"`{name}`" for name in _enum_members(node))
        extra = ["**Miembros**", "", members, ""]
    lines = _render_symbol(
        level=2,
        title=node.name,
        anchor=node.name.lower(),
        code=code,
        doc=ast.get_docstring(node) or "",
        url=_source_url(path, node.lineno),
        extra=extra,
    )
    for item in node.body:
        if isinstance(item, FUNCTION_TYPES) and (
            item.name == "__init__" or _is_public(item.name)
        ):
            lines += _render_method(path, node.name, item)
    return lines


def _render_module(path: Path, dotted: str, exported: set[str]) -> list[str]:
    """Renderiza la página de un módulo."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    doc = ast.get_docstring(tree) or ""
    entries: list[Entry] = []
    blocks: list[str] = []
    overloads: dict[str, list[str]] = {}

    for node in tree.body:
        if isinstance(node, FUNCTION_TYPES) and _is_public(node.name):
            signature = _signature(node)
            if "overload" in _decorator_names(node):
                overloads.setdefault(node.name, []).append(signature)
                continue
            fn_doc = ast.get_docstring(node) or ""
            entries.append(Entry(node.name, node.name, _summary(fn_doc)))
            blocks += _render_symbol(
                level=2,
                title=node.name,
                anchor=node.name,
                code="\n\n".join(overloads.pop(node.name, [signature])),
                doc=fn_doc,
                url=_source_url(path, node.lineno),
            )
        elif isinstance(node, ast.ClassDef) and _is_public(node.name):
            cls_doc = ast.get_docstring(node) or ""
            entries.append(Entry(node.name.lower(), node.name, _summary(cls_doc)))
            blocks += _render_class(path, node)

    lines = [f"# {dotted}", ""]
    if doc:
        lines += [_clean(doc), ""]
    package = dotted.rsplit(".", 1)[0]
    if entries and all(entry.title in exported for entry in entries):
        lines += [f"Todo lo documentado aquí se importa desde `{package}`.", ""]
    return lines + blocks


# -----------------------------------------------------------------------------
# Páginas de paquete y generación
# -----------------------------------------------------------------------------


def _reexports(init: Path) -> set[str]:
    """Nombres reexportados con alias redundante (`from .x import f as f`)."""
    tree = ast.parse(init.read_text(encoding="utf-8"), filename=str(init))
    return {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if alias.asname == alias.name
    }


def _module_doc(path: Path) -> str:
    """Docstring de un módulo, o cadena vacía."""
    return ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""


def _write(path: Path, lines: list[str]) -> None:
    """Escribe un fichero Markdown en UTF-8 con saltos de línea LF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines).rstrip() + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def _generate_subpackage(directory: Path) -> tuple[str, str, int]:
    """Genera las páginas de un subpaquete y devuelve (nombre, resumen, páginas)."""
    dotted = f"{PACKAGE}.{directory.name}"
    init = directory / "__init__.py"
    exported = _reexports(init)
    modules = sorted(
        path
        for path in directory.glob("*.py")
        if path.name != "__init__.py" and _is_public(path.name)
    )

    doc = _module_doc(init)
    index = [f"# {dotted}", "", _clean(doc), "", "## Módulos", ""]
    for module in modules:
        summary = _summary(_module_doc(module))
        index.append(
            f"- [`{dotted}.{module.stem}`]({module.stem}.md)"
            + (f": {summary}" if summary else "")
        )
        _write(
            OUTPUT / directory.name / f"{module.stem}.md",
            _render_module(module, f"{dotted}.{module.stem}", exported),
        )
    _write(OUTPUT / directory.name / "index.md", index)
    return dotted, _summary(doc), len(modules) + 1


def main() -> int:
    """Regenera `docs/api/` y devuelve el código de salida del proceso."""
    package_dir = SOURCE / PACKAGE
    if not package_dir.is_dir():
        print(f"No se encontró el paquete en {package_dir}.", file=sys.stderr)
        return 1

    project = tomllib.loads((FRAMEWORK / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]

    shutil.rmtree(OUTPUT, ignore_errors=True)
    subpackages = sorted(
        path.parent
        for path in package_dir.glob("*/__init__.py")
        if _is_public(path.parent.name)
    )
    pages = 1
    index = [
        "# Referencia de la API",
        "",
        f"Generada automáticamente a partir de los docstrings de `acodo-framework` "
        f"{version} con `scripts/gen-api.py`. No se edita a mano.",
        "",
        "## Paquetes",
        "",
    ]
    for directory in subpackages:
        dotted, summary, count = _generate_subpackage(directory)
        pages += count
        index.append(
            f"- [`{dotted}`]({directory.name}/index.md)"
            + (f": {summary}" if summary else "")
        )
    _write(OUTPUT / "index.md", index)

    print(f"API generada: {pages} páginas en {OUTPUT.relative_to(ROOT).as_posix()}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
