"""Comprueba el acceso de una GitHub App al repositorio configurado.

Usa el JSON indicado en `[github_app]` de `acodo.toml`, igual que `gh-token`.

Uso:
    uv run acodo gh-check
"""

import typer
from rich.markup import escape
from rich.table import Table

from acodo_cli.commands_service import (
    console,
    err_console,
    generate_token,
    get_config,
    gh_config_path,
    load_gh_config,
    normalize_repo,
    request,
    resolve_api_url,
)


def main() -> None:
    """Comprueba el acceso al repositorio configurado."""
    file = gh_config_path(get_config())
    cfg = load_gh_config(file)

    try:
        repo_slug = normalize_repo(str(cfg["repository"]))
        body = generate_token(cfg, file)
        token = body["token"]
        api_url = resolve_api_url(cfg)
        info = request("GET", f"{api_url}/repos/{repo_slug}", token)
    except ValueError as exc:
        err_console.print(f"[error]Error:[/] {escape(str(exc))}")
        raise typer.Exit(code=1) from None

    perms = info.get("permissions") or {}

    def mark(value: bool | None) -> str:
        if value is True:
            return "[ok]✓[/]"
        if value is False:
            return "[error]✗[/]"
        return "[muted]·[/]"

    vis = "privado" if info.get("private") else "público"

    table = Table(
        title=f"Acceso a {info.get('full_name', repo_slug)}",
        show_header=False,
        title_style="title",
    )
    table.add_column("Campo", style="label", no_wrap=True)
    table.add_column("Valor")
    table.add_row("Repositorio", f"{info.get('full_name', repo_slug)} ({vis})")
    table.add_row("URL", info.get("html_url", "-"))
    table.add_row("Rama por defecto", info.get("default_branch", "-"))
    table.add_row(
        "Permisos",
        f"pull={mark(perms.get('pull'))}  "
        f"push={mark(perms.get('push'))}  "
        f"admin={mark(perms.get('admin'))}",
    )
    console.print(table)
