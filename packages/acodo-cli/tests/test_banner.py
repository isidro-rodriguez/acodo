import pytest
from typer.testing import CliRunner

from acodo_cli import __version__
from acodo_cli.banner import ASCII_ART, gradient_art
from acodo_cli.cli import app
from acodo_cli.theme import PALETTE


def test_gradient_art_keeps_the_art_text() -> None:
    text = gradient_art(PALETTE["green"], PALETTE["light_green"])

    assert [line.rstrip() for line in text.plain.splitlines()] == [
        line.rstrip() for line in ASCII_ART.splitlines()
    ]


def test_gradient_art_goes_from_start_to_end_color() -> None:
    text = gradient_art("#000000", "#FFFFFF")
    colors = [str(span.style) for span in text.spans]

    assert colors[0] == "#000000"
    assert int(colors[-1][1:3], 16) > 0xF0


def test_version_flag_shows_versions_and_exits(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output
    assert "Python" in result.output


def test_no_args_shows_banner_and_help(runner: CliRunner) -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert "╚═╝" in result.output
    assert "Usage" in result.output


@pytest.mark.parametrize("argument", ["--help"])
def test_help_lists_version_option(runner: CliRunner, argument: str) -> None:
    assert "--version" in runner.invoke(app, [argument]).output
