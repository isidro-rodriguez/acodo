"""Comprobaciones de calidad del proyecto.

Ejecuta `ruff format`, `ruff check --fix`, `ty check` y `pytest` sin detenerse
en el primer fallo, muestra un resumen final y sale con código 1 si alguna falla.

Con `--ci` solo verifica (sin `--fix` ni reescribir ficheros) y con `--cov`
mide la cobertura de pytest.

Uso:
    uv run acodo check
    uv run acodo check --lint --types
    uv run acodo check --ci --cov
"""

import sys
import time

import typer
from rich.table import Table

from acodo_cli.commands_service import console, get_config, run
from acodo_cli.models import AcodoConfig, Step
from acodo_cli.typer_options import (
    CiOption,
    CovOption,
    FormatOption,
    LintOption,
    TestOption,
    TypesOption,
)


def _build_steps(cfg: AcodoConfig, *, ci: bool, cov: bool) -> dict[str, Step]:
    """Comprobaciones disponibles, en el orden en que se ejecutan."""
    python = (sys.executable, "-m")
    format_args = ("--check",) if ci else ()
    lint_args = () if ci else ("--fix",)
    test_args = (f"--cov={cfg.src_dir}", "--cov-report=term-missing") if cov else ()
    return {
        "format": Step("ruff format", (*python, "ruff", "format", *format_args)),
        "lint": Step("ruff check", (*python, "ruff", "check", *lint_args)),
        "types": Step("ty check", (*python, "ty", "check")),
        "tests": Step("pytest", (*python, "pytest", *test_args)),
    }


def main(
    format_: FormatOption = False,
    lint: LintOption = False,
    types: TypesOption = False,
    tests: TestOption = False,
    ci: CiOption = False,
    cov: CovOption = False,
) -> None:
    """Ejecuta las comprobaciones de calidad; sin opciones, todas."""
    cfg = get_config()
    steps = _build_steps(cfg, ci=ci, cov=cov)
    flags = {"format": format_, "lint": lint, "types": types, "tests": tests}
    selected = [key for key, enabled in flags.items() if enabled] or list(steps)

    results: list[tuple[Step, int, float]] = []
    for key in selected:
        step = steps[key]
        console.rule(f"[title]{step.name}[/]")
        start = time.perf_counter()
        code = run(step.command, cfg.root)
        results.append((step, code, time.perf_counter() - start))

    table = Table(title="Resultado", title_style="title", border_style="border")
    table.add_column("Comprobación", style="label")
    table.add_column("Estado")
    table.add_column("Tiempo", justify="right")
    for step, code, seconds in results:
        status = "[ok]✓ OK[/]" if code == 0 else f"[error]✗ código {code}[/]"
        table.add_row(step.name, status, f"{seconds:.1f} s")
    console.print(table)

    if any(code != 0 for _, code, _ in results):
        raise typer.Exit(code=1)
