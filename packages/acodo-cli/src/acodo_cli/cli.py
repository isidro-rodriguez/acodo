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
from pathlib import Path
from typing import Annotated

import typer

from acodo_cli.banner import version_callback
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

apply_typer_styles()

app = typer.Typer(
    add_completion=False,
    help="Herramientas de desarrollo del proyecto.",
)


@app.command(name="api")
def api_() -> None:
    """Genera la documentación de la API a partir de los docstrings."""
    api.main()


@app.command(name="backup")
def backup_() -> None:
    """Limpia las cachés y crea una copia de seguridad."""
    backup.main()


@app.command(name="check", rich_help_panel="Quality check")
def check_() -> None:
    """Ejecuta format, lint, types y tests."""
    check.main()


@app.command(name="clean")
def clean_() -> None:
    """Elimina cachés y artefactos generados, previa confirmación."""
    clean.main()


@app.command(name="code-count")
def code_count_() -> None:
    """Cuenta las líneas de código y de docstrings."""
    code_count.main()


@app.command(name="doctor")
def doctor_() -> None:
    """Comprueba que el entorno y la configuración están listos."""
    doctor.main()


@app.command(name="format", rich_help_panel="Quality check")
def format_() -> None:
    """Formatea el código (ruff format)."""
    check.run_steps(("format",))


@app.command(name="gh-check")
def gh_check_() -> None:
    """Comprueba el acceso al repositorio configurado."""
    gh_check.main()


@app.command(name="gh-token")
def gh_token_() -> None:
    """Genera un token de instalación para la GitHub App."""
    gh_token.main()


@app.command(name="init")
def init_() -> None:
    """Crea el acodo.toml por defecto en el directorio actual."""
    init.main()


@app.command(name="lint", rich_help_panel="Quality check")
def lint_() -> None:
    """Revisa y autocorrige el lint (ruff check --fix)."""
    check.run_steps(("lint",))


@app.command(name="tests", rich_help_panel="Quality check")
def tests_() -> None:
    """Ejecuta las pruebas (pytest)."""
    check.run_steps(("tests",))


@app.command(name="tests-cov", rich_help_panel="Quality check")
def tests_cov_() -> None:
    """Ejecuta las pruebas con cobertura (requiere pytest-cov)."""
    check.run_steps(("tests-cov",))


@app.command(name="todo")
def todo_() -> None:
    """Lista los marcadores TODO, FIXME, XXX y HACK del código."""
    todo.main()


@app.command(name="types", rich_help_panel="Quality check")
def types_() -> None:
    """Comprueba el tipado (ty check)."""
    check.run_steps(("types",))


def _is_global() -> bool:
    return is_global_install(Path(sys.prefix), Path(sys.base_prefix))


@app.callback(invoke_without_command=True)
def _main(
    ctx: typer.Context,
    _version: Annotated[
        bool,
        typer.Option(
            default="--version",
            callback=version_callback,
            is_eager=True,
            help="Muestra la versión de acodo y sale.",
        ),
    ] = False,
) -> None:
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
