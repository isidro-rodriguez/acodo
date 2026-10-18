"""Getters: obtienen valores del entorno del programa.

Las funciones `get_*` producen valores: leen variables de entorno, calculan
hashes o generan credenciales aleatorias seguras. A diferencia de `to_*` (que
transforman) o `valid_*` (que verifican), aquí el valor no existía antes de
llamarlas.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeVar, overload
from uuid import uuid4

from .converters import to_str
from .validators import _allowed_chars, _check_password_args, valid_filename

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from os import PathLike
    from uuid import UUID

T = TypeVar("T")


def get_config_dir(app_name: str) -> Path:
    r"""Devuelve el directorio de configuración del usuario para una aplicación.

    La ubicación depende del sistema operativo:

    - **Linux/BSD**: `$XDG_CONFIG_HOME/<app_name>` o `~/.config/<app_name>`.
    - **macOS**: `~/Library/Application Support/<app_name>`.
    - **Windows**: `%APPDATA%\\<app_name>`.

    No crea el directorio.

    Args:
        app_name: Nombre de la aplicación; debe ser un nombre de fichero válido.

    Returns:
        Ruta al directorio de configuración (puede no existir todavía).

    Raises:
        ValueError: Si `app_name` no es un nombre de fichero válido.

    Examples:
        >>> get_config_dir("miapp").name
        'miapp'
    """
    if not valid_filename(app_name):
        raise ValueError(f"Nombre de aplicación no válido: {app_name!r}.")
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / app_name


@overload
def get_env(name: str, *, required: Literal[True]) -> str: ...
@overload
def get_env(name: str, *, default: str) -> str: ...
@overload
def get_env(
    name: str,
    *,
    default: None = None,
    required: Literal[False] = False,
) -> str | None: ...
@overload
def get_env[T](
    name: str,
    cast: Callable[[str], T | None],
    *,
    required: Literal[True],
) -> T: ...
@overload
def get_env[T](name: str, cast: Callable[[str], T | None], default: T) -> T: ...
@overload
def get_env[T](
    name: str,
    cast: Callable[[str], T | None],
    default: None = None,
    *,
    required: Literal[False] = False,
) -> T | None: ...
def get_env(
    name: str,
    cast: Callable[[str], Any] = to_str,
    default: Any = None,
    *,
    required: bool = False,
) -> Any:
    """Lee una variable de entorno y la convierte con un conversor `to_*`.

    El tipo devuelto depende de los argumentos: con `default` o
    `required=True` es el del conversor (sin `None`); en otro caso, el del
    conversor o `None`.

    Args:
        name: Nombre de la variable de entorno.
        cast: Conversor a aplicar sobre el valor leído (por defecto `to_str`).
        default: Valor a devolver si la variable falta o el conversor falla.
        required: Si es `True`, lanza `ValueError` en lugar de devolver
            `None` cuando la variable falta o no es convertible.

    Returns:
        El valor convertido, o `default` si la variable no está definida o su
        valor no es convertible por `cast`.

    Raises:
        ValueError: Si `required` es `True` y la variable falta o no es
            convertible, o si se indican a la vez `required` y `default`.

    Examples:
        >>> import os
        >>> from acodo.utils import to_int
        >>> os.environ["IRG_PORT"] = "8080"
        >>> get_env("IRG_PORT")
        '8080'
        >>> get_env("IRG_PORT", cast=to_int)
        8080
        >>> get_env("IRG_AUSENTE", default="x")
        'x'
        >>> get_env("IRG_AUSENTE", to_int, 3000)
        3000
        >>> get_env("IRG_PORT", to_int, required=True)
        8080
        >>> get_env("IRG_AUSENTE", required=True)
        Traceback (most recent call last):
            ...
        ValueError: La variable de entorno 'IRG_AUSENTE' falta o no es válida.
        >>> del os.environ["IRG_PORT"]
    """
    if required and default is not None:
        raise ValueError("`required` y `default` son incompatibles.")
    raw = os.environ.get(name)
    value = None if raw is None else cast(raw)
    if value is not None:
        return value
    if required:
        raise ValueError(f"La variable de entorno {name!r} falta o no es válida.")
    return default


def get_file_hash(
    path: str | PathLike[str],
    algorithm: str = "sha256",
) -> str:
    """Calcula el hash hexadecimal del contenido de un fichero.

    El fichero se lee por bloques, sin cargarlo entero en memoria.

    Args:
        path: Ruta del fichero cuyo hash se quiere calcular.
        algorithm: Algoritmo de `hashlib` (por ejemplo `sha256`, `sha1`).

    Returns:
        El hash en formato hexadecimal.

    Raises:
        ValueError: Si el algoritmo no está soportado por `hashlib`.
        OSError: Si el fichero no existe o no puede leerse.

    Examples:
        >>> import tempfile
        >>> from pathlib import Path
        >>> with tempfile.TemporaryDirectory() as folder:
        ...     file = Path(folder) / "abc.txt"
        ...     _ = file.write_bytes(b"abc")
        ...     get_file_hash(file, "sha1")
        'a9993e364706816aba3e25717850c26c9cd0d89d'
    """
    try:
        with Path(path).open("rb") as file:
            return hashlib.file_digest(file, algorithm).hexdigest()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Algoritmo de hash no soportado: {algorithm!r}.") from exc


def get_hash(raw: str | bytes, algorithm: str = "sha256") -> str:
    """Calcula el hash hexadecimal de un texto o de unos bytes.

    El texto se codifica en UTF-8. Para hashear un fichero usa
    `get_file_hash`.

    Args:
        raw: Texto o bytes cuyo hash se quiere calcular.
        algorithm: Algoritmo de `hashlib` (por ejemplo `sha256`, `sha1`).

    Returns:
        El hash en formato hexadecimal.

    Raises:
        ValueError: Si el algoritmo no está soportado por `hashlib`.

    Examples:
        >>> get_hash("abc")
        'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
        >>> get_hash(b"abc", "sha1")
        'a9993e364706816aba3e25717850c26c9cd0d89d'
    """
    try:
        digest = hashlib.new(algorithm)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Algoritmo de hash no soportado: {algorithm!r}.") from exc
    digest.update(raw.encode() if isinstance(raw, str) else raw)
    return digest.hexdigest()


def get_hmac(key: str | bytes, message: str | bytes, algorithm: str = "sha256") -> str:
    """Calcula el HMAC hexadecimal de un mensaje con una clave secreta.

    A diferencia de `get_hash`, usa una clave, lo que permite verificar la
    integridad y autenticidad de un mensaje, no solo su huella.

    Args:
        key: Clave secreta (texto o bytes).
        message: Mensaje a autenticar (texto o bytes).
        algorithm: Algoritmo de `hashlib` (por ejemplo `sha256`, `sha1`).

    Returns:
        El HMAC en formato hexadecimal.

    Raises:
        ValueError: Si el algoritmo no está soportado por `hashlib`.

    Examples:
        >>> get_hmac("clave", "mensaje", "sha1")
        '25dff5fc3efc225e6d8a520e32dec1c8f671b86f'
        >>> get_hmac("Jefe", "what do ya want for nothing?")
        '5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843'
    """
    try:
        hashlib.new(algorithm)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Algoritmo de hash no soportado: {algorithm!r}.") from exc

    key_bytes = key.encode() if isinstance(key, str) else key
    message_bytes = message.encode() if isinstance(message, str) else message
    return hmac.new(key_bytes, message_bytes, algorithm).hexdigest()


def get_now() -> datetime:
    """Devuelve la fecha y hora actual en UTC, con zona horaria.

    Returns:
        El `datetime` actual, consciente de zona horaria (UTC).

    Examples:
        >>> get_now().tzinfo is not None
        True
    """
    return datetime.now(UTC)


def get_otp(digits: int = 6) -> str:
    """Genera un código numérico de un solo uso (OTP) con `secrets`.

    Args:
        digits: Cantidad de dígitos del código (por defecto 6).

    Returns:
        El código, como cadena de `digits` dígitos (con ceros a la izquierda
        si es necesario).

    Raises:
        ValueError: Si `digits` es menor que 1.

    Examples:
        >>> import re
        >>> re.fullmatch(r"[0-9]{6}", get_otp()) is not None
        True
        >>> len(get_otp(8))
        8
    """
    if not isinstance(digits, int) or isinstance(digits, bool) or digits < 1:
        raise ValueError("`digits` debe ser un entero positivo.")

    return str(secrets.randbelow(10**digits)).zfill(digits)


def get_password_hash(
    password: str | bytes,
    salt: str | bytes,
    *,
    algorithm: str = "sha256",
    iterations: int = 600_000,
) -> str:
    """Deriva un hash de contraseña con PBKDF2 (`hashlib`).

    Pensado para almacenar contraseñas de forma segura, no para generarlas
    (usa `get_random_password` para eso). Es determinista: mismos `password`,
    `salt`, `algorithm` e `iterations` producen el mismo resultado, útil para
    verificar.

    Args:
        password: Contraseña a derivar (texto o bytes).
        salt: Sal (texto o bytes); debe ser única por contraseña.
        algorithm: Algoritmo HMAC de `hashlib` (por ejemplo `sha256`, `sha1`).
        iterations: Número de iteraciones (mayor = más lento y seguro).

    Returns:
        El hash derivado en formato hexadecimal.

    Raises:
        ValueError: Si el algoritmo no está soportado o `iterations` < 1.

    Examples:
        >>> hashed = get_password_hash("secreto", "sal", iterations=1000)
        >>> hashed
        '85a0d61dca9df1effa45c6540efa5f00f9511e7dfd53d8d2f1d72447ceadbfa9'
        >>> get_password_hash("secreto", "sal", iterations=1000) == hashed
        True
        >>> get_password_hash("secreto", "otra-sal", iterations=1000) == hashed
        False
    """
    if (
        not isinstance(iterations, int)
        or isinstance(iterations, bool)
        or iterations < 1
    ):
        raise ValueError("`iterations` debe ser un entero positivo.")

    password_bytes = password.encode() if isinstance(password, str) else password
    salt_bytes = salt.encode() if isinstance(salt, str) else salt

    try:
        return hashlib.pbkdf2_hmac(
            algorithm,
            password_bytes,
            salt_bytes,
            iterations,
        ).hex()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Algoritmo de hash no soportado: {algorithm!r}.") from exc


def get_random_choice[T](seq: Sequence[T]) -> T:
    """Elige un elemento al azar de una secuencia usando `secrets` (CSPRNG).

    Args:
        seq: Secuencia no vacía de la que elegir.

    Returns:
        Un elemento de `seq`, elegido de forma segura.

    Raises:
        ValueError: Si la secuencia está vacía.

    Examples:
        >>> fruta = get_random_choice(["manzana", "pera", "uva"])
        >>> fruta in ("manzana", "pera", "uva")
        True
        >>> get_random_choice([42])
        42
    """
    if not seq:
        raise ValueError("La secuencia no puede estar vacía.")
    return secrets.choice(seq)


def get_random_int(minimum: int, maximum: int) -> int:
    """Genera un entero aleatorio en el rango inclusivo con `secrets`.

    Args:
        minimum: Extremo inferior del rango (incluido).
        maximum: Extremo superior del rango (incluido).

    Returns:
        Un entero entre `minimum` y `maximum`, ambos inclusive.

    Raises:
        ValueError: Si `minimum` es mayor que `maximum`.

    Examples:
        >>> valor = get_random_int(1, 6)
        >>> 1 <= valor <= 6
        True
        >>> get_random_int(5, 5)
        5
    """
    if minimum > maximum:
        raise ValueError("El mínimo no puede ser mayor que el máximo.")
    return secrets.randbelow(maximum - minimum + 1) + minimum


def get_random_password(
    length: tuple[int, int] = (8, 16),
    special_characters: str = "",
    allow_uppercase: bool = True,
    only_digits: bool = False,
) -> str:
    """Genera una contraseña aleatoria que cumple los criterios de `valid_password`.

    Usa `secrets` (CSPRNG), nunca `random`. La longitud se elige al azar
    dentro del rango indicado y cada carácter se toma del mismo conjunto que
    admitiría `valid_password` con esos argumentos.

    Args:
        length: Rango (mínimo, máximo) de longitud, ambos inclusive.
        special_characters: Caracteres especiales permitidos.
        allow_uppercase: Mayúsculas permitidas.
        only_digits: Si solo se generan dígitos.

    Returns:
        La contraseña generada.

    Raises:
        ValueError: Si se han indicado argumentos ambiguos o incoherentes.

    Examples:
        >>> len(get_random_password(length=(12, 12)))
        12
        >>> get_random_password(length=(6, 6), only_digits=True).isdigit()
        True
        >>> from acodo.utils import valid_password
        >>> password = get_random_password(special_characters="!?")
        >>> valid_password(password, length=(8, 16), special_characters="!?")
        True
    """
    _check_password_args(length, special_characters, only_digits)
    alphabet = sorted(_allowed_chars(special_characters, allow_uppercase, only_digits))

    min_length, max_length = length
    size = secrets.randbelow(max_length - min_length + 1) + min_length
    return "".join(secrets.choice(alphabet) for _ in range(size))


def get_random_token(nbytes: int = 32, url_safe: bool = True) -> str:
    """Genera un token aleatorio criptográficamente seguro con `secrets`.

    Args:
        nbytes: Cantidad de bytes de entropía (por defecto 32).
        url_safe: Si es `True`, usa codificación URL-segura (`token_urlsafe`);
            si es `False`, genera hexadecimal (`token_hex`).

    Returns:
        El token generado.

    Raises:
        ValueError: Si `nbytes` no es un entero positivo.

    Examples:
        >>> token = get_random_token()
        >>> len(token) >= 40
        True
        >>> len(get_random_token(16, url_safe=False))
        32
    """
    if not isinstance(nbytes, int) or isinstance(nbytes, bool) or nbytes < 1:
        raise ValueError("`nbytes` debe ser un entero positivo.")

    if url_safe:
        return secrets.token_urlsafe(nbytes)
    return secrets.token_hex(nbytes)


def get_uuid() -> UUID:
    """Genera un UUID versión 4 (aleatorio) con el módulo `uuid`.

    Returns:
        Un objeto `UUID` v4.

    Examples:
        >>> from acodo.utils import valid_uuid
        >>> valid_uuid(str(get_uuid()))
        True
    """
    return uuid4()
