import re
from pathlib import Path

import pytest
from rich.style import Style
from typer import rich_utils

import acodo_cli
from acodo_cli.theme import (
    ACODO_THEME,
    SEMANTIC_STYLES,
    THEME,
    TYPER_STYLES,
    apply_typer_styles,
)

SRC = Path(acodo_cli.__file__).parent
STYLE_NAME_RE = re.compile(r"(?:title_|border_|guide_)?style=\"([\w.]+)\"")
MARKUP_RE = re.compile(r"\[([a-z][a-z.]*)\][^\[\n]*\[/\]")
PALETTE_HEXES = {color.casefold() for color in ACODO_THEME.values()}


def _hexes(style: str) -> set[str]:
    parsed = Style.parse(style)
    return {
        color.get_truecolor().hex.casefold()
        for color in (parsed.color, parsed.bgcolor)
        if color is not None
    }


def test_semantic_styles_only_use_palette_colors() -> None:
    for name, style in SEMANTIC_STYLES.items():
        assert _hexes(style) <= PALETTE_HEXES, name


def test_typer_styles_only_use_palette_colors() -> None:
    for name, style in TYPER_STYLES.items():
        assert _hexes(style) <= PALETTE_HEXES, name


def test_theme_contains_palette_and_semantic_styles() -> None:
    assert set(ACODO_THEME) | set(SEMANTIC_STYLES) <= set(THEME.styles)


def test_named_styles_in_code_exist_in_theme() -> None:
    used = {
        match
        for path in SRC.rglob("*.py")
        for match in STYLE_NAME_RE.findall(path.read_text(encoding="utf-8"))
    }

    assert used
    assert used <= set(THEME.styles)


def test_markup_tags_in_code_exist_in_theme() -> None:
    used = {
        match
        for path in SRC.rglob("*.py")
        for match in MARKUP_RE.findall(path.read_text(encoding="utf-8"))
    }

    assert {"ok", "error", "title"} <= used
    assert used <= set(THEME.styles)


def test_apply_typer_styles_uses_palette(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rich_utils, "STYLE_OPTION", "x")

    apply_typer_styles()

    assert TYPER_STYLES["STYLE_OPTION"] == rich_utils.STYLE_OPTION
    assert ACODO_THEME["light_green"] in rich_utils.RICH_HELP
