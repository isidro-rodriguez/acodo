"""Modelos de datos compartidos por la configuración y los comandos."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Self


@dataclass(frozen=True, slots=True)
class Scope:
    """Rutas que un comando incluye y excluye, tal como se leen de `acodo.toml`.

    Attributes:
        include: Rutas a procesar, relativas a la raíz del proyecto.
        exclude: Rutas o patrones a omitir, relativos a la raíz del proyecto.
    """

    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class OutputConfig:
    """Destino de un fichero generado (`[backup]` y `[api]`).

    Attributes:
        target: Ruta del fichero de salida, relativa a la raíz del proyecto.
        version_suffix: Si es `True`, añade la versión del proyecto al nombre.
    """

    target: str
    version_suffix: bool


@dataclass(frozen=True, slots=True)
class AcodoConfig:
    """Configuración del proyecto sobre el que se ejecuta `acodo-cli`.

    Se lee de `acodo.toml`; el nombre, la versión y `requires-python` salen del
    `[project]` del `pyproject.toml` contiguo, si existe.

    Attributes:
        root: Directorio que contiene el `acodo.toml` del proyecto.
        project_name: Nombre del proyecto (`[project].name` o el del directorio).
        version: Versión del proyecto (`[project].version`), vacía si no consta.
        requires_python: Especificador PEP 440 de `[project].requires-python`.
        scopes: Alcance efectivo (`[all]` más la sección) de cada comando.
        backup: Destino de la copia de seguridad.
        api: Destino de la documentación de la API.
        gh_config_file: Ruta del JSON de la GitHub App, relativa a `root`.
    """

    root: Path
    project_name: str
    version: str
    requires_python: str
    scopes: dict[str, Scope]
    backup: OutputConfig
    api: OutputConfig
    gh_config_file: str

    def scope_dirs(self, name: str) -> list[Path]:
        """Directorios existentes del `include` de la sección `name`."""
        return [
            path
            for entry in self.scopes[name].include
            if (path := self.root / entry).is_dir()
        ]


@dataclass(frozen=True, slots=True)
class Step:
    """Comprobación de calidad: nombre visible y comando a ejecutar."""

    name: str
    command: tuple[str, ...]


class Archiver(StrEnum):
    """Formatos de compresión admitidos por `backup`."""

    ZIP = "zip"
    TAR_GZ = "tar.gz"


class Status(StrEnum):
    """Resultado de una comprobación de `doctor`."""

    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class DoctorResult:
    """Comprobación de `doctor`: nombre, estado y detalle legible."""

    name: str
    status: Status
    detail: str = ""


@dataclass(slots=True)
class LineStats:
    """Métricas de código y docstrings para un fichero o categoría."""

    code: int = 0
    docstrings: int = 0

    @property
    def total(self) -> int:
        """Suma total de líneas efectivas (código + docstrings)."""
        return self.code + self.docstrings

    def __add__(self, other: Self) -> LineStats:
        """Suma las métricas de dos conteos."""
        return LineStats(
            code=self.code + other.code,
            docstrings=self.docstrings + other.docstrings,
        )


@dataclass
class Category:
    """Grupo de ficheros con sus métricas de código y docstrings."""

    name: str
    files: list[tuple[Path, LineStats]] = field(default_factory=list)

    @property
    def totals(self) -> LineStats:
        """Suma acumulada de todas las métricas de la categoría."""
        stats = LineStats()
        for _, file_stats in self.files:
            stats += file_stats
        return stats
