"""Conteo de líneas de código y docstrings.

Cuenta las líneas efectivas separando el código fuente de los docstrings,
excluyendo líneas en blanco y comentarios ordinarios (#).

Uso:
    uv run acodo code-count
    uv run acodo code-count --verbose
    uv run acodo code-count --tree
    uv run acodo code-count --verbose --tree
    uv run acodo code-count --json
"""

import ast
import json
from collections.abc import Iterator
from pathlib import Path

import typer
from rich.table import Table
from rich.tree import Tree

from acodo_cli.commands_service import console, get_config
from acodo_cli.models import AcodoConfig, Category, LineStats
from acodo_cli.typer_options import JsonOption, TreeOption, VerboseOption

CODE_EXTENSIONS = {".py"}


def _extract_docstring_range(node: ast.AST) -> range | None:
    """Extrae el rango de líneas (1-indexed) de un docstring si el nodo lo posee."""
    if not isinstance(
        node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    ):
        return None

    if not node.body:
        return None

    first_stmt = node.body[0]
    if not isinstance(first_stmt, ast.Expr):
        return None

    if isinstance(first_stmt.value, ast.Constant) and isinstance(
        first_stmt.value.value, str
    ):
        start = first_stmt.lineno
        end = first_stmt.end_lineno or start
        return range(start, end + 1)

    return None


def _get_docstring_lines(content: str) -> set[int]:
    """Obtiene los números de línea (1-indexed) pertenecientes a docstrings."""
    doc_lines: set[int] = set()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return doc_lines

    for node in ast.walk(tree):
        line_range = _extract_docstring_range(node)
        if line_range:
            doc_lines.update(line_range)

    return doc_lines


def _count_file_lines(path: Path) -> LineStats:
    """Cuenta por separado las líneas de código y de docstrings."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return LineStats()

    doc_line_numbers = (
        _get_docstring_lines(content) if path.suffix.lower() == ".py" else set()
    )

    code_lines = 0
    docstring_lines = 0

    for line_no, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if line_no in doc_line_numbers:
            docstring_lines += 1
        else:
            code_lines += 1

    return LineStats(code=code_lines, docstrings=docstring_lines)


def _files_with_exts(base: Path, extensions: set[str]) -> Iterator[Path]:
    if not base.is_dir():
        return
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix.lower() in extensions:
            yield path


def _py_files(base: Path) -> Iterator[Path]:
    return _files_with_exts(base, {".py"})


def build_categories(cfg: AcodoConfig) -> list[Category]:
    """Construye las categorías de conteo con métricas desglosadas."""
    definitions = {
        "scripts": cfg.root / "scripts",
        "tests": cfg.tests,
        "src": cfg.src,
    }
    if cfg.tests == cfg.src:  # Workspace: los tests viven dentro del código.
        del definitions["tests"]

    return [
        Category(
            name=name,
            files=[(path, _count_file_lines(path)) for path in _py_files(base)],
        )
        for name, base in definitions.items()
    ]


def _print_verbose_tables(categories: list[Category], root: Path) -> None:
    """Imprime el informe usando tablas de Rich."""
    for category in categories:
        cat_totals = category.totals
        table = Table(
            title=f"{category.name} ({len(category.files)} ficheros)",
            title_style="title",
            show_lines=True,
            width=80,
            border_style="border",
        )
        table.add_column("Ruta", overflow="fold")
        table.add_column("Código", justify="right", style="lines.code")
        table.add_column("Docstr", justify="right", style="lines.docs")
        table.add_column("Total", justify="right", style="lines.total")

        sorted_files = sorted(category.files, key=lambda item: -item[1].total)
        for path, stats in sorted_files:
            relative = path.relative_to(root)
            table.add_row(
                str(relative),
                str(stats.code),
                str(stats.docstrings),
                str(stats.total),
            )

        table.add_row(
            "[total]TOTAL[/]",
            f"[lines.code]{cat_totals.code}[/]",
            f"[lines.docs]{cat_totals.docstrings}[/]",
            f"[lines.total]{cat_totals.total}[/]",
        )
        console.print(table)
        console.print()


def _print_summary_table(categories: list[Category]) -> None:
    """Imprime la tabla resumen global."""
    grand_totals = LineStats()
    total_files = 0
    for category in categories:
        grand_totals += category.totals
        total_files += len(category.files)

    table = Table(
        title="Resumen por directorio",
        title_style="title",
        width=80,
        border_style="border",
    )
    table.add_column("Categoría", style="label")
    table.add_column("Código", justify="right", style="lines.code")
    table.add_column("Docstr", justify="right", style="lines.docs")
    table.add_column("Total", justify="right", style="lines.total")
    table.add_column("Ficheros", justify="right")

    for category in categories:
        t = category.totals
        table.add_row(
            category.name,
            str(t.code),
            str(t.docstrings),
            str(t.total),
            str(len(category.files)),
        )

    table.add_row(
        "[total]TOTAL[/]",
        f"[lines.code]{grand_totals.code}[/]",
        f"[lines.docs]{grand_totals.docstrings}[/]",
        f"[lines.total]{grand_totals.total}[/]",
        f"[lines.total]{total_files}[/]",
    )

    console.print(table)
    console.print(
        f"[muted]{total_files} ficheros procesados: "
        f"{grand_totals.code} líneas de código, "
        f"{grand_totals.docstrings} líneas de docstrings "
        f"({grand_totals.total} líneas totales).[/]"
    )


def _print_tree(categories: list[Category], root: Path, verbose: bool) -> None:
    """Imprime el informe usando árbol de Rich."""
    root_tree = Tree("code_count", style="title", guide_style="border")

    grand_totals = LineStats()
    total_files = 0

    for category in categories:
        cat_totals = category.totals
        grand_totals += cat_totals
        total_files += len(category.files)

        cat_branch = root_tree.add(
            f"[label]{category.name}[/]/"
            f"([lines.code]{cat_totals.code}[/]/"
            f"[lines.docs]{cat_totals.docstrings}[/]/"
            f"[lines.total]{cat_totals.total}[/], {len(category.files)} ficheros)"
        )

        if verbose:
            sorted_files = sorted(category.files, key=lambda item: -item[1].total)
            for path, stats in sorted_files:
                relative = path.relative_to(root)
                cat_branch.add(
                    f"{relative} ([lines.code]{stats.code}[/]/"
                    f"[lines.docs]{stats.docstrings}[/]/"
                    f"[lines.total]{stats.total}[/])"
                )

    root_tree.add(
        f"[total]TOTAL[/] "
        f"([lines.code]{grand_totals.code} l. código[/], "
        f"[lines.docs]{grand_totals.docstrings} l. docstrings[/], "
        f"[lines.total]{grand_totals.total} l. totales[/], {total_files} ficheros)"
    )

    console.print(root_tree)


def _to_json(categories: list[Category], root: Path) -> str:
    """Serializa el informe como JSON (rutas relativas con `/`)."""
    grand_totals = LineStats()
    total_files = 0
    payload_categories = []
    for category in categories:
        totals = category.totals
        grand_totals += totals
        total_files += len(category.files)
        payload_categories.append(
            {
                "name": category.name,
                "code": totals.code,
                "docstrings": totals.docstrings,
                "total": totals.total,
                "files": [
                    {
                        "path": path.relative_to(root).as_posix(),
                        "code": stats.code,
                        "docstrings": stats.docstrings,
                        "total": stats.total,
                    }
                    for path, stats in category.files
                ],
            }
        )
    payload = {
        "categories": payload_categories,
        "total": {
            "code": grand_totals.code,
            "docstrings": grand_totals.docstrings,
            "total": grand_totals.total,
            "files": total_files,
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def main(
    verbose: VerboseOption = False,
    tree: TreeOption = False,
    as_json: JsonOption = False,
) -> None:
    """Muestra el informe de conteo de líneas por categorías."""
    cfg = get_config()
    categories = build_categories(cfg)

    if as_json:
        typer.echo(_to_json(categories, cfg.root))
        return

    if tree:
        _print_tree(categories, cfg.root, verbose)
    else:
        if verbose:
            _print_verbose_tables(categories, cfg.root)
        _print_summary_table(categories)
