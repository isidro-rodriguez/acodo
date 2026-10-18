"""Logger con destino configurable (consola y/o fichero) sobre ``logging``.

Ofrece `Logger`, un wrapper que permite decidir en cada mensaje si se muestra
por consola, se escribe en el fichero de log o ambos, y `get_logger`, que lo
configura una sola vez por nombre sin tocar el logger raíz.
"""

from __future__ import annotations

import logging
import pprint
import sys
from logging.handlers import TimedRotatingFileHandler
from typing import TYPE_CHECKING, Any

from acodo.utils.validators import valid_filename

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


def _prettify(value: Any) -> str:
    """Convierte un valor en una representación legible de varias líneas.

    Args:
        value: Valor a formatear.

    Returns:
        Cadena formateada con ``pprint`` para contenedores o ``str`` para el
        resto.
    """
    if isinstance(value, (dict, list, tuple, set)):
        return pprint.pformat(value, indent=4, width=120)
    return str(value)


class _DestinationFilter(logging.Filter):
    """Filtra registros según el destino solicitado (consola o fichero)."""

    def __init__(self, key: str) -> None:
        super().__init__()
        self._key = key

    def filter(self, record: logging.LogRecord) -> bool:
        # Un registro sin la marca (emitido directamente con `logging`) se
        # deja pasar a todos los destinos.
        return bool(getattr(record, self._key, True))


class Logger:
    """Wrapper sobre ``logging`` que permite elegir el destino de cada mensaje.

    Los valores con nombre se interpolan con ``%(nombre)s``; un ``%`` literal en
    ``msg`` debe escribirse ``%%`` cuando se pasan valores.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """Inicializa el wrapper sobre un logger estándar.

        Args:
            logger: Logger estándar sobre el que se escribe.
        """
        self._logger = logger

    def error(
        self,
        msg: str,
        exc_info: bool = False,
        console: bool = True,
        file: bool = True,
        **kwargs: object,
    ) -> None:
        """Registra un mensaje de nivel error.

        Args:
            msg: Mensaje a registrar.
            exc_info: Si `True`, añade la traza de la excepción activa.
            console: Si `True`, se muestra por consola.
            file: Si `True`, se escribe en el fichero de log.
            **kwargs: Valores para interpolar en `msg` con `%(nombre)s`.
        """
        self._log(logging.ERROR, msg, console, file, kwargs, exc_info=exc_info)

    def warning(
        self,
        msg: str,
        console: bool = True,
        file: bool = True,
        **kwargs: object,
    ) -> None:
        """Registra un mensaje de nivel aviso.

        Args:
            msg: Mensaje a registrar.
            console: Si `True`, se muestra por consola.
            file: Si `True`, se escribe en el fichero de log.
            **kwargs: Valores para interpolar en `msg` con `%(nombre)s`.
        """
        self._log(logging.WARNING, msg, console, file, kwargs)

    def info(
        self,
        msg: str,
        console: bool = True,
        file: bool = True,
        **kwargs: object,
    ) -> None:
        """Registra un mensaje de nivel información.

        Args:
            msg: Mensaje a registrar.
            console: Si `True`, se muestra por consola.
            file: Si `True`, se escribe en el fichero de log.
            **kwargs: Valores para interpolar en `msg` con `%(nombre)s`.
        """
        self._log(logging.INFO, msg, console, file, kwargs)

    def debug(
        self,
        msg: str,
        console: bool = True,
        file: bool = True,
        **kwargs: object,
    ) -> None:
        """Registra un mensaje de nivel depuración.

        Los contenedores (`dict`, `list`, `tuple`, `set`) pasados como valores
        se formatean en varias líneas para facilitar su lectura.

        Args:
            msg: Mensaje a registrar.
            console: Si `True`, se muestra por consola.
            file: Si `True`, se escribe en el fichero de log.
            **kwargs: Valores para interpolar en `msg` con `%(nombre)s`.
        """
        values = {name: _prettify(value) for name, value in kwargs.items()}
        self._log(logging.DEBUG, msg, console, file, values)

    def _log(
        self,
        level: int,
        msg: str,
        console: bool,
        file: bool,
        values: Mapping[str, object],
        *,
        exc_info: bool = False,
    ) -> None:
        # `logging` interpola de forma perezosa: solo si el nivel está activo.
        # `stacklevel=3` apunta al código que llamó a `info`, `error`...
        self._logger.log(
            level,
            msg,
            *([values] if values else []),
            exc_info=exc_info,
            extra={"to_console": console, "to_file": file},
            stacklevel=3,
        )


def get_logger(
    name: str = "acodo",
    *,
    debug: bool = False,
    file: Path | None = None,
) -> Logger:
    """Configura y devuelve un :class:`Logger` con nombre.

    La configuración es idempotente por nombre: solo se realiza la primera vez.
    En llamadas posteriores con el mismo nombre se devuelve el logger ya
    configurado y se ignoran `debug` y `file`. No se modifica el logger raíz.

    Args:
        name: Nombre del logger.
        debug: Si `True`, activa el nivel `DEBUG` (por defecto, `INFO`).
        file: Ruta del fichero de log, con rotación diaria y 7 copias. Si es
            `None`, solo se escribe por consola. Se crean los directorios que
            falten.

    Returns:
        Instancia de `Logger` lista para usar.

    Raises:
        ValueError: Si `name` está vacío o `file` no tiene un nombre de
            fichero válido.

    Examples:
        >>> log = get_logger("ejemplo")
        >>> log.info("Procesando %(n)s ficheros", n=3)
        Procesando 3 ficheros
    """
    if not name.strip():
        raise ValueError("El nombre del logger no puede estar vacío.")
    if file is not None and not valid_filename(file.name):
        raise ValueError(f"Nombre de fichero de log no válido: {file.name!r}.")

    logger = logging.getLogger(name)
    if logger.handlers:
        return Logger(logger)

    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    console_handler.addFilter(_DestinationFilter("to_console"))
    logger.addHandler(console_handler)

    if file is not None:
        file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            filename=file,
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)-8s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        file_handler.addFilter(_DestinationFilter("to_file"))
        logger.addHandler(file_handler)

    return Logger(logger)
