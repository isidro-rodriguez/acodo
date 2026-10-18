from typer.testing import CliRunner

from acodo_cli import __version__
from acodo_cli.banner import (
    ASCII_ART,
    GRADIENT_STOPS,
    build_version_panel,
    gradient_color,
    render_art,
)
from acodo_cli.cli import app
from acodo_cli.theme import ACODO_THEME


def test_render_art_keeps_the_art_text() -> None:
    assert render_art().plain == ASCII_ART.rstrip("\n")


def test_gradient_color_hits_the_stops() -> None:
    stops = [(0, 0, 0), (100, 100, 100), (200, 200, 200)]

    assert gradient_color(0.0, stops) == (0, 0, 0)
    assert gradient_color(0.5, stops) == (100, 100, 100)
    assert gradient_color(1.0, stops) == (200, 200, 200)


def test_gradient_color_clamps_out_of_range_positions() -> None:
    stops = [(0, 0, 0), (10, 10, 10)]

    assert gradient_color(-1, stops) == (0, 0, 0)
    assert gradient_color(2, stops) == (10, 10, 10)


def test_gradient_stops_are_palette_colors() -> None:
    assert set(GRADIENT_STOPS) <= set(ACODO_THEME)


def test_version_panel_shows_version() -> None:
    panel = build_version_panel()

    assert panel.border_style == "border"


def test_version_flag_shows_version_and_exits(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output
    assert "Python" in result.output
