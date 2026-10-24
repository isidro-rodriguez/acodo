"""Comprobaciones: verifican que los objetos cumplan los requisitos.

Las funciones `has_*` devuelven `bool`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection, Hashable, Iterable, Mapping
    from typing import Any


# =============================================================================
#  Comprobaciones
# =============================================================================


def has_required_attrs(raw: object, required_attrs: Iterable[str]) -> bool:
    """Comprueba que el objeto tiene todos los atributos requeridos.

    Args:
        raw: Objeto a verificar.
        required_attrs: Nombres de los atributos requeridos.

    Returns:
        `True` si el objeto tiene todos los atributos requeridos.

    Examples:
        >>> has_required_attrs("texto", ["upper", "lower"])
        True
        >>> has_required_attrs("texto", ["append"])
        False
    """
    return all(hasattr(raw, attr) for attr in required_attrs)


def has_required_fields(
    raw: Collection[Any],
    required_fields: Iterable[Any],
) -> bool:
    """Comprueba que la colección tiene todos los campos requeridos.

    Args:
        raw: Colección a verificar.
        required_fields: Campos requeridos.

    Returns:
        `True` si la colección tiene todos los campos requeridos.

    Examples:
        >>> has_required_fields(["a", "b", "c"], ["a", "c"])
        True
        >>> has_required_fields({"a", "b"}, ["a", "z"])
        False
    """
    return all(field in raw for field in required_fields)


def has_required_keys(
    raw: Mapping[Hashable, Any],
    required_keys: Iterable[Hashable],
) -> bool:
    """Comprueba que el diccionario tiene todas las llaves requeridas.

    Args:
        raw: Diccionario a verificar.
        required_keys: Llaves requeridas.

    Returns:
        `True` si el diccionario tiene todas las llaves requeridas.

    Examples:
        >>> has_required_keys({"name": "Ana", "age": 30}, ["name"])
        True
        >>> has_required_keys({"name": "Ana"}, ["name", "age"])
        False
    """
    return all(key in raw for key in required_keys)
