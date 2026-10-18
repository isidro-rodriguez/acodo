"""Prepara un proyecto para usar `acodo`.

Añade `[tool.acodo-cli]` al `pyproject.toml` (con los valores por defecto),
crea la plantilla `.local/gh_app.json` y asegura que `.local/` está en
`.gitignore`. Nunca sobrescribe lo que ya existe.

Uso:
    uv run acodo init
"""

import json
import tomllib

from rich.markup import escape

from acodo_cli.commands_service import (
    GH_CONFIG_TEMPLATE,
    console,
    default_gh_config_file,
    get_config,
)
from acodo_cli.config import (
    DEFAULT_PYTHON_VERSION,
    DEFAULT_SRC_DIR,
    DEFAULT_TEST_DIR,
    PYPROJECT,
    SECTION,
)

CONFIG_BLOCK = f"""[tool.{SECTION}]
src-dir = "{DEFAULT_SRC_DIR}"
test-dir = "{DEFAULT_TEST_DIR}"
python-version = "{DEFAULT_PYTHON_VERSION}"
"""
"""Sección que se añade al `pyproject.toml`."""


def _done(message: str) -> None:
    console.print(f"[ok]✓[/] {escape(message)}")


def _skipped(message: str) -> None:
    console.print(f"[muted]·[/] {escape(message)}")


def main() -> None:
    """Crea la configuración inicial de `acodo` en el proyecto."""
    cfg = get_config()
    root = cfg.root

    pyproject = root / PYPROJECT
    text = pyproject.read_text(encoding="utf-8")
    if SECTION in tomllib.loads(text).get("tool", {}):
        _skipped(f"[tool.{SECTION}] ya existe en {PYPROJECT}")
    else:
        separator = "" if not text or text.endswith("\n\n") else "\n"
        if text and not text.endswith("\n"):
            separator = "\n\n"
        pyproject.write_text(text + separator + CONFIG_BLOCK, encoding="utf-8")
        _done(f"Añadida [tool.{SECTION}] a {PYPROJECT}")

    gh_config = default_gh_config_file(root)
    if gh_config.exists():
        _skipped(f"{gh_config.relative_to(root).as_posix()} ya existe")
    else:
        gh_config.parent.mkdir(parents=True, exist_ok=True)
        gh_config.write_text(
            json.dumps(GH_CONFIG_TEMPLATE, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        _done(f"Creada la plantilla {gh_config.relative_to(root).as_posix()}")

    gitignore = root / ".gitignore"
    lines = (
        gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    )
    if any(line.strip().strip("/") == ".local" for line in lines):
        _skipped(".local/ ya está en .gitignore")
    else:
        lines.append(".local/")
        gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _done("Añadido .local/ a .gitignore")
