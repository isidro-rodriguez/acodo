"""Validaciones: verifican que un string tenga el formato requerido.

Las funciones `valid_*` devuelven `bool`.

Comprueban el formato, no la existencia ni la titularidad: `valid_email`,
`valid_phone` y `valid_url` son comprobaciones heurísticas. Si necesitas una
validación estricta, usa en tu proyecto una librería especializada (por
ejemplo `email-validator` o `phonenumbers`).
"""

from __future__ import annotations

import re
import string
from functools import cache
from ipaddress import ip_address
from json import loads
from urllib.parse import urlparse

from .converters import (
    _reject_constant,
    to_bool,
    to_date,
    to_datetime,
    to_int,
    to_network,
    to_path,
    to_port,
    to_timedelta,
)
from .types import SocialLink

# =============================================================================
#  Constantes
# =============================================================================


# Parte local: átomos separados por un único punto, sin puntos al inicio, al
# final ni consecutivos (RFC 5322).
_EMAIL_ATOM = r"[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+"

_EMAIL_RE = re.compile(
    rf"{_EMAIL_ATOM}(?:\.{_EMAIL_ATOM})*"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+"
)

# Etiqueta DNS: 1-63 caracteres, empieza y termina en alfanumérico,
# con guiones solo en el interior.
_LABEL = r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"

_DOMAIN_RE = re.compile(rf"{_LABEL}(?:\.{_LABEL})+")

_TLD_RE = re.compile(r"[a-zA-Z]{2,}")

# BIC/SWIFT (ISO 9362): 6 letras + 2 alfanuméricos + 3 opcionales.
_BIC_RE = re.compile(r"[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?")

# MAC de 48 bits: separada por `:` o `-` (siempre el mismo), por `.` (grupos de
# 4) o sin separar.
_MAC_RE = re.compile(
    r"[0-9A-F]{2}(?P<sep>[:-])(?:[0-9A-F]{2}(?P=sep)){4}[0-9A-F]{2}"
    r"|[0-9A-F]{4}(?:\.[0-9A-F]{4}){2}"
    r"|[0-9A-F]{12}"
)

_LOWER_LETTERS = string.ascii_lowercase + "ñ"

_HEX_DIGITS = frozenset(string.hexdigits)

_DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

_INVALID_FILENAME_CHARS = frozenset('<>:"/\\|?*') | frozenset(map(chr, range(32)))

_WINDOWS_RESERVED_NAMES = frozenset(
    {
        "aux",
        "con",
        "nul",
        "prn",
        *(f"com{n}" for n in range(1, 10)),
        *(f"lpt{n}" for n in range(1, 10)),
    }
)

# =============================================================================
#  Validaciones
# =============================================================================


_CIF_RE = re.compile(r"[ABCDEFGHJNPQRSUVW][0-9]{7}[0-9A-J]")

_POSTAL_CODE_RE = re.compile(r"(?:0[1-9]|[1-4][0-9]|5[0-2])[0-9]{3}")


def _dni_letter(number: int) -> str:
    # Letra de control de DNI/NIE.
    return _DNI_LETTERS[number % 23]


def valid_bic(raw: str) -> bool:
    """Comprueba si el string es un BIC/SWIFT con formato válido (ISO 9362).

    Acepta 8 (BIC8) u 11 (BIC11) caracteres: seis letras del banco, dos del
    código de país y dos o cinco alfanuméricos. No valida que el país esté
    asignado realmente ni el dígito de control.

    Args:
        raw: String a validar.

    Returns:
        `True` si el BIC presenta un formato válido.

    Examples:
        >>> valid_bic("ESPCESMMXXX")
        True
        >>> valid_bic("ESPCESMM")
        True
        >>> valid_bic("ESPCESMMX")
        False
    """
    return _BIC_RE.fullmatch(raw.upper()) is not None


def valid_bool(raw: str) -> bool:
    """Comprueba si el string lo aceptaría `to_bool`.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string representa un booleano reconocible.

    Examples:
        >>> valid_bool("Sí")
        True
        >>> valid_bool("off")
        True
        >>> valid_bool("basura")
        False
    """
    return to_bool(raw) is not None


def valid_cidr(raw: str, version: int | None = None, strict: bool = False) -> bool:
    """Comprueba si el string es una red IPv4 o IPv6 en notación CIDR.

    Se apoya en `to_network`: exige prefijo (`/`).

    Args:
        raw: String a validar.
        version: `4` o `6` para exigir esa versión; `None` admite ambas.
        strict: Si es `True`, rechaza las redes con bits de host activos.

    Returns:
        `True` si es una red CIDR válida (de la versión indicada).

    Raises:
        ValueError: Si `version` no es `None`, `4` ni `6`.

    Examples:
        >>> valid_cidr("192.168.1.0/24")
        True
        >>> valid_cidr("192.168.1.5/24")
        True
        >>> valid_cidr("192.168.1.5/24", strict=True)
        False
        >>> valid_cidr("10.0.0.1")
        False
        >>> valid_cidr("fd00::/8", version=4)
        False
        >>> valid_cidr("300.0.0.0/8")
        False
    """
    if version not in (None, 4, 6):
        raise ValueError("`version` debe ser None, 4 o 6.")

    network = to_network(raw, strict=strict)
    return network is not None and (version is None or network.version == version)


def valid_cif(raw: str) -> bool:
    """Comprueba si el string es un CIF español válido (persona jurídica).

    Formato: letra de entidad, 7 dígitos y carácter de control (dígito o
    letra según el tipo de entidad).

    Args:
        raw: String a validar.

    Returns:
        `True` si el formato y el carácter de control son correctos.

    Examples:
        >>> valid_cif("A58818501")
        True
        >>> valid_cif("A58818502")
        False
    """
    text = raw.upper()
    if not _CIF_RE.fullmatch(text):
        return False
    digits = [int(char) for char in text[1:8]]
    total = sum(digits[1::2]) + sum(sum(divmod(2 * d, 10)) for d in digits[::2])
    control = (10 - total % 10) % 10
    if text[0] in "ABEH":
        return text[8] == str(control)
    if text[0] in "NPQRSW":
        return text[8] == "JABCDEFGHI"[control]
    return text[8] in (str(control), "JABCDEFGHI"[control])


def valid_date(raw: str) -> bool:
    """Comprueba si el string lo aceptaría `to_date`.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string representa una fecha habitual.

    Examples:
        >>> valid_date("31/01/2024")
        True
        >>> valid_date("basura")
        False
    """
    return to_date(raw) is not None


def valid_datetime(raw: str) -> bool:
    """Comprueba si el string lo aceptaría `to_datetime`.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string representa una fecha habitual.

    Examples:
        >>> valid_datetime("2024-01-31")
        True
        >>> valid_datetime("basura")
        False
    """
    return to_datetime(raw) is not None


def valid_dni(raw: str) -> bool:
    """Comprueba si el string es un DNI español válido (8 dígitos y letra).

    Args:
        raw: String a validar.

    Returns:
        `True` si el formato y la letra de control son correctos.

    Examples:
        >>> valid_dni("12345678Z")
        True
        >>> valid_dni("12345678A")
        False
    """
    text = raw.upper()
    if not re.fullmatch(r"[0-9]{8}[A-Z]", text):
        return False
    return text[8] == _dni_letter(int(text[:8]))


def valid_domain(raw: str) -> bool:
    """Comprueba si el string es un nombre de dominio (DNS) bien formado.

    Exige al menos dos etiquetas separadas por puntos, cada una de 1-63
    caracteres que empiece y termine en alfanumérico (guiones solo en el
    interior), un TLD final solo de letras de longitud ≥ 2 y una longitud
    total ≤ 253. No se admiten espacios ni puntos finales; no valida IDN.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string es un dominio válido.

    Examples:
        >>> valid_domain("example.com")
        True
        >>> valid_domain("sub.dominio.example.com")
        True
        >>> valid_domain("example")
        False
        >>> valid_domain("example.123")
        False
        >>> valid_domain("-example.com")
        False
    """
    if len(raw) > 253 or _DOMAIN_RE.fullmatch(raw) is None:
        return False
    return _TLD_RE.fullmatch(raw.rsplit(".", 1)[-1]) is not None


def valid_duration(raw: str) -> bool:
    """Comprueba si el string es aceptado por `to_timedelta`.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string representa una duración (`"1h 30m"`, `"2d"`...).

    Examples:
        >>> valid_duration("1h 30m")
        True
        >>> valid_duration("abc")
        False
    """
    return to_timedelta(raw) is not None


def valid_email(raw: str) -> bool:
    """Comprueba si el string presenta un formato de email válido.

    Solo comprueba el formato habitual (hasta 254 caracteres): no cubre todo
    el RFC 5322 ni verifica que el dominio o el buzón existan.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string presenta formato de email válido.

    Examples:
        >>> valid_email("a@b.com")
        True
        >>> valid_email("hola")
        False
    """
    return len(raw) <= 254 and _EMAIL_RE.fullmatch(raw) is not None


def valid_filename(raw: str) -> bool:
    r"""Comprueba si el string es un nombre de fichero válido en cualquier SO.

    Rechaza nombres vacíos o de más de 255 caracteres, caracteres
    `<>:"/\|?*` y de control, nombres que terminan en punto o espacio, y los
    nombres reservados de Windows (`CON`, `NUL`, `COM1`...) con cualquier
    extensión.

    Args:
        raw: Nombre de fichero (sin ruta) a validar.

    Returns:
        `True` si el nombre es válido.

    Examples:
        >>> valid_filename("informe.pdf")
        True
        >>> valid_filename("a/b.txt")
        False
        >>> valid_filename("CON.txt")
        False
        >>> valid_filename("archivo.")
        False
    """
    if not raw or len(raw) > 255 or raw[-1] in " .":
        return False
    if not _INVALID_FILENAME_CHARS.isdisjoint(raw):
        return False
    return raw.split(".", 1)[0].rstrip(" ").casefold() not in _WINDOWS_RESERVED_NAMES


def valid_hex_color(raw: str, allow_alpha: bool = True) -> bool:
    """Comprueba si el string es un color hexadecimal (`#rgb`, `#rrggbb`...).

    Args:
        raw: String a validar.
        allow_alpha: Si se admiten las formas con canal alfa
            (`#rgba`, `#rrggbbaa`).

    Returns:
        `True` si el string es un color hexadecimal válido.

    Examples:
        >>> valid_hex_color("#fff")
        True
        >>> valid_hex_color("#ff00cc80")
        True
        >>> valid_hex_color("#ff00cc80", allow_alpha=False)
        False
        >>> valid_hex_color("fff")
        False
    """
    lengths = (4, 5, 7, 9) if allow_alpha else (4, 7)
    return len(raw) in lengths and raw[0] == "#" and set(raw[1:]) <= _HEX_DIGITS


def valid_iban(raw: str) -> bool:
    """Comprueba si el string es un IBAN con dígitos de control correctos.

    Admite espacios y minúsculas. Valida el formato general y el módulo 97,
    pero no la longitud específica de cada país.

    Args:
        raw: String a validar.

    Returns:
        `True` si el IBAN es válido.

    Examples:
        >>> valid_iban("ES91 2100 0418 4502 0005 1332")
        True
        >>> valid_iban("ES91 2100 0418 4502 0005 1333")
        False
    """
    text = raw.replace(" ", "").upper()
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", text):
        return False

    rearranged = text[4:] + text[:4]
    return int("".join(str(int(char, 36)) for char in rearranged)) % 97 == 1


def valid_int(raw: str, minimum: int | None = None, maximum: int | None = None) -> bool:
    """Comprueba si el string lo aceptaría `to_int`, opcionalmente en un rango.

    Hereda las reglas de `to_int`: rechaza `bool`, los guiones bajos (`"1_000"`)
    y los decimales.

    Args:
        raw: String a validar.
        minimum: Valor mínimo admitido (inclusivo); `None` sin límite.
        maximum: Valor máximo admitido (inclusivo); `None` sin límite.

    Returns:
        `True` si es un entero dentro de los límites indicados.

    Raises:
        ValueError: Si `minimum` es mayor que `maximum`.

    Examples:
        >>> valid_int("42")
        True
        >>> valid_int("3.5")
        False
        >>> valid_int("0", minimum=1)
        False
        >>> valid_int("8192", 512, 131072)
        True
    """
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("`minimum` no puede ser mayor que `maximum`.")

    value = to_int(raw)
    if value is None:
        return False
    return (minimum is None or value >= minimum) and (
        maximum is None or value <= maximum
    )


def valid_ip(raw: str, version: int | None = None) -> bool:
    """Comprueba si el string es una dirección IPv4 o IPv6 válida.

    Args:
        raw: String a validar.
        version: `4` o `6` para exigir esa versión; `None` admite ambas.

    Returns:
        `True` si es una dirección IP válida (de la versión indicada).

    Raises:
        ValueError: Si `version` no es `None`, `4` ni `6`.

    Examples:
        >>> valid_ip("192.168.1.1")
        True
        >>> valid_ip("::1", version=4)
        False
        >>> valid_ip("999.1.1.1")
        False
    """
    if version not in (None, 4, 6):
        raise ValueError("`version` debe ser None, 4 o 6.")

    try:
        ip = ip_address(raw)
    except ValueError:
        return False
    return version is None or ip.version == version


def valid_json(raw: str) -> bool:
    """Comprueba si el string es JSON bien formado (RFC 8259).

    Se rechazan `NaN`, `Infinity` y `-Infinity`.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string es JSON válido.

    Examples:
        >>> valid_json('{"a": [1, 2]}')
        True
        >>> valid_json("{'a': 1}")
        False
        >>> valid_json("NaN")
        False
    """
    try:
        loads(raw, parse_constant=_reject_constant)
    except (ValueError, RecursionError):  # JSONDecodeError es ValueError
        return False
    return True


def valid_mac(raw: str) -> bool:
    """Comprueba si el string es una dirección MAC de 48 bits válida.

    Admite los separadores `:` y `-` (seis pares hexadecimales), `.` (tres
    grupos de cuatro) o ningún separador (doce dígitos seguidos), en
    mayúsculas o minúsculas.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string es una MAC válida.

    Examples:
        >>> valid_mac("00:1A:2B:3C:4D:5E")
        True
        >>> valid_mac("00-1a-2b-3c-4d-5e")
        True
        >>> valid_mac("001A.2B3C.4D5E")
        True
        >>> valid_mac("00:1A:2B:3C:4D")
        False
        >>> valid_mac("GG:1A:2B:3C:4D:5E")
        False
    """
    return _MAC_RE.fullmatch(raw.upper()) is not None


def valid_nie(raw: str) -> bool:
    """Comprueba si el string es un NIE español válido (X/Y/Z, 7 dígitos, letra).

    Args:
        raw: String a validar.

    Returns:
        `True` si el formato y la letra de control son correctos.

    Examples:
        >>> valid_nie("X1234567L")
        True
        >>> valid_nie("X1234567A")
        False
    """
    text = raw.upper()
    if not re.fullmatch(r"[XYZ][0-9]{7}[A-Z]", text):
        return False
    number = int(f"{'XYZ'.index(text[0])}{text[1:8]}")
    return text[8] == _dni_letter(number)


def valid_nif(raw: str) -> bool:
    """Comprueba si el string es un NIF español de persona física válido.

    Admite DNI, NIE y los NIF especiales que empiezan por K, L o M. Para
    personas jurídicas usa `valid_cif`.

    Args:
        raw: String a validar.

    Returns:
        `True` si el formato y la letra de control son correctos.

    Examples:
        >>> valid_nif("12345678Z")
        True
        >>> valid_nif("X1234567L")
        True
        >>> valid_nif("K1234567L")
        True
        >>> valid_nif("12345678A")
        False
    """
    text = raw.upper()
    if valid_dni(text) or valid_nie(text):
        return True
    return bool(re.fullmatch(r"[KLM][0-9]{7}[A-Z]", text)) and text[8] == _dni_letter(
        int(text[1:8])
    )


def valid_passport(raw: str) -> bool:
    """Comprueba si el string tiene formato de pasaporte genérico.

    Cada país usa su propio formato, así que aquí se acepta el patrón más
    habitual: entre 6 y 9 caracteres alfanuméricos. No valida el dígito de
    control ni el país emisor.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string presenta un formato de pasaporte genérico.

    Examples:
        >>> valid_passport("ABC123456")
        True
        >>> valid_passport("12345678")
        True
        >>> valid_passport("AB123")
        False
        >>> valid_passport("ABC-1234")
        False
    """
    return re.fullmatch(r"[A-Z0-9]{6,9}", raw.upper()) is not None


@cache
def _allowed_chars(
    special_characters: str,
    allow_uppercase: bool,
    only_digits: bool,
) -> frozenset[str]:
    # Conjunto de caracteres permitidos (cacheado por combinación de argumentos).
    if only_digits:
        return frozenset(string.digits)

    letters = _LOWER_LETTERS + (_LOWER_LETTERS.upper() if allow_uppercase else "")
    return frozenset(string.digits + letters + special_characters)


def _check_password_args(
    length: tuple[int, int],
    special_characters: str,
    only_digits: bool,
) -> None:
    # Valida los argumentos de configuración compartidos por valid_ y get_.
    min_length, max_length = length
    if min_length > max_length:
        raise ValueError("Rango de longitud incoherente: mínimo mayor que máximo.")
    if only_digits and special_characters:
        raise ValueError("Argumentos ambiguos: `only_digits` con `special_characters`.")


def valid_password(
    raw: str,
    length: tuple[int, int],
    special_characters: str = "",
    allow_uppercase: bool = True,
    only_digits: bool = False,
) -> bool:
    """Comprueba si el string presenta el formato de contraseña requerido.

    Solo valida longitud y caracteres permitidos; no exige mínimos de cada
    tipo de carácter. Con `only_digits`, `allow_uppercase` carece de efecto.

    Args:
        raw: Contraseña a validar.
        length: Rango (mínimo, máximo) de longitud permitida, ambos inclusive.
        special_characters: Caracteres especiales permitidos.
        allow_uppercase: Mayúsculas permitidas.
        only_digits: Si solo se permiten dígitos.

    Returns:
        `True` si la contraseña cumple las condiciones.

    Raises:
        ValueError: Si se han indicado argumentos ambiguos o incoherentes.

    Examples:
        >>> valid_password("Secreto123", length=(8, 16))
        True
        >>> valid_password("corta", length=(8, 16))
        False
        >>> valid_password("clave!2026", length=(8, 16))
        False
        >>> valid_password("clave!2026", length=(8, 16), special_characters="!")
        True
        >>> valid_password("12345678", length=(8, 8), only_digits=True)
        True
    """
    _check_password_args(length, special_characters, only_digits)
    min_length, max_length = length

    if not min_length <= len(raw) <= max_length:
        return False

    return set(raw) <= _allowed_chars(special_characters, allow_uppercase, only_digits)


def valid_path(raw: str, absolute: bool = False, exists: bool = False) -> bool:
    """Comprueba si el string lo aceptaría `to_path`.

    `absolute` se evalúa sobre el texto tal cual, sin expandir `~`: debe
    empezar por `/`. Así `~/x` no cuenta como absoluta, porque al expandirse
    depende del usuario que ejecuta (como `root` acabaría en `/root`).

    Args:
        raw: String a validar.
        absolute: Si es `True`, exige que el texto empiece por `/`.
        exists: Si es `True`, exige que la ruta exista (tras expandir `~`).

    Returns:
        `True` si es una ruta válida que cumple las condiciones indicadas.

    Examples:
        >>> valid_path("/etc/hosts", absolute=True)
        True
        >>> valid_path("rel/ativa", absolute=True)
        False
        >>> valid_path("~/x", absolute=True)
        False
        >>> valid_path("   ")
        False
    """
    path = to_path(raw)
    if path is None:
        return False
    if absolute and not raw.startswith("/"):
        return False
    return not exists or path.exists()


def valid_phone(raw: str) -> bool:
    """Comprueba si el string es un teléfono en formato internacional básico.

    Admite un `+` inicial y los separadores espacio, punto, guion y
    paréntesis; exige entre 7 y 15 dígitos (E.164). No valida por país ni comprueba que
    el número exista.

    Args:
        raw: String a validar.

    Returns:
        `True` si el formato es válido.

    Examples:
        >>> valid_phone("+34 612 345 678")
        True
        >>> valid_phone("(91) 123-4567")
        True
        >>> valid_phone("12345")
        False
    """
    text = raw.strip()
    if not re.fullmatch(r"\+?[0-9 .()\-]+", text):
        return False
    if text.count("(") != text.count(")"):
        return False
    return 7 <= sum(char.isdigit() for char in text) <= 15


def valid_port(raw: str) -> bool:
    """Comprueba si el string lo aceptaría `to_port`.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string representa un puerto en el rango 1-65535.

    Examples:
        >>> valid_port("8080")
        True
        >>> valid_port("0")
        False
        >>> valid_port("70000")
        False
        >>> valid_port("abc")
        False
    """
    return to_port(raw) is not None


def valid_postal_code(raw: str) -> bool:
    """Comprueba si el string es un código postal español (provincias 01-52).

    Args:
        raw: String a validar.

    Returns:
        `True` si son 5 dígitos y los dos primeros son una provincia válida.

    Examples:
        >>> valid_postal_code("38001")
        True
        >>> valid_postal_code("00001")
        False
        >>> valid_postal_code("53000")
        False
    """
    return _POSTAL_CODE_RE.fullmatch(raw) is not None


def valid_slug(raw: str) -> bool:
    """Comprueba si el string es un slug: minúsculas, dígitos y guiones simples.

    Args:
        raw: String a validar.

    Returns:
        `True` si el string es un slug válido (el que produce `parse_slug`).

    Examples:
        >>> valid_slug("hola-mundo")
        True
        >>> valid_slug("Hola Mundo")
        False
        >>> valid_slug("hola--mundo")
        False
    """
    return re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", raw) is not None


def valid_social_url(raw: str, link: SocialLink) -> bool:
    """Comprueba que es un enlace de red social válido.

    Solo comprueba el formato: no verifica que el contenido exista.

    Args:
        raw: String a validar como enlace de red social.
        link: Tipo de enlace esperado (`SocialLink`), por ejemplo
            `GITHUB_REPO`, `INSTAGRAM_REEL` o `YOUTUBE_CHANNEL`.

    Returns:
        `True` si `raw` es un enlace válido del tipo indicado.

    Examples:
        >>> from acodo.utils.types import SocialLink
        >>> valid_social_url("https://github.com/isidro", SocialLink.GITHUB_PROFILE)
        True
        >>> valid_social_url("instagram.com/reel/C1a2B3c/", SocialLink.INSTAGRAM_REEL)
        True
        >>> valid_social_url("https://youtu.be/dQw4w9WgXcQ", SocialLink.YOUTUBE_VIDEO)
        True
        >>> valid_social_url("https://github.com/user", SocialLink.GITHUB_REPO)
        False
    """
    return link.pattern.fullmatch(raw.strip()) is not None


def valid_url(raw: str) -> bool:
    """Comprueba si el string presenta formato de URL http/https.

    Solo comprueba el formato: no verifica que el host exista ni responda.

    Args:
        raw: String a validar.

    Returns:
        `True` si es una URL http/https con host y sin espacios.

    Examples:
        >>> valid_url("https://example.com/x")
        True
        >>> valid_url("https://[::1")
        False
    """
    if any(map(str.isspace, raw)):
        return False

    try:
        url = urlparse(raw)
        _ = url.port  # Lanza ValueError si el puerto es inválido.
    except ValueError:
        return False

    return url.scheme in ("http", "https") and bool(url.hostname)


def valid_uuid(raw: str) -> bool:
    """Comprueba si el string es un UUID en forma canónica (8-4-4-4-12).

    Args:
        raw: String a validar.

    Returns:
        `True` si el string es un UUID válido.

    Examples:
        >>> valid_uuid("123e4567-e89b-12d3-a456-426614174000")
        True
        >>> valid_uuid("123e4567")
        False
    """
    return (
        re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            raw,
        )
        is not None
    )
