"""Diagnóstico del entorno y de la configuración del proyecto.

Comprueba lo imprescindible (versión de Python, ruff, ty, pytest, directorios
de código y tests) y avisa de lo opcional (uv, pytest-cov, PyInstaller,
`.local/` en `.gitignore`, configuración de la GitHub App). Sale con código 1
si falla algo imprescindible.

Uso:
    uv run acodo doctor
"""

import importlib.util
import re
import shutil
import sys
from pathlib import Path

import typer
from rich.table import Table

from acodo_cli.commands_service import console, default_gh_config_file, get_config
from acodo_cli.models import AcodoConfig, DoctorResult, Status

_CLAUSE_RE = re.compile(r"\s*(>=|<=|==|!=|>|<)\s*(\d+(?:\.\d+)*)\s*$")
_ICONS = {
    Status.OK: "[ok]✓ OK[/]",
    Status.WARN: "[warning]! aviso[/]",
    Status.FAIL: "[error]✗ falla[/]",
}


def satisfies(version: tuple[int, ...], spec: str) -> bool | None:
    """Comprueba `version` contra un especificador como `>=3.13` o `>=3.12,<3.15`.

    Compara solo tantos componentes como indique el especificador.

    Args:
        version: Versión actual, p. ej. `(3, 13, 1)`.
        spec: Especificador de versión separado por comas.

    Returns:
        `True` o `False` según se cumpla; `None` si no se puede interpretar.

    Examples:
        >>> satisfies((3, 13, 1), ">=3.13")
        True
        >>> satisfies((3, 12, 4), ">=3.13")
        False
    """
    for clause in spec.split(","):
        match = _CLAUSE_RE.match(clause)
        if match is None:
            return None
        operator, raw = match.groups()
        wanted = tuple(int(part) for part in raw.split("."))
        current = version[: len(wanted)]
        ok = {
            ">=": current >= wanted,
            "<=": current <= wanted,
            ">": current > wanted,
            "<": current < wanted,
            "==": current == wanted,
            "!=": current != wanted,
        }[operator]
        if not ok:
            return False
    return True


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _check_python(cfg: AcodoConfig) -> DoctorResult:
    version = sys.version_info[:3]
    shown = ".".join(str(n) for n in version)
    result = satisfies(version, cfg.python_version)
    if result is None:
        return DoctorResult(
            "Python",
            Status.FAIL,
            f"No se entiende python-version: {cfg.python_version}",
        )
    status = Status.OK if result else Status.FAIL
    return DoctorResult("Python", status, f"{shown} (se espera {cfg.python_version})")


def _check_module(name: str, label: str, *, required: bool, hint: str) -> DoctorResult:
    if _has_module(name):
        return DoctorResult(label, Status.OK)
    return DoctorResult(label, Status.FAIL if required else Status.WARN, hint)


def _check_dir(label: str, path: Path, root: Path) -> DoctorResult:
    relative = path.relative_to(root).as_posix()
    if path.is_dir():
        return DoctorResult(label, Status.OK, relative)
    return DoctorResult(label, Status.FAIL, f"No existe {relative}")


def _check_uv() -> DoctorResult:
    if shutil.which("uv"):
        return DoctorResult("uv", Status.OK)
    return DoctorResult("uv", Status.WARN, "Necesario para `acodo api`")


def _check_gitignore(root: Path) -> DoctorResult:
    gitignore = root / ".gitignore"
    lines = (
        gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    )
    if any(line.strip().strip("/") == ".local" for line in lines):
        return DoctorResult(".local/ ignorado", Status.OK)
    return DoctorResult(
        ".local/ ignorado", Status.WARN, "Añádelo a .gitignore (`acodo init`)"
    )


def _check_gh_config(root: Path) -> DoctorResult:
    path = default_gh_config_file(root)
    if path.is_file():
        return DoctorResult(
            "Config GitHub App", Status.OK, path.relative_to(root).as_posix()
        )
    return DoctorResult(
        "Config GitHub App", Status.WARN, "Solo si usas gh-token/gh-check"
    )


def run_checks(cfg: AcodoConfig) -> list[DoctorResult]:
    """Ejecuta todas las comprobaciones de `doctor`."""
    return [
        _check_python(cfg),
        _check_module("ruff", "ruff", required=True, hint="Falta: uv add --dev ruff"),
        _check_module("ty", "ty", required=True, hint="Falta: uv add --dev ty"),
        _check_module(
            "pytest", "pytest", required=True, hint="Falta: uv add --dev pytest"
        ),
        _check_dir("Código fuente", cfg.src, cfg.root),
        _check_dir("Tests", cfg.tests, cfg.root),
        _check_uv(),
        _check_module(
            "pytest_cov",
            "pytest-cov",
            required=False,
            hint="Necesario para `check --cov`",
        ),
        _check_module(
            "PyInstaller",
            "PyInstaller",
            required=False,
            hint="Necesario para `acodo build`",
        ),
        _check_gitignore(cfg.root),
        _check_gh_config(cfg.root),
    ]


def main() -> None:
    """Comprueba que el entorno y la configuración están listos."""
    cfg = get_config()
    results = run_checks(cfg)

    table = Table(
        title=f"Diagnóstico de {cfg.project_name}",
        title_style="title",
        border_style="border",
    )
    table.add_column("Comprobación", style="label")
    table.add_column("Estado")
    table.add_column("Detalle", overflow="fold")
    for result in results:
        table.add_row(result.name, _ICONS[result.status], result.detail)
    console.print(table)

    if any(result.status is Status.FAIL for result in results):
        raise typer.Exit(code=1)
