from pathlib import Path

import pytest

from acodo_cli.config import ConfigError, find_pyproject, load_config


def write_pyproject(directory: Path, content: str) -> Path:
    path = directory / "pyproject.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_defaults_without_tool_section(tmp_path: Path) -> None:
    write_pyproject(tmp_path, '[project]\nname = "demo"\n')

    cfg = load_config(tmp_path)

    assert cfg.root == tmp_path.resolve()
    assert cfg.project_name == "demo"
    assert cfg.src_dir == "src"
    assert cfg.test_dir == "tests"
    assert cfg.python_version == ">=3.13"
    assert cfg.src == tmp_path.resolve() / "src"
    assert cfg.tests == tmp_path.resolve() / "tests"


def test_reads_tool_section(tmp_path: Path) -> None:
    write_pyproject(
        tmp_path,
        '[tool.acodo-cli]\nsrc-dir = "lib"\ntest-dir = "pruebas"\n'
        'python-version = ">=3.14"\n',
    )

    cfg = load_config(tmp_path)

    assert (cfg.src_dir, cfg.test_dir, cfg.python_version) == (
        "lib",
        "pruebas",
        ">=3.14",
    )
    assert cfg.project_name == tmp_path.resolve().name


def test_finds_pyproject_in_parent_directories(tmp_path: Path) -> None:
    pyproject = write_pyproject(tmp_path, "")
    child = tmp_path / "a" / "b"
    child.mkdir(parents=True)

    assert find_pyproject(child) == pyproject
    assert load_config(child).root == tmp_path.resolve()


def test_missing_pyproject_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"pyproject\.toml"):
        load_config(tmp_path)


def test_invalid_toml_raises(tmp_path: Path) -> None:
    write_pyproject(tmp_path, "esto = = no es toml")

    with pytest.raises(ConfigError, match="TOML"):
        load_config(tmp_path)


@pytest.mark.parametrize(
    "content",
    [
        "[tool.acodo-cli]\nsrc-dir = 3\n",
        '[tool.acodo-cli]\ntest-dir = ""\n',
        'tool = { acodo-cli = "texto" }\n',
    ],
)
def test_invalid_values_raise(tmp_path: Path, content: str) -> None:
    write_pyproject(tmp_path, content)

    with pytest.raises(ConfigError):
        load_config(tmp_path)
