"""CLI principal de `acodo-cli`.

Reúne las herramientas de desarrollo de un proyecto Python: comprobaciones de
calidad, documentación de la API, copias de seguridad, conteo de líneas y
tokens de una GitHub App. Los comandos no reciben argumentos: se ejecutan desde
el directorio de un proyecto y leen su configuración de `acodo.toml`. Cada
comando solo llama a su script de `acodo_cli.commands`.

Instalado globalmente, solo expone `init`, que ofrece clonar la plantilla.

Uso:
    uv run acodo --help
    uv run acodo init
    uv run acodo doctor
    uv run acodo check
    uv run python -m acodo_cli gh-token
"""

import sys
from collections.abc import Callable
from pathlib import Path

import typer

from acodo_cli.commands import (
    api,
    backup,
    check,
    clean,
    code_count,
    doctor,
    gh_check,
    gh_token,
    init,
    todo,
)
from acodo_cli.commands_service import is_global_install
from acodo_cli.theme import apply_typer_styles
from acodo_cli.typer_options import VersionOption

apply_typer_styles()


def api_() -> None:
    """Genera la documentación de la API a partir de los docstrings."""
    api.main()


def backup_() -> None:
    """Limpia las cachés y crea una copia de seguridad."""
    backup.main()


def check_() -> None:
    """Ejecuta format, lint, types y tests."""
    check.main()


def clean_() -> None:
    """Elimina cachés y artefactos generados, previa confirmación."""
    clean.main()


def code_count_() -> None:
    """Cuenta las líneas de código y de docstrings."""
    code_count.main()


def doctor_() -> None:
    """Comprueba que el entorno y la configuración están listos."""
    doctor.main()


def format_() -> None:
    """Formatea el código (ruff format)."""
    check.run_steps(("format",))


def gh_check_() -> None:
    """Comprueba el acceso al repositorio configurado."""
    gh_check.main()


def gh_token_() -> None:
    """Genera un token de instalación para la GitHub App."""
    gh_token.main()


def init_() -> None:
    """Crea el acodo.toml por defecto en el directorio actual."""
    init.main()


def lint_() -> None:
    """Revisa y autocorrige el lint (ruff check --fix)."""
    check.run_steps(("lint",))


def tests_() -> None:
    """Ejecuta las pruebas (pytest)."""
    check.run_steps(("tests",))


def tests_cov_() -> None:
    """Ejecuta las pruebas con cobertura (requiere pytest-cov)."""
    check.run_steps(("tests-cov",))


def todo_() -> None:
    """Lista los marcadores TODO, FIXME, XXX y HACK del código."""
    todo.main()


def types_() -> None:
    """Comprueba el tipado (ty check)."""
    check.run_steps(("types",))


def _is_global() -> bool:
    return is_global_install(Path(sys.prefix), Path(sys.base_prefix))


COMMANDS: dict[str, Callable[[], None]] = {
    "api": api_,
    "backup": backup_,
    "check": check_,
    "clean": clean_,
    "code-count": code_count_,
    "doctor": doctor_,
    "format": format_,
    "gh-check": gh_check_,
    "gh-token": gh_token_,
    "init": init_,
    "lint": lint_,
    "tests": tests_,
    "tests-cov": tests_cov_,
    "todo": todo_,
    "types": types_,
}
"""Comandos de la CLI: nombre y función que llama a su script."""


def _main(ctx: typer.Context, version: VersionOption = False) -> None:
    """Comando por defecto: sin subcomando muestra la ayuda (u ofrece inicializar)."""
    if ctx.invoked_subcommand is not None:
        return
    in_project_env = not _is_global()
    if (
        in_project_env
        and not init.is_initialized(Path.cwd())
        and typer.confirm(
            "Este directorio no tiene acodo.toml. ¿Inicializar el proyecto?"
        )
    ):
        init.main()
        return
    help_text = ctx.get_help()
    if help_text:
        typer.echo(help_text)


def build_app() -> typer.Typer:
    """Crea la aplicación; en una instalación global solo registra `init`.

    El resto de comandos usan `ruff`, `ty` y `pytest` del entorno del proyecto,
    que no existen fuera de él.
    """
    app = typer.Typer(
        add_completion=False,
        help="Herramientas de desarrollo del proyecto.",
    )
    names = ("init",) if _is_global() else tuple(COMMANDS)
    for name in names:
        app.command(name)(COMMANDS[name])
    app.callback(invoke_without_command=True)(_main)
    return app


app = build_app()
