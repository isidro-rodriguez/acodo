"""Tests estructurales del paquete acodo.utils."""

import ast
import pathlib
from types import ModuleType

import acodo.utils as iu
from acodo.utils import checkers, converters, getters, parsers, types, validators

MODULES = (converters, checkers, parsers, validators, getters, types)
PREFIXES = ("to_", "has_", "parse_", "valid_", "get_")


def test_all_lists_the_modules() -> None:
    modules = [module.__name__.rpartition(".")[2] for module in MODULES]
    assert iu.__all__ == sorted(modules)
    assert all(isinstance(getattr(iu, name), ModuleType) for name in iu.__all__)


def _public_names(module: ModuleType) -> list[str]:
    # `dict.fromkeys` elimina duplicados conservando el orden: las sobrecargas
    # (`@overload`) repiten el nombre de la función.
    tree = ast.parse(pathlib.Path(str(module.__file__)).read_text(encoding="utf-8"))
    return list(
        dict.fromkeys(
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef | ast.ClassDef)
            and not node.name.startswith("_")
        )
    )


def test_public_names_are_reexported() -> None:
    for module in MODULES:
        for name in _public_names(module):
            assert getattr(iu, name) is getattr(module, name), name


def test_reexports_use_redundant_alias() -> None:
    # `from .x import f as f` declara la reexportación para los verificadores de
    # tipos (el paquete lleva `py.typed`).
    tree = ast.parse(pathlib.Path(str(iu.__file__)).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            assert all(a.asname == a.name for a in node.names), node.module


def test_public_functions_are_alphabetical_per_prefix() -> None:
    for module in MODULES:
        public = _public_names(module)
        for prefix in PREFIXES:
            names = [name for name in public if name.startswith(prefix)]
            assert names == sorted(names), (module.__name__, prefix)
