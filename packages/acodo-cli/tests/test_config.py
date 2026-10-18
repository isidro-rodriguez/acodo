from pathlib import Path

import pytest

from acodo_cli.config import (
    ConfigError,
    default_acodo_toml,
    find_acodo_toml,
    load_config,
)
from acodo_cli.models import OutputConfig, Scope


def write_acodo_toml(directory: Path, content: str) -> Path:
    path = directory / "acodo.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_default_acodo_toml_loads_with_the_documented_defaults(tmp_path: Path) -> None:
    write_acodo_toml(tmp_path, default_acodo_toml())

    cfg = load_config(tmp_path)

    assert cfg.root == tmp_path.resolve()
    assert cfg.scopes["all"].include == ("scripts/", "src/", "tests/")
    assert cfg.backup == OutputConfig(".local/backup.zip", version_suffix=True)
    assert cfg.api == OutputConfig(".local/api.md", version_suffix=True)
    assert cfg.gh_config_file == ".local/gh_app.json"


def test_empty_acodo_toml_uses_defaults(tmp_path: Path) -> None:
    write_acodo_toml(tmp_path, "")

    cfg = load_config(tmp_path)

    assert cfg.scopes["lint"] == Scope()
    assert cfg.project_name == tmp_path.resolve().name
    assert (cfg.version, cfg.requires_python) == ("", "")


def test_sections_add_to_all(tmp_path: Path) -> None:
    write_acodo_toml(
        tmp_path,
        '[all]\ninclude = ["src/", "tests/"]\nexclude = [".venv"]\n'
        '[lint]\ninclude = ["scripts/"]\nexclude = [".venv", "build/"]\n',
    )

    scopes = load_config(tmp_path).scopes

    assert scopes["lint"] == Scope(
        include=("src/", "tests/", "scripts/"), exclude=(".venv", "build/")
    )
    assert scopes["format"] == Scope(include=("src/", "tests/"), exclude=(".venv",))
    assert scopes["all"] == Scope(include=("src/", "tests/"), exclude=(".venv",))


def test_reads_outputs_and_github_app(tmp_path: Path) -> None:
    write_acodo_toml(
        tmp_path,
        '[backup]\ntarget = "out/b.tar.gz"\nversion_suffix = false\n'
        '[api]\ntarget = "docs/api.md"\n'
        '[github_app]\nconfig_file = "gh.json"\n',
    )

    cfg = load_config(tmp_path)

    assert cfg.backup == OutputConfig("out/b.tar.gz", version_suffix=False)
    assert cfg.api == OutputConfig("docs/api.md", version_suffix=True)
    assert cfg.gh_config_file == "gh.json"


def test_reads_project_metadata_from_pyproject(tmp_path: Path) -> None:
    write_acodo_toml(tmp_path, "")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "1.2.0"\nrequires-python = ">=3.14"\n',
        encoding="utf-8",
    )

    cfg = load_config(tmp_path)

    assert (cfg.project_name, cfg.version, cfg.requires_python) == (
        "demo",
        "1.2.0",
        ">=3.14",
    )


def test_tool_acodo_cli_in_pyproject_is_ignored(tmp_path: Path) -> None:
    write_acodo_toml(tmp_path, '[all]\ninclude = ["lib/"]\n')
    (tmp_path / "pyproject.toml").write_text(
        '[tool.acodo-cli]\nsrc-dir = "otro"\n', encoding="utf-8"
    )

    assert load_config(tmp_path).scopes["all"].include == ("lib/",)


def test_scope_dirs_only_returns_existing_directories(tmp_path: Path) -> None:
    write_acodo_toml(tmp_path, '[all]\ninclude = ["src/", "falta/"]\n')
    (tmp_path / "src").mkdir()

    assert load_config(tmp_path).scope_dirs("lint") == [tmp_path.resolve() / "src"]


def test_finds_acodo_toml_in_parent_directories(tmp_path: Path) -> None:
    path = write_acodo_toml(tmp_path, "")
    child = tmp_path / "a" / "b"
    child.mkdir(parents=True)

    assert find_acodo_toml(child) == path
    assert load_config(child).root == tmp_path.resolve()


def test_missing_acodo_toml_suggests_init(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match=r"acodo\.toml.*acodo init"):
        load_config(tmp_path)


def test_invalid_toml_raises(tmp_path: Path) -> None:
    write_acodo_toml(tmp_path, "esto = = no es toml")

    with pytest.raises(ConfigError, match="TOML"):
        load_config(tmp_path)


@pytest.mark.parametrize(
    "content",
    [
        '[all]\ninclude = "src/"\n',
        "[lint]\nexclude = [1]\n",
        '[types]\ninclude = [""]\n',
        "all = 3\n",
        "[backup]\ntarget = 3\n",
        '[api]\nversion_suffix = "si"\n',
        '[github_app]\nconfig_file = ""\n',
    ],
)
def test_invalid_values_raise(tmp_path: Path, content: str) -> None:
    write_acodo_toml(tmp_path, content)

    with pytest.raises(ConfigError):
        load_config(tmp_path)
