"""Carga de la configuración del proyecto desde su `acodo.toml`."""

import tomllib
from importlib.resources import files
from pathlib import Path
from typing import Any

from acodo_cli.models import AcodoConfig, OutputConfig, Scope

ACODO_TOML = "acodo.toml"
PYPROJECT = "pyproject.toml"

SCOPE_SECTIONS = ("format", "lint", "types", "test", "todo", "backup", "api")
"""Secciones que añaden su `include`/`exclude` a los de `[all]`."""

DEFAULT_BACKUP_TARGET = ".local/backup.zip"
DEFAULT_API_TARGET = ".local/api.md"
DEFAULT_GH_CONFIG_FILE = ".local/gh_app.json"


class ConfigError(Exception):
    """No se pudo localizar, leer o interpretar la configuración del proyecto."""


def default_acodo_toml() -> str:
    """Contenido del `acodo.toml` por defecto que copia `acodo init`."""
    return files("acodo_cli").joinpath("resources", ACODO_TOML).read_text("utf-8")


def find_acodo_toml(start: Path) -> Path:
    """Busca `acodo.toml` en `start` y sus directorios superiores.

    Args:
        start: Directorio desde el que empezar a buscar.

    Returns:
        Ruta del primer `acodo.toml` encontrado.

    Raises:
        ConfigError: Si no hay ningún `acodo.toml`.
    """
    for directory in (start, *start.parents):
        candidate = directory / ACODO_TOML
        if candidate.is_file():
            return candidate
    raise ConfigError(
        f"No se encontró {ACODO_TOML} en {start} ni en sus superiores. "
        "Ejecuta `acodo init`."
    )


def _read_toml(path: Path) -> dict[str, Any]:
    """Lee un fichero TOML y traduce sus errores a `ConfigError`."""
    try:
        with path.open("rb") as file:
            return tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path} no es un TOML válido: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"No se pudo leer {path}: {exc.strerror}") from exc


def _table(data: dict[str, Any], name: str) -> dict[str, Any]:
    """Devuelve la tabla `[name]` (vacía si falta)."""
    section = data.get(name, {})
    if not isinstance(section, dict):
        raise ConfigError(f"[{name}] debe ser una tabla.")
    return section


def _get_str_list(section: dict[str, Any], name: str, key: str) -> tuple[str, ...]:
    """Devuelve `section[key]` como tupla de cadenas no vacías (vacía si falta)."""
    value = section.get(key, [])
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ConfigError(f"[{name}] «{key}» debe ser una lista de cadenas no vacías.")
    return tuple(value)


def _get_str(section: dict[str, Any], name: str, key: str, default: str) -> str:
    """Devuelve `section[key]` como cadena no vacía, o `default` si falta."""
    value = section.get(key, default)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"[{name}] «{key}» debe ser una cadena no vacía.")
    return value


def _get_bool(section: dict[str, Any], name: str, key: str, default: bool) -> bool:
    """Devuelve `section[key]` como booleano, o `default` si falta."""
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(f"[{name}] «{key}» debe ser true o false.")
    return value


def _merge(base: tuple[str, ...], extra: tuple[str, ...]) -> tuple[str, ...]:
    """Concatena sin duplicados, conservando el orden."""
    return tuple(dict.fromkeys((*base, *extra)))


def _read_scope(data: dict[str, Any], name: str) -> Scope:
    """Lee `include` y `exclude` de la tabla `[name]`."""
    section = _table(data, name)
    return Scope(
        include=_get_str_list(section, name, "include"),
        exclude=_get_str_list(section, name, "exclude"),
    )


def _read_output(data: dict[str, Any], name: str, default_target: str) -> OutputConfig:
    """Lee `target` y `version_suffix` de la tabla `[name]`."""
    section = _table(data, name)
    return OutputConfig(
        target=_get_str(section, name, "target", default_target),
        version_suffix=_get_bool(section, name, "version_suffix", True),
    )


def _read_project(root: Path) -> dict[str, Any]:
    """Lee `[project]` del `pyproject.toml` de `root`; vacío si no existe."""
    pyproject = root / PYPROJECT
    if not pyproject.is_file():
        return {}
    project = _read_toml(pyproject).get("project")
    return project if isinstance(project, dict) else {}


def load_config(start: Path | None = None) -> AcodoConfig:
    """Carga la configuración del proyecto desde su `acodo.toml`.

    El alcance de cada sección de `SCOPE_SECTIONS` suma sus `include` y
    `exclude` a los de `[all]`; lo que falte toma su valor por defecto.

    Args:
        start: Directorio desde el que buscar `acodo.toml`. Por defecto,
            el directorio actual.

    Returns:
        Configuración resuelta del proyecto.

    Raises:
        ConfigError: Si falta `acodo.toml`, no es TOML válido o algún valor
            es incorrecto.
    """
    path = find_acodo_toml((start or Path.cwd()).resolve())
    data = _read_toml(path)
    root = path.parent

    base = _read_scope(data, "all")
    scopes: dict[str, Scope] = {"all": base}
    for name in SCOPE_SECTIONS:
        own = _read_scope(data, name)
        scopes[name] = Scope(
            include=_merge(base.include, own.include),
            exclude=_merge(base.exclude, own.exclude),
        )

    project = _read_project(root)
    name = project.get("name")
    version = project.get("version")
    requires = project.get("requires-python")
    return AcodoConfig(
        root=root,
        project_name=name if isinstance(name, str) and name else root.name,
        version=version if isinstance(version, str) else "",
        requires_python=requires if isinstance(requires, str) else "",
        scopes=scopes,
        backup=_read_output(data, "backup", DEFAULT_BACKUP_TARGET),
        api=_read_output(data, "api", DEFAULT_API_TARGET),
        gh_config_file=_get_str(
            _table(data, "github_app"),
            "github_app",
            "config_file",
            DEFAULT_GH_CONFIG_FILE,
        ),
    )
