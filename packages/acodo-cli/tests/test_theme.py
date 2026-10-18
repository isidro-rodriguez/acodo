import re
from pathlib import Path

import pytest
from rich.style import Style
from typer import rich_utils

import acodo_cli
from acodo_cli.theme import ACODO_STYLES, PALETTE, apply_typer_styles

SRC = Path(acodo_cli.__file__).parent
STYLE_NAME_RE = re.compile(r"(?:title_|border_|guide_)?style=\"([\w.]+)\"")
MARKUP_RE = re.compile(r"\[([a-z][a-z.]*)\][^\[\n]*\[/\]")
PALETTE_HEXES = {color.casefold() for color in PALETTE.values()}


def test_theme_only_uses_palette_colors() -> None:
    for name, style in ACODO_STYLES.items():
        color = Style.parse(style).color
        assert color is not None, name
        assert color.get_truecolor().hex.casefold() in PALETTE_HEXES, name


def test_named_styles_in_code_exist_in_theme() -> None:
    used = {
        match
        for path in SRC.rglob("*.py")
        for match in STYLE_NAME_RE.findall(path.read_text(encoding="utf-8"))
    }

    assert used
    assert used <= set(ACODO_STYLES)


def test_markup_tags_in_code_exist_in_theme() -> None:
    # Los tags de Rich que se cierran con `[/]` deben ser estilos del tema.
    used = {
        match
        for path in SRC.rglob("*.py")
        for match in MARKUP_RE.findall(path.read_text(encoding="utf-8"))
    }

    assert {"ok", "error", "title"} <= used
    assert used <= set(ACODO_STYLES)


def test_apply_typer_styles_uses_palette(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rich_utils, "STYLE_OPTION", "x")

    apply_typer_styles()

    assert PALETTE["light_green"] == rich_utils.STYLE_OPTION
