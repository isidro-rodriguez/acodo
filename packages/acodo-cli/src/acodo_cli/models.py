"""Modelos de datos compartidos por la configuración y los comandos."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Self


@dataclass(frozen=True, slots=True)
class AcodoConfig:
    """Configuración del proyecto sobre el que se ejecuta `acodo-cli`.

    Attributes:
        root: Directorio que contiene el `pyproject.toml` del proyecto.
        project_name: Nombre del proyecto (`[project].name` o el del directorio).
        src_dir: Directorio del código fuente, relativo a `root`.
        test_dir: Directorio de tests, relativo a `root`.
        python_version: Versión de Python esperada (especificador PEP 440).
    """

    root: Path
    project_name: str
    src_dir: str
    test_dir: str
    python_version: str

    @property
    def src(self) -> Path:
        """Ruta absoluta del directorio de código fuente."""
        return self.root / self.src_dir

    @property
    def tests(self) -> Path:
        """Ruta absoluta del directorio de tests."""
        return self.root / self.test_dir


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
