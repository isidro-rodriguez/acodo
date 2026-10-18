"""Conversores: transforman valores en otros tipos.

Las funciones `to_*` nunca lanzan excepciones por valores inválidos: si no
pueden convertir el valor, devuelven `None`.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from json import loads
from os import fspath
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn, cast

if TYPE_CHECKING:
    from collections.abc import Iterator
    from os import PathLike


# =============================================================================
#  Constantes
# =============================================================================

_TRUE_STRINGS = frozenset({"1", "on", "si", "sí", "t", "true", "verdadero", "y", "yes"})

_FALSE_STRINGS = frozenset({"0", "f", "false", "falso", "n", "no", "off"})

# `kb` y `kib` (y análogos) significan lo mismo: base 1024, como `parse_size`.
_BYTE_UNITS = {"": 1, "b": 1, "byte": 1, "bytes": 1} | {
    f"{prefix}{suffix}": 1024**power
    for power, prefix in enumerate("kmgtp", start=1)
    for suffix in ("b", "ib")
}

_MAX_TIMESTAMP = 4_133_980_799  # 2100-12-31T23:59:59Z

_MAX_TIMEDELTA_SECONDS = 1e12

_DURATION_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(d|h|min|m|s)")

_DURATION_UNITS = {"d": 86400, "h": 3600, "min": 60, "m": 60, "s": 1}

# Los nombres de mes/día (%a %b %B) dependen del locale activo.
_NAMED_MONTH_FORMATS = (
    "%a %b %d %H:%M:%S %Y",
    "%b %d %H:%M:%S %Y",
    "%b %d %Y",
    "%d %b %Y",
    "%d %B %Y",
    "%B %d %Y",
)

# Formatos numéricos no ISO. Se asume día primero (convención europea);
# se evitan deliberadamente los formatos mes-primero.
_NUMERIC_FORMATS = (
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%d.%m.%Y",
)


# =============================================================================
#  Conversores
# =============================================================================


def _reject_constant(name: str) -> NoReturn:
    # Rechaza NaN, Infinity y -Infinity, que no son JSON estándar.
    raise ValueError(name)


def to_bool(raw: str | int | None) -> bool | None:
    """Convierte textos habituales (`"sí"`, `"off"`, `"1"`...) a bool.

    Args:
        raw: Valor a convertir. Los enteros solo pueden ser 0 o 1.

    Returns:
        El booleano, o `None` si el valor no es reconocible.

    Examples:
        >>> to_bool("Sí")
        True
        >>> to_bool(" OFF ")
        False
        >>> to_bool("quizá") is None
        True
        >>> to_bool(2) is None
        True
    """
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, int):
        return bool(raw) if raw in (0, 1) else None
    if isinstance(raw, str):
        text = raw.strip().casefold()
        if text in _TRUE_STRINGS:
            return True
        if text in _FALSE_STRINGS:
            return False
    return None


def to_bytes(raw: str | None) -> int | None:
    """Convierte un texto de tamaño (`"1,5 GiB"`) a bytes.

    Todas las unidades usan base 1024: `KB` y `KiB` valen lo mismo, y así
    `MB`/`MiB`, `GB`/`GiB`... Admite coma o punto decimal. Sin unidad se asumen
    bytes. Es el camino inverso, aproximado, de `parse_size`.

    Args:
        raw: Texto a convertir.

    Returns:
        Cantidad de bytes, o `None` si el texto no es válido.

    Examples:
        >>> to_bytes("1,5 GiB")
        1610612736
        >>> to_bytes("2 MB")
        2097152
        >>> to_bytes("512")
        512
        >>> to_bytes("1 furlong") is None
        True
    """

    def _normalize_number(text: str) -> str:
        # Unifica separadores: el último que aparezca es el decimal.
        if text.rfind(",") > text.rfind("."):
            return text.replace(".", "").replace(",", ".")
        return text.replace(",", "")

    if raw is None:
        return None

    match = re.fullmatch(r"(\d[\d.,]*)\s*([a-z]*)", raw.strip().casefold())
    if match is None:
        return None

    factor = _BYTE_UNITS.get(match[2])
    if factor is None:
        return None

    try:
        return round(float(_normalize_number(match[1])) * factor)
    except (ValueError, OverflowError):
        return None


def to_date(raw: str) -> date | None:
    """Convierte un string con fechas habituales a date.

    Acepta los mismos formatos que `to_datetime`.

    Args:
        raw: String a ser parseado como fecha.

    Returns:
        La fecha, o `None` si la conversión falla.

    Examples:
        >>> to_date("31/01/2024")
        datetime.date(2024, 1, 31)
    """
    dt = to_datetime(raw)
    return None if dt is None else dt.date()


def to_datetime(raw: str) -> datetime | None:
    """Convierte un string con fechas habituales a datetime.

    Solo se conserva la fecha: el resultado es siempre medianoche y sin zona
    horaria. En los formatos con día y mes numéricos se asume día primero.

    Args:
        raw: String a ser parseado como fecha.

    Returns:
        El datetime a medianoche, o `None` si la conversión falla.

    Examples:
        >>> to_datetime("2024-01-31")
        datetime.datetime(2024, 1, 31, 0, 0)
        >>> to_datetime("31/01/2024")
        datetime.datetime(2024, 1, 31, 0, 0)
        >>> to_datetime("1700000000")
        datetime.datetime(2023, 11, 14, 0, 0)
        >>> to_datetime("basura") is None
        True
    """

    def _midnight(dt: datetime) -> datetime:
        # Descarta hora y zona horaria.
        return datetime(dt.year, dt.month, dt.day)

    raw = raw.strip()

    # ISO 8601 (C puro, el camino más rápido). `fromisoformat` acepta "Z".
    if raw[-1:] == "z":
        raw = raw[:-1] + "Z"
    try:
        return _midnight(datetime.fromisoformat(raw))
    except ValueError:
        pass

    # Unix timestamp en segundos (barato: se descarta antes que `strptime`).
    if raw.isascii() and raw.isdigit() and 9 <= len(raw) <= 11:
        timestamp = int(raw)
        if timestamp <= _MAX_TIMESTAMP:
            return _midnight(datetime.fromtimestamp(timestamp, tz=UTC))

    # Formatos con nombres de mes y formatos numéricos no ISO.
    for fmt in _NAMED_MONTH_FORMATS + _NUMERIC_FORMATS:
        try:
            return _midnight(datetime.strptime(raw, fmt))
        except ValueError:
            pass

    # RFC 2822 / RFC 5322.
    try:
        return _midnight(parsedate_to_datetime(raw))
    except (TypeError, ValueError, OverflowError):
        return None


def to_decimal(raw: str | float | None) -> Decimal | None:
    """Convierte strings numéricos a Decimal (apto para importes).

    Los `float` se convierten a través de su representación en texto
    (`0.1` -> `Decimal("0.1")`). Se rechazan `bool`, `nan`, `inf` y los
    guiones bajos (`"1_000"`).

    Args:
        raw: Valor a convertir (texto numérico, entero o flotante).

    Returns:
        El número convertido, o `None` si la conversión falla.

    Examples:
        >>> to_decimal("0.10")
        Decimal('0.10')
        >>> to_decimal(0.1)
        Decimal('0.1')
        >>> to_decimal("nan") is None
        True
    """
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, str) and "_" in raw:
        return None

    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return None
    return value if value.is_finite() else None


def to_dict(raw: object) -> dict[Any, Any] | None:
    """Convierte un valor a dict, convirtiendo también los anidados.

    Se aceptan mappings, dataclasses y pares `("k", v)`; los valores
    anidados que sean mappings o dataclasses se convierten recursivamente.

    Args:
        raw: Valor a convertir.

    Returns:
        El dict resultante; `None` si el valor no es convertible o el
        resultado está vacío.

    Examples:
        >>> to_dict({"a": 1})
        {'a': 1}
        >>> to_dict([("a", 1), ("b", 2)])
        {'a': 1, 'b': 2}
        >>> to_dict(None) is None
        True
        >>> to_dict({}) is None
        True
    """

    def _convert(value: object) -> object:
        # `asdict` solo se llama en instancias de dataclass, nunca en la
        # clase en sí, por eso se comprueba `not isinstance(value, type)`.
        if is_dataclass(value) and not isinstance(value, type):
            return asdict(value)
        if isinstance(value, Mapping):
            return {key: _convert(item) for key, item in value.items()}
        return value

    if is_dataclass(raw) and not isinstance(raw, type):
        # `asdict` solo se llama en instancias de dataclass, nunca en la
        # clase en sí, por eso se comprueba `not isinstance(raw, type)`.
        result = asdict(raw)
    elif isinstance(raw, Mapping):
        result = {key: _convert(value) for key, value in raw.items()}
    elif isinstance(raw, Iterable):
        # `isinstance(raw, Iterable)` no estreña el tipo en ty; se aplica
        # `cast` para indicar explícitamente que `raw` es un iterable.
        result = {}
        try:
            for item in cast(Iterable[Any], raw):
                # Un texto de dos caracteres se desempaquetaría como un par.
                if isinstance(item, (str, bytes)):
                    return None
                key, value = item
                result[key] = _convert(value)
        except (TypeError, ValueError):
            return None
    else:
        return None
    return result or None


def to_float(raw: str | float | None) -> float | None:
    """Convierte strings numéricos a float.

    Se rechazan `bool`, `nan`, `inf` y los guiones bajos (`"1_000"`).

    Args:
        raw: Valor a convertir (texto numérico o flotante).

    Returns:
        El número convertido, o `None` si la conversión falla.

    Examples:
        >>> to_float("1.5")
        1.5
        >>> to_float("nan") is None
        True
    """
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, str) and "_" in raw:
        return None

    try:
        value = float(raw)
    except (ValueError, TypeError, OverflowError):
        return None
    return value if math.isfinite(value) else None


def to_int(raw: str | float | int | None) -> int | None:
    """Convierte strings numéricos a int.

    Un `float` solo se convierte si es entero exacto (`3.0` sí, `3.7` no).
    Se rechazan `bool` y los guiones bajos (`"1_000"`).

    Args:
        raw: Valor a convertir (texto numérico o entero).

    Returns:
        El número convertido, o `None` si la conversión falla.

    Examples:
        >>> to_int("42")
        42
        >>> to_int(3.7) is None
        True
        >>> to_int(float("inf")) is None
        True
    """
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, float):
        return int(raw) if raw.is_integer() else None  # nan/inf -> None
    if isinstance(raw, str) and "_" in raw:
        return None

    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


def to_json(raw: str | bytes | None) -> Any | None:
    """Convierte un string JSON (RFC 8259) en su valor de Python.

    Se rechazan `NaN`, `Infinity` y `-Infinity`. El JSON `null` también
    produce `None`: para distinguirlo de un JSON inválido usa `valid_json`.

    Args:
        raw: String o bytes con el JSON.

    Returns:
        El valor decodificado (`dict`, `list`, `str`, `int`, `float`,
        `bool` o `None`); `None` si el JSON no es válido.

    Examples:
        >>> to_json('{"a": [1, 2]}')
        {'a': [1, 2]}
        >>> to_json("{'a': 1}") is None
        True
        >>> to_json("NaN") is None
        True
    """
    if raw is None:
        return None
    try:
        return loads(raw, parse_constant=_reject_constant)
    except (ValueError, RecursionError):  # JSONDecodeError es ValueError
        return None


def _flatten(raw: object) -> Iterator[Any]:
    # Aplana iterables anidados; `None` no aporta elementos.
    if raw is None:
        return
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Iterable):
        yield raw
        return
    for value in raw:
        yield from _flatten(value)


def to_list(raw: object) -> list[Any] | None:
    """Convierte un valor a lista, aplanando las anidadas.

    Un escalar (o un `str`/`bytes`) produce una lista de un elemento; un
    iterable se aplana recursivamente y se ignoran los `None`.

    Args:
        raw: Valor a convertir.

    Returns:
        La lista aplanada; `None` si el resultado está vacío.

    Examples:
        >>> to_list([1, [2, 3]])
        [1, 2, 3]
        >>> to_list("abc")
        ['abc']
        >>> to_list(None) is None
        True
        >>> to_list([]) is None
        True
    """
    return list(_flatten(raw)) or None


def to_path(raw: str | PathLike[str] | None) -> Path | None:
    """Convierte un texto o ruta a Path, expandiendo `~`.

    Args:
        raw: Texto o ruta a convertir.

    Returns:
        La ruta, o `None` si el valor falta, está en blanco o no es válido.

    Examples:
        >>> to_path("carpeta/fichero.txt").name
        'fichero.txt'
        >>> to_path("   ") is None
        True
    """
    if raw is None:
        return None

    try:
        text = fspath(raw)
    except TypeError:
        return None

    if not isinstance(text, str) or not text.strip() or "\0" in text:
        return None

    try:
        return Path(text).expanduser()
    except (RuntimeError, ValueError):
        return None


def to_port(raw: str | int | None) -> int | None:
    """Convierte un texto o entero a número de puerto TCP/UDP (1-65535).

    Args:
        raw: Valor a convertir (texto numérico o entero).

    Returns:
        El puerto, o `None` si el valor falta o está fuera del rango 1-65535.

    Examples:
        >>> to_port("8080")
        8080
        >>> to_port(80)
        80
        >>> to_port("0") is None
        True
        >>> to_port(70000) is None
        True
    """
    value = to_int(raw)
    return value if value is not None and 1 <= value <= 65535 else None


def to_str(raw: object) -> str | None:
    """Devuelve el valor si es un texto con contenido.

    Args:
        raw: Valor a comprobar.

    Returns:
        El propio `raw` si es un `str` que no está vacío ni es solo espacios;
        `None` en otro caso.

    Examples:
        >>> to_str("hola")
        'hola'
        >>> to_str("   ") is None
        True
        >>> to_str(42) is None
        True
    """
    return raw if isinstance(raw, str) and raw.strip() else None


def to_timedelta(raw: str | float | None) -> timedelta | None:
    """Convierte segundos o un texto de duración a timedelta.

    Con un `str` se interpreta una duración con unidades: `d`, `h`,
    `min`/`m` y `s`, con decimales y separadas por espacios opcionales
    (`"1h 30m"`, `"1,5h"`). Un texto sin unidades (`"90"`) no es válido.

    Args:
        raw: Cantidad de segundos, o texto de duración.

    Returns:
        La duración, o `None` si el valor falta, no es válido, no es finito
        o es desmesurado.

    Examples:
        >>> to_timedelta(90)
        datetime.timedelta(seconds=90)
        >>> to_timedelta("1h 30m")
        datetime.timedelta(seconds=5400)
        >>> to_timedelta("1h30x") is None
        True
    """
    if isinstance(raw, str):
        text = raw.strip().casefold()
        tokens = _DURATION_RE.findall(text)
        if not tokens or _DURATION_RE.sub("", text).strip():
            return None
        seconds = sum(
            float(number.replace(",", ".")) * _DURATION_UNITS[unit]
            for number, unit in tokens
        )
    elif isinstance(raw, bool):
        return None
    else:
        seconds = raw
    if (
        seconds is None
        or not math.isfinite(seconds)
        or abs(seconds) > _MAX_TIMEDELTA_SECONDS
    ):
        return None
    return timedelta(seconds=seconds)
