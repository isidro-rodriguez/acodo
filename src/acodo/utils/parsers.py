"""Parsers: transforman valores a strings legibles.

Las funciones `parse_*` siempre devuelven `str`.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fractions import Fraction

# =============================================================================
#  Constantes
# =============================================================================


# Intercambia separadores: 1,234.50 <-> 1.234,50
_SWAP_SEPARATORS = str.maketrans(",.", ".,")

_ENGLISH_CODES = frozenset({"en", "eng"})

_SIZE_UNITS = ("KiB", "MiB", "GiB", "TiB", "PiB")


# =============================================================================
#  Parsers
# =============================================================================


def _check_lang(lang: str | None) -> str | None:
    # Normaliza el código de lenguaje y lanza ValueError si es inválido.
    if lang is None:
        return None

    lang = lang.lower()
    if not (lang.isalpha() and 2 <= len(lang) <= 3):
        raise ValueError(
            "Código de lenguaje incorrecto. Consultar: "
            "https://www.loc.gov/standards/iso639-2/php/code_list.php"
        )
    return lang


def parse_amount(
    raw: int | float | Fraction,
    lang: str | None = None,
    decimals: int = 2,
) -> str:
    """Parsea un tipo numérico a string numérico de legibilidad cómoda.

    Los enteros (y las fracciones de denominador 1) se muestran sin decimales.
    Con `lang` `en`/`eng` se usa `1,234.50`; en cualquier otro caso
    (incluido `None`), `1.234,50`.

    Args:
        raw: Número a parsear.
        lang: Código del lenguaje al que se va a formatear el número.
        decimals: Cantidad de dígitos decimales a mostrar.

    Returns:
        String numérico de legibilidad cómoda.

    Raises:
        ValueError: Si se ha indicado código de lenguaje inválido.

    Examples:
        >>> parse_amount(1234.5)
        '1.234,50'
        >>> parse_amount(1234.5, "en")
        '1,234.50'
        >>> parse_amount(1234)
        '1.234'
    """
    lang = _check_lang(lang)

    if not isinstance(raw, (int, float)):  # Fraction, sin importarlo
        raw = raw.numerator if raw.denominator == 1 else float(raw)

    text = f"{raw:,}" if isinstance(raw, int) else f"{raw:,.{decimals}f}"

    return text if lang in _ENGLISH_CODES else text.translate(_SWAP_SEPARATORS)


def parse_bool(raw: bool, lang: str | None = None) -> str:
    """Parsea un booleano a string legible (`"Sí"`/`"No"`).

    Es el camino inverso a `to_bool`. Con `lang` `en`/`eng` se usa
    `"Yes"`/`"No"`; en cualquier otro caso (incluido `None`), `"Sí"`/`"No"`.

    Args:
        raw: Booleano a parsear.
        lang: Código del lenguaje al que se va a formatear el booleano.

    Returns:
        String legible del booleano.

    Raises:
        ValueError: Si se ha indicado código de lenguaje inválido.

    Examples:
        >>> parse_bool(True)
        'Sí'
        >>> parse_bool(False)
        'No'
        >>> parse_bool(True, "en")
        'Yes'
    """
    lang = _check_lang(lang)

    if lang in _ENGLISH_CODES:
        return "Yes" if raw else "No"
    return "Sí" if raw else "No"


def parse_datetime(raw: date | datetime, lang: str | None = None) -> str:
    """Parsea una fecha o fecha-hora a string legible.

    La hora solo se muestra si no es medianoche, y los segundos solo si no
    son cero. La zona horaria se ignora. Con `lang` `en`/`eng` se usa
    `2024-01-31`; en cualquier otro caso (incluido `None`), `31/01/2024`.

    Args:
        raw: Fecha o fecha-hora a parsear.
        lang: Código del lenguaje al que se va a formatear la fecha.

    Returns:
        String de fecha de legibilidad cómoda.

    Raises:
        ValueError: Si se ha indicado código de lenguaje inválido.

    Examples:
        >>> parse_datetime(datetime(2024, 1, 31))
        '31/01/2024'
        >>> parse_datetime(datetime(2024, 1, 31, 10, 30))
        '31/01/2024 10:30'
        >>> parse_datetime(datetime(2024, 1, 31, 10, 30), "en")
        '2024-01-31 10:30'
    """
    lang = _check_lang(lang)

    text = raw.strftime("%Y-%m-%d" if lang in _ENGLISH_CODES else "%d/%m/%Y")
    if isinstance(raw, datetime) and (raw.hour or raw.minute or raw.second):
        text += raw.strftime(" %H:%M:%S" if raw.second else " %H:%M")
    return text


def parse_percent(
    raw: int | float | Fraction,
    lang: str | None = None,
    decimals: int = 1,
) -> str:
    """Parsea un número o fracción (`0.256`, `Fraction(1, 4)`) a porcentaje.

    Se eliminan los ceros decimales sobrantes. Con `lang` `en`/`eng` se usa
    `25.6%`; en cualquier otro caso (incluido `None`), `25,6 %`.

    Args:
        raw: Proporción a parsear (`1` equivale a 100 %).
        lang: Código del lenguaje al que se va a formatear el número.
        decimals: Máximo de dígitos decimales a mostrar.

    Returns:
        String de porcentaje de legibilidad cómoda.

    Raises:
        ValueError: Si se ha indicado código de lenguaje inválido.

    Examples:
        >>> from fractions import Fraction
        >>> parse_percent(0.256)
        '25,6 %'
        >>> parse_percent(Fraction(1, 4))
        '25 %'
        >>> parse_percent(0.5, "en")
        '50%'
        >>> parse_percent(1 / 3, decimals=2)
        '33,33 %'
    """
    lang = _check_lang(lang)

    text = f"{float(raw) * 100:,.{decimals}f}"
    if decimals > 0:
        text = text.rstrip("0").rstrip(".")

    if lang in _ENGLISH_CODES:
        return f"{text}%"
    return f"{text.translate(_SWAP_SEPARATORS)} %"


def parse_size(raw: int) -> str:
    """Parsea el tamaño de fichero a su unidad ISO/IEC 80000-13 correspondiente.

    Args:
        raw: Tamaño de fichero, en bytes, a parsear.

    Returns:
        String de tamaño de fichero con legibilidad cómoda.

    Examples:
        >>> parse_size(1)
        '1 byte'
        >>> parse_size(1536)
        '1,500 KiB'
        >>> parse_size(1048575)
        '1023,999 KiB'
    """
    if raw < 1024:
        return f"{raw} {'byte' if raw == 1 else 'bytes'}"

    value = raw / 1024
    unit = _SIZE_UNITS[0]
    for next_unit in _SIZE_UNITS[1:]:
        # Se compara el valor ya redondeado para no mostrar "1024,000 KiB".
        if round(value, 3) < 1024:
            break
        value /= 1024
        unit = next_unit

    return f"{value:.3f} {unit}".translate(_SWAP_SEPARATORS)


def parse_slug(raw: str) -> str:
    """Parsea un texto a slug: minúsculas, sin acentos y separado por guiones.

    Los caracteres sin equivalente ASCII (`ß`, `€`, emojis...) se descartan.

    Args:
        raw: Texto a parsear.

    Returns:
        El slug; cadena vacía si no queda ningún carácter válido.

    Examples:
        >>> parse_slug("¡Hola, Mundo! Ñandú")
        'hola-mundo-nandu'
    """
    text = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_timedelta(duration: timedelta) -> str:
    """Formatea un timedelta a una cadena con formato `H:MM:SS` o `M:SS`.

    Args:
        duration: Duración a formatear.

    Returns:
        Texto en formato `H:MM:SS` o `M:SS` (con `-` delante si es negativa).

    Examples:
        >>> parse_timedelta(timedelta(seconds=3725))
        '1:02:05'
        >>> parse_timedelta(timedelta(seconds=65))
        '1:05'
        >>> parse_timedelta(timedelta(seconds=-65))
        '-1:05'
    """
    total = int(duration.total_seconds())
    sign = "-" if total < 0 else ""
    hours, remainder = divmod(abs(total), 3600)
    minutes, secs = divmod(remainder, 60)

    if hours > 0:
        return f"{sign}{hours}:{minutes:02d}:{secs:02d}"
    return f"{sign}{minutes}:{secs:02d}"
