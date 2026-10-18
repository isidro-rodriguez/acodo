import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import jwt
import pytest
import typer
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from acodo_cli.commands_service import (
    build_jwt,
    find_pycache,
    is_excluded,
    load_gh_config,
    load_private_key,
    normalize_repo,
    output_path,
    resolve_api_url,
    run,
    scope_files,
)
from acodo_cli.config import load_config
from acodo_cli.models import AcodoConfig, OutputConfig

VALID_CONFIG = {
    "repository": "owner/repo",
    "app-id": "123456",
    "private-key": "private-key.pem",
    "installation-id": "12345678",
}


@pytest.fixture(scope="module")
def rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def private_pem(rsa_key: rsa.RSAPrivateKey) -> str:
    return rsa_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


# ---------------------------------------------------------------------------
#  Comunes
# ---------------------------------------------------------------------------


def test_run_returns_exit_code_and_uses_cwd(tmp_path: Path) -> None:
    code = run(
        [sys.executable, "-c", "import sys; sys.exit(int(len(sys.argv) == 1) + 4)"],
        tmp_path,
    )

    assert code == 5


@pytest.mark.parametrize(
    ("relative", "patterns", "expected"),
    [
        ("src/.venv/x.py", [".venv"], True),
        ("src/a.py", [".venv"], False),
        ("docs/api/a.md", ["docs/api/"], True),
        ("docs/apis/a.md", ["docs/api"], False),
        ("src/pkg/a_test.py", ["*_test.py"], True),
        (".github/x.yml", [".git"], False),
        ("src/a.py", [], False),
    ],
)
def test_is_excluded(relative: str, patterns: list[str], expected: bool) -> None:
    assert is_excluded(Path(relative), patterns) is expected


def make_config(root: Path, content: str) -> AcodoConfig:
    (root / "acodo.toml").write_text(content, encoding="utf-8")
    return load_config(root)


def test_scope_files_respects_include_suffix_and_exclude(tmp_path: Path) -> None:
    for name in ("src/a.py", "src/b.txt", "src/skip/c.py", "lib/d.py", "otro/e.py"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("")
    cfg = make_config(
        tmp_path,
        '[all]\ninclude = ["src/", "src/", "falta/"]\nexclude = ["skip"]\n'
        '[lint]\ninclude = ["lib/"]\n',
    )

    found = [
        p.relative_to(cfg.root).as_posix() for p in scope_files(cfg, "lint", ".py")
    ]

    assert found == ["src/a.py", "lib/d.py"]


def test_find_pycache_skips_excluded_paths(tmp_path: Path) -> None:
    (tmp_path / "src" / "__pycache__").mkdir(parents=True)
    (tmp_path / "src" / ".venv" / "__pycache__").mkdir(parents=True)
    cfg = make_config(tmp_path, '[all]\ninclude = ["src/"]\nexclude = [".venv"]\n')

    assert find_pycache(cfg) == [cfg.root / "src" / "__pycache__"]


@pytest.mark.parametrize(
    ("target", "version", "suffix", "expected"),
    [
        ("b.zip", "1.2.0", True, "b-1.2.0.zip"),
        ("out/b.tar.gz", "1.2.0", True, "out/b-1.2.0.tar.gz"),
        ("b.zip", "1.2.0", False, "b.zip"),
        ("b.zip", "", True, "b.zip"),
    ],
)
def test_output_path(
    tmp_path: Path, target: str, version: str, suffix: bool, expected: str
) -> None:
    cfg = make_config(tmp_path, "")
    cfg = replace(cfg, version=version)

    assert output_path(cfg, OutputConfig(target, suffix)) == cfg.root / expected


# ---------------------------------------------------------------------------
#  Configuración de la GitHub App
# ---------------------------------------------------------------------------


def write_config(tmp_path: Path, cfg: dict[str, str]) -> Path:
    path = tmp_path / "gh_app.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_load_gh_config_returns_valid_config(tmp_path: Path) -> None:
    assert load_gh_config(write_config(tmp_path, VALID_CONFIG)) == VALID_CONFIG


@pytest.mark.parametrize("missing", list(VALID_CONFIG))
def test_load_gh_config_requires_every_key(tmp_path: Path, missing: str) -> None:
    cfg = {k: v for k, v in VALID_CONFIG.items() if k != missing}

    with pytest.raises(typer.Exit):
        load_gh_config(write_config(tmp_path, cfg))


def test_load_gh_config_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(typer.Exit):
        load_gh_config(tmp_path / "no_existe.json")


def test_load_gh_config_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "gh_app.json"
    path.write_text("{no es json", encoding="utf-8")

    with pytest.raises(typer.Exit):
        load_gh_config(path)


def test_load_gh_config_rejects_non_object(tmp_path: Path) -> None:
    path = tmp_path / "gh_app.json"
    path.write_text("[1, 2]", encoding="utf-8")

    with pytest.raises(typer.Exit):
        load_gh_config(path)


@pytest.mark.parametrize(
    ("cfg", "expected"),
    [
        ({}, "https://api.github.com"),
        (
            {"api-url": "https://ghe.example.com/api/v3/"},
            "https://ghe.example.com/api/v3",
        ),
    ],
)
def test_resolve_api_url(cfg: dict[str, Any], expected: str) -> None:
    assert resolve_api_url(cfg) == expected


def test_resolve_api_url_rejects_invalid() -> None:
    with pytest.raises(typer.Exit):
        resolve_api_url({"api-url": "htp:/mal"})


# ---------------------------------------------------------------------------
#  Repositorio y clave privada
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        "owner/repo",
        "https://github.com/owner/repo.git",
        "https://www.github.com/owner/repo?tab=x",
        "git@github.com:owner/repo.git",
    ],
)
def test_normalize_repo_accepts_slug_and_urls(raw: str) -> None:
    assert normalize_repo(raw) == "owner/repo"


@pytest.mark.parametrize("raw", ["no-es-un-repo", "https://github.com/-abc/repo"])
def test_normalize_repo_rejects_invalid(raw: str) -> None:
    with pytest.raises(ValueError, match="repositorio"):
        normalize_repo(raw)


def test_load_private_key_reads_file_next_to_config(
    tmp_path: Path, private_pem: str
) -> None:
    (tmp_path / "private-key.pem").write_text(private_pem, encoding="utf-8")

    key = load_private_key("private-key.pem", tmp_path / "gh_app.json")

    assert key == private_pem


def test_load_private_key_accepts_embedded_pem_with_escaped_newlines(
    tmp_path: Path, private_pem: str
) -> None:
    embedded = private_pem.replace("\n", "\\n")

    assert load_private_key(embedded, tmp_path / "gh_app.json") == private_pem


def test_load_private_key_embedded_pem_with_long_base64_run(tmp_path: Path) -> None:
    # Más de 255 caracteres seguidos sin "/" harían fallar a `Path.is_file()`.
    embedded = (
        "-----BEGIN PRIVATE KEY-----\\n" + "A" * 300 + "\\n-----END PRIVATE KEY-----"
    )

    key = load_private_key(embedded, tmp_path / "gh_app.json")

    assert key == embedded.replace("\\n", "\n")


def test_load_private_key_rejects_garbage(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="clave privada"):
        load_private_key("no-existe.pem", tmp_path / "gh_app.json")


# ---------------------------------------------------------------------------
#  JWT
# ---------------------------------------------------------------------------


def test_build_jwt_is_signed_with_the_private_key(
    rsa_key: rsa.RSAPrivateKey, private_pem: str
) -> None:
    token = build_jwt("123456", private_pem)

    claims = jwt.decode(token, rsa_key.public_key(), algorithms=["RS256"])
    assert claims["iss"] == "123456"
    assert claims["exp"] - claims["iat"] <= 600  # GitHub exige menos de 10 minutos


def test_build_jwt_rejects_garbage_key() -> None:
    with pytest.raises(ValueError, match="JWT"):
        build_jwt("123456", "no-es-una-clave")


def test_build_jwt_rejects_public_key(rsa_key: rsa.RSAPrivateKey) -> None:
    public_pem = rsa_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with pytest.raises(ValueError, match="JWT"):
        build_jwt("123456", public_pem.decode())


def test_build_jwt_rejects_encrypted_key(rsa_key: rsa.RSAPrivateKey) -> None:
    encrypted = rsa_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(b"secreto"),
    )

    with pytest.raises(ValueError, match="JWT"):
        build_jwt("123456", encrypted.decode())
