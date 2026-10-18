"""CLI principal de `acodo-cli`.

Reúne las herramientas de desarrollo de un proyecto Python: comprobaciones de
calidad, documentación de la API, copias de seguridad, compilado con PyInstaller,
conteo de líneas y tokens de una GitHub App. Se ejecuta desde el directorio de un
proyecto y lee su configuración de `[tool.acodo-cli]` en el `pyproject.toml`.

Uso:
    uv run acodo --help
    uv run acodo init
    uv run acodo doctor
    uv run acodo check --ci --cov
    uv run acodo backup --archiver tar.gz
    uv run python -m acodo_cli gh-token
"""

import sys
from pathlib import Path

import typer

from acodo_cli.banner import show_banner
from acodo_cli.commands import (
    api,
    backup,
    build,
    check,
    clean,
    code_count,
    doctor,
    gh_check,
    gh_token,
    init,
    todo,
)
from acodo_cli.commands_service import fail, is_global_install
from acodo_cli.theme import apply_typer_styles
from acodo_cli.typer_options import VersionOption

apply_typer_styles()

app = typer.Typer(
    add_completion=False,
    help="Herramientas de desarrollo del proyecto.",
)

app.command("api")(api.main)
app.command("backup")(backup.main)
app.command("build")(build.main)
app.command("check")(check.main)
app.command("clean")(clean.main)
app.command("code-count")(code_count.main)
app.command("doctor")(doctor.main)
app.command("gh-check")(gh_check.main)
app.command("gh-token")(gh_token.main)
app.command("init")(init.main)
app.command("todo")(todo.main)


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context, version: VersionOption = False) -> None:
    """Comando por defecto: sin subcomando muestra el banner y la ayuda."""
    if ctx.invoked_subcommand is None:
        show_banner()
        help_text = ctx.get_help()
        if help_text:
            typer.echo(help_text)
        return
    if is_global_install(Path(sys.prefix), Path(sys.base_prefix)):
        fail(
            "acodo-cli no admite instalarse como herramienta global. "
            "Añádelo al proyecto con `uv add --dev acodo-cli` "
            "y ejecútalo con `uv run acodo`."
        )
