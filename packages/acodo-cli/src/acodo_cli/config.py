"""Carga de la configuración desde el `pyproject.toml` del proyecto consumidor."""

import tomllib
from pathlib import Path
from typing import Any

from acodo_cli.models import AcodoConfig

PYPROJECT = "pyproject.toml"
SECTION = "acodo-cli"
"""Tabla de `pyproject.toml` que se lee: `[tool.acodo-cli]`."""

DEFAULT_SRC_DIR = "src"
DEFAULT_TEST_DIR = "tests"
DEFAULT_PYTHON_VERSION = ">=3.13"


class ConfigError(Exception):
    """No se pudo localizar, leer o interpretar la configuración del proyecto."""


def find_pyproject(start: Path) -> Path:
    """Busca `pyproject.toml` en `start` y sus directorios superiores.

    Args:
        start: Directorio desde el que empezar a buscar.

    Returns:
        Ruta del primer `pyproject.toml` encontrado.

    Raises:
        ConfigError: Si no hay ningún `pyproject.toml`.
    """
    for directory in (start, *start.parents):
        candidate = directory / PYPROJECT
        if candidate.is_file():
            return candidate
    raise ConfigError(f"No se encontró {PYPROJECT} en {start} ni en sus superiores.")


def _read_toml(path: Path) -> dict[str, Any]:
    """Lee un fichero TOML y traduce sus errores a `ConfigError`."""
    try:
        with path.open("rb") as file:
            return tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path} no es un TOML válido: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"No se pudo leer {path}: {exc.strerror}") from exc


def _get_str(section: dict[str, Any], key: str, default: str) -> str:
    """Devuelve `section[key]` como cadena no vacía, o `default` si falta."""
    value = section.get(key, default)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"[tool.{SECTION}] «{key}» debe ser una cadena no vacía.")
    return value


def load_config(start: Path | None = None) -> AcodoConfig:
    """Carga la configuración del proyecto desde su `pyproject.toml`.

    Lee la tabla `[tool.acodo-cli]` (claves `src-dir`, `test-dir` y
    `python-version`); lo que falte toma su valor por defecto.

    Args:
        start: Directorio desde el que buscar `pyproject.toml`. Por defecto,
            el directorio actual.

    Returns:
        Configuración resuelta del proyecto.

    Raises:
        ConfigError: Si falta el `pyproject.toml`, no es TOML válido o algún
            valor de `[tool.acodo-cli]` es incorrecto.
    """
    pyproject = find_pyproject((start or Path.cwd()).resolve())
    data = _read_toml(pyproject)

    tool = data.get("tool")
    section = tool.get(SECTION, {}) if isinstance(tool, dict) else {}
    if not isinstance(section, dict):
        raise ConfigError(f"[tool.{SECTION}] debe ser una tabla.")

    project = data.get("project")
    name = project.get("name") if isinstance(project, dict) else None

    return AcodoConfig(
        root=pyproject.parent,
        project_name=name if isinstance(name, str) and name else pyproject.parent.name,
        src_dir=_get_str(section, "src-dir", DEFAULT_SRC_DIR),
        test_dir=_get_str(section, "test-dir", DEFAULT_TEST_DIR),
        python_version=_get_str(section, "python-version", DEFAULT_PYTHON_VERSION),
    )
