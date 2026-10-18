from pathlib import Path

from typer.testing import CliRunner

from acodo_cli.cli import app
from acodo_cli.commands.code_count import _count_file_lines, _get_docstring_lines
from acodo_cli.models import Category, LineStats

# ---------------------------------------------------------------------------
#  Modelos
# ---------------------------------------------------------------------------


def test_line_stats_add() -> None:
    result = LineStats(code=10, docstrings=5) + LineStats(code=3, docstrings=2)

    assert result.code == 13
    assert result.docstrings == 7
    assert result.total == 20


def test_category_totals() -> None:
    cat = Category(name="scripts")
    cat.files = [
        (Path("a.py"), LineStats(code=10, docstrings=5)),
        (Path("b.py"), LineStats(code=3, docstrings=2)),
    ]

    assert cat.totals == LineStats(code=13, docstrings=7)


# ---------------------------------------------------------------------------
#  Docstrings y conteo
# ---------------------------------------------------------------------------


def test_get_docstring_lines_single_line() -> None:
    assert _get_docstring_lines('"""modulo docstring"""\nx = 1\n') == {1}


def test_get_docstring_lines_multiline() -> None:
    assert _get_docstring_lines('"""doc\nmulti\n"""\nx = 1\n') == {1, 2, 3}


def test_get_docstring_lines_class_and_function() -> None:
    content = (
        '"""modulo"""\n'
        "class C:\n"
        '    """clase"""\n'
        "    def m(self):\n"
        '        """funcion"""\n'
        "        pass\n"
    )

    assert _get_docstring_lines(content) == {1, 3, 5}


def test_get_docstring_lines_none() -> None:
    assert _get_docstring_lines("x = 1\n# comentario\n") == set()


def test_get_docstring_lines_syntax_error() -> None:
    assert _get_docstring_lines("x =\n") == set()


def test_count_file_lines(tmp_path: Path) -> None:
    path = tmp_path / "sample.py"
    path.write_text(
        '"""documento de modulo"""\n'
        "x = 1\n"
        "# comentario ordinario\n"
        "\n"
        "def f():\n"
        '    """doc de funcion"""\n'
        "    return x\n",
        encoding="utf-8",
    )

    stats = _count_file_lines(path)

    assert stats.code == 3  # x = 1, def f():, return x
    assert stats.docstrings == 2  # doc de modulo, doc de funcion
    assert stats.total == 5


def test_count_file_lines_ignores_comments_and_blanks(tmp_path: Path) -> None:
    path = tmp_path / "sample.py"
    path.write_text("# solo comentario\n\n   \nx = 1\n", encoding="utf-8")

    assert _count_file_lines(path) == LineStats(code=1, docstrings=0)


# ---------------------------------------------------------------------------
#  Comando
# ---------------------------------------------------------------------------


def test_command_prints_summary(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["code-count"], input="n\n")

    assert result.exit_code == 0
    assert "Resumen por directorio" in result.output
    assert "2 ficheros procesados" in result.output
    assert "src/" in result.output
    assert "main.py" not in result.output


def test_command_lists_files_when_asked(project: Path, runner: CliRunner) -> None:
    result = runner.invoke(app, ["code-count"], input="y\n")

    assert result.exit_code == 0
    assert "main.py" in result.output


def test_command_does_not_ask_without_files(project: Path, runner: CliRunner) -> None:
    for path in (project / "src").rglob("*.py"):
        path.unlink()

    result = runner.invoke(app, ["code-count"])

    assert result.exit_code == 0
    assert "0 ficheros procesados" in result.output


def test_workspace_layout_counts_each_file_once(
    project: Path, runner: CliRunner
) -> None:
    (project / "packages").mkdir()
    (project / "packages" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (project / "acodo.toml").write_text(
        '[all]\ninclude = ["packages/"]\n', encoding="utf-8"
    )

    result = runner.invoke(app, ["code-count"], input="n\n")

    assert "1 ficheros procesados" in result.output


def test_exclude_skips_files(project: Path, runner: CliRunner) -> None:
    (project / "acodo.toml").write_text(
        '[all]\ninclude = ["src/"]\nexclude = ["main.py"]\n', encoding="utf-8"
    )

    result = runner.invoke(app, ["code-count"], input="n\n")

    assert "1 ficheros procesados" in result.output
