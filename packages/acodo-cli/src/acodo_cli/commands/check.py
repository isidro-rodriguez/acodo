"""Comprobaciones de calidad del proyecto.

Cada comprobación lee de `acodo.toml` las rutas de su sección (`[format]`,
`[lint]`, `[types]` y `[test]`, sumadas a `[all]`). Las comprobaciones se
ejecutan sin detenerse en el primer fallo, se muestra un resumen final y se
sale con código 1 si alguna falla.

Uso:
    uv run acodo format
    uv run acodo lint
    uv run acodo types
    uv run acodo tests
    uv run acodo tests-cov
    uv run acodo check
"""

import sys
import time
from collections.abc import Callable, Sequence

import typer
from rich.table import Table

from acodo_cli.commands_service import console, fail, get_config, run
from acodo_cli.models import AcodoConfig, Step

PYTHON = (sys.executable, "-m")


def _paths(cfg: AcodoConfig, section: str) -> list[str]:
    """Rutas existentes de la sección, relativas a la raíz y con `/`."""
    paths = [path.relative_to(cfg.root).as_posix() for path in cfg.scope_dirs(section)]
    if not paths:
        fail(f"No hay rutas que procesar: revisa `include` en [all] y [{section}].")
    return paths


def _excludes(cfg: AcodoConfig, section: str) -> list[str]:
    """Patrones `exclude` de la sección, sin la barra final."""
    return [pattern.rstrip("/") for pattern in cfg.scopes[section].exclude]


def _flags(option: str, values: Sequence[str]) -> list[str]:
    """Repite `option` por cada valor: `--x a --x b`."""
    return [arg for value in values for arg in (option, value)]


def _format(cfg: AcodoConfig) -> Step:
    excludes = _flags("--extend-exclude", _excludes(cfg, "format"))
    command = (*PYTHON, "ruff", "format", *_paths(cfg, "format"), *excludes)
    return Step("ruff format", command)


def _lint(cfg: AcodoConfig) -> Step:
    excludes = _flags("--extend-exclude", _excludes(cfg, "lint"))
    command = (*PYTHON, "ruff", "check", "--fix", *_paths(cfg, "lint"), *excludes)
    return Step("ruff check", command)


def _types(cfg: AcodoConfig) -> Step:
    excludes = _flags("--exclude", _excludes(cfg, "types"))
    command = (*PYTHON, "ty", "check", *_paths(cfg, "types"), *excludes)
    return Step("ty check", command)


def _pytest_ignores(cfg: AcodoConfig) -> list[str]:
    """`--ignore-glob` por cada patrón `exclude` (pytest compara rutas absolutas)."""
    return [
        f"--ignore-glob={glob}"
        for pattern in _excludes(cfg, "test")
        for glob in (f"*/{pattern}", f"*/{pattern}/*")
    ]


def _tests(cfg: AcodoConfig) -> Step:
    command = (*PYTHON, "pytest", *_paths(cfg, "test"), *_pytest_ignores(cfg))
    return Step("pytest", command)


def _tests_cov(cfg: AcodoConfig) -> Step:
    command = (*_tests(cfg).command, "--cov", "--cov-report=term-missing")
    return Step("pytest (cobertura)", command)


STEPS: dict[str, Callable[[AcodoConfig], Step]] = {
    "format": _format,
    "lint": _lint,
    "types": _types,
    "tests": _tests,
}
"""Comprobaciones de `check`, en el orden en que se ejecutan."""

COVERAGE_STEPS: dict[str, Callable[[AcodoConfig], Step]] = {"tests-cov": _tests_cov}


def run_steps(names: Sequence[str]) -> None:
    """Ejecuta las comprobaciones `names`, imprime el resumen y sale con 1 si falla."""
    available = {**STEPS, **COVERAGE_STEPS}
    cfg = get_config()
    steps = [available[name](cfg) for name in names]

    results: list[tuple[Step, int, float]] = []
    for step in steps:
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


def main() -> None:
    """Ejecuta todas las comprobaciones: format, lint, types y tests."""
    run_steps(tuple(STEPS))
