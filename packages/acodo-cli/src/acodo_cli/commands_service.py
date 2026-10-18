"""Lógica común a los comandos: consolas, errores, procesos y GitHub App."""

import json
import re
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Iterator, Sequence
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, NoReturn

import jwt
import typer
from rich.console import Console
from rich.markup import escape

from acodo.utils import valid_social_url, valid_url
from acodo.utils.types import SocialLink
from acodo_cli.config import ConfigError, load_config
from acodo_cli.models import AcodoConfig, OutputConfig
from acodo_cli.theme import THEME

console = Console(theme=THEME, highlight=False)
err_console = Console(theme=THEME, highlight=False, stderr=True)

DEFAULT_API_URL = "https://api.github.com"
JWT_LIFETIME = 480  # 8 min: margen bajo el máximo de 10 min de GitHub.
REPO_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")

GH_CONFIG_TEMPLATE: dict[str, str] = {
    "repository": "owner/repo",
    "app-id": "123456",
    "private-key": "private-key.pem",
    "installation-id": "12345678",
    "api-url": "https://api.github.com",
}
"""Plantilla del JSON de configuración de la GitHub App."""


# =============================================================================
#  Comunes
# =============================================================================


def fail(message: str) -> NoReturn:
    """Imprime un error y aborta con código 1."""
    err_console.print(f"[error]Error:[/] {escape(message)}")
    raise typer.Exit(code=1)


def is_global_install(prefix: Path, base_prefix: Path) -> bool:
    """Indica si el CLI corre fuera del entorno virtual de un proyecto.

    Detecta Python global (sin entorno virtual) y los entornos aislados de
    `uv tool install` y `pipx`, donde no están ruff, ty ni pytest del proyecto.

    Args:
        prefix: Prefijo del entorno actual (`sys.prefix`).
        base_prefix: Prefijo del intérprete base (`sys.base_prefix`).

    Returns:
        `True` si es una instalación global o como herramienta.
    """
    return (
        prefix == base_prefix
        or (prefix / "uv-receipt.toml").is_file()
        or (prefix / "pipx_metadata.json").is_file()
    )


def get_config() -> AcodoConfig:
    """Carga la configuración del proyecto actual o aborta con un error claro."""
    try:
        return load_config()
    except ConfigError as exc:
        fail(str(exc))


def output_path(cfg: AcodoConfig, output: OutputConfig) -> Path:
    """Ruta absoluta del fichero generado, con la versión si `version_suffix`.

    Con `backup.zip` y versión `1.2.0` devuelve `backup-1.2.0.zip`; con
    `backup.tar.gz`, `backup-1.2.0.tar.gz`.
    """
    target = cfg.root / output.target
    if not (output.version_suffix and cfg.version):
        return target
    extension = ".tar.gz" if target.name.endswith(".tar.gz") else target.suffix
    stem = target.name.removesuffix(extension)
    return target.with_name(f"{stem}-{cfg.version}{extension}")


def run(command: Sequence[str], cwd: Path) -> int:
    """Ejecuta `command` en `cwd` y devuelve su código de salida."""
    return subprocess.run(command, cwd=cwd, check=False).returncode


def is_excluded(relative: Path, patterns: Sequence[str]) -> bool:
    """Indica si `relative` (ruta desde la raíz) encaja con algún patrón `exclude`.

    Un patrón sin `/` interior (p. ej. `.venv`) se compara con cada componente
    de la ruta; uno con `/` (p. ej. `docs/api`) con su comienzo.

    Examples:
        >>> is_excluded(Path("src/.venv/x.py"), [".venv"])
        True
        >>> is_excluded(Path("docs/api/a.md"), ["docs/api/"])
        True
        >>> is_excluded(Path("src/a.py"), [".venv"])
        False
    """
    posix = relative.as_posix()
    for raw in patterns:
        pattern = raw.strip("/")
        if "/" in pattern:
            if fnmatch(posix, pattern) or posix.startswith(f"{pattern}/"):
                return True
        elif any(fnmatch(part, pattern) for part in relative.parts):
            return True
    return False


def scope_files(cfg: AcodoConfig, name: str, suffix: str = "") -> Iterator[Path]:
    """Recorre los ficheros de la sección `name`, ordenados y sin duplicados.

    Args:
        cfg: Configuración del proyecto.
        name: Sección de `acodo.toml` (`lint`, `todo`, `backup`...).
        suffix: Si no está vacío, solo ficheros con esta extensión (`.py`).
    """
    exclude = cfg.scopes[name].exclude
    seen: set[Path] = set()
    for directory in cfg.scope_dirs(name):
        for path in sorted(directory.rglob(f"*{suffix}")):
            if path in seen or not path.is_file():
                continue
            if is_excluded(path.relative_to(cfg.root), exclude):
                continue
            seen.add(path)
            yield path


def find_pycache(cfg: AcodoConfig) -> list[Path]:
    """Localiza los `__pycache__` de las rutas de `[all]`, respetando `exclude`."""
    exclude = cfg.scopes["all"].exclude
    return [
        cache
        for directory in cfg.scope_dirs("all")
        for cache in sorted(directory.rglob("__pycache__"))
        if cache.is_dir() and not is_excluded(cache.relative_to(cfg.root), exclude)
    ]


# =============================================================================
#  GitHub App (gh-token y gh-check)
# =============================================================================


def gh_config_path(cfg: AcodoConfig) -> Path:
    """Ruta del JSON de la GitHub App según `[github_app]` de `acodo.toml`."""
    return cfg.root / cfg.gh_config_file


def fail_gh(message: str) -> NoReturn:
    """Imprime un error con la plantilla del JSON y aborta."""
    err_console.print(f"[error]Error:[/] {escape(message)}")
    err_console.print()
    err_console.print("[title]Plantilla esperada del fichero de configuración:[/]")
    err_console.print(json.dumps(GH_CONFIG_TEMPLATE, indent=2, ensure_ascii=False))
    raise typer.Exit(code=1)


def load_gh_config(path: Path) -> dict[str, Any]:
    """Lee y valida el JSON de configuración de la GitHub App."""
    if not path.is_file():
        fail_gh(f"No se encontró el fichero de configuración: {path}")
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail_gh(f"{path} no es un JSON válido: {exc}")
    except OSError as exc:
        fail_gh(f"No se pudo leer {path}: {exc.strerror}")

    if not isinstance(cfg, dict):
        fail_gh(f"{path} debe contener un objeto JSON en la raíz.")

    for key in ("repository", "app-id", "private-key", "installation-id"):
        if not cfg.get(key):
            fail_gh(f"Falta la clave '{key}' en {path}.")
    return cfg


def resolve_api_url(cfg: dict[str, Any]) -> str:
    """Devuelve la URL base de la API, validada, o la de github.com."""
    raw = cfg.get("api-url") or DEFAULT_API_URL
    api_url = str(raw).rstrip("/")
    if not valid_url(api_url):
        fail_gh(f"La clave 'api-url' no es una URL http/https válida: {raw!r}.")
    return api_url


def load_private_key(raw: str, config_path: Path) -> str:
    """Acepta ruta absoluta, relativa al JSON, o el PEM embebido."""
    # El PEM se comprueba antes que las rutas: con un PEM largo, `Path.is_file()`
    # lanza OSError ("File name too long") en Linux y macOS.
    if "BEGIN" in raw and "PRIVATE KEY" in raw:
        return raw.replace("\\n", "\n")
    candidate = Path(raw).expanduser()
    if candidate.is_file():
        return candidate.read_text(encoding="utf-8")
    local_candidate = config_path.parent / raw
    if local_candidate.is_file():
        return local_candidate.read_text(encoding="utf-8")
    raise ValueError("La clave privada no es un fichero legible ni un PEM válido.")


def normalize_repo(raw: str) -> str:
    """Acepta `owner/repo` o URL de GitHub y devuelve `owner/repo`."""
    value = raw.strip()
    looks_like_url = (
        "github.com" in value.casefold() or "://" in value or value.startswith("www.")
    ) and not value.startswith("git@github.com:")
    if looks_like_url and not valid_social_url(value, SocialLink.GITHUB_REPO):
        raise ValueError(
            f"'{raw}' no parece un repositorio válido (usa 'owner/repo' o la URL)."
        )
    for prefix in (
        "https://github.com/",
        "http://github.com/",
        "https://www.github.com/",
        "http://www.github.com/",
        "www.github.com/",
        "github.com/",
        "git@github.com:",
    ):
        if value.startswith(prefix):
            value = value[len(prefix) :]
            break
    value = value.split("?", 1)[0].split("#", 1)[0]
    if value.endswith(".git"):
        value = value[:-4]
    value = value.strip("/")
    if not REPO_SLUG_RE.match(value):
        raise ValueError(
            f"'{raw}' no parece un repositorio válido (usa 'owner/repo' o la URL)."
        )
    return value


def build_jwt(app_id: str, private_key: str) -> str:
    """Construye el JWT de la App (RS256)."""
    now = int(time.time())
    try:
        return jwt.encode(
            {"iss": app_id, "iat": now - 60, "exp": now + JWT_LIFETIME},
            private_key,
            algorithm="RS256",
        )
    # PyJWT lanza InvalidKeyError con claves malformadas, pero AttributeError con
    # una clave pública y TypeError con una clave cifrada.
    except (jwt.PyJWTError, AttributeError, TypeError) as exc:
        raise ValueError(f"No se pudo firmar el JWT: {exc}") from exc


def request(
    method: str,
    url: str,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Realiza una petición JSON a la API de GitHub."""
    data = json.dumps(payload).encode() if payload is not None else None
    http_request = urllib.request.Request(url, data=data, method=method)
    http_request.add_header("Accept", "application/vnd.github+json")
    http_request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token is not None:
        http_request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(http_request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            detail = json.load(exc).get("message", "")
        except (json.JSONDecodeError, UnicodeDecodeError):
            detail = ""
        raise ValueError(f"GitHub devolvió {exc.code}: {detail or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"No se pudo contactar con GitHub: {exc.reason}") from exc


def generate_token(cfg: dict[str, Any], config_path: Path) -> dict[str, Any]:
    """Pide a GitHub un installation token y devuelve el body completo."""
    api_url = resolve_api_url(cfg)
    key = load_private_key(str(cfg["private-key"]), config_path)
    jwt_token = build_jwt(str(cfg["app-id"]), key)
    return request(
        "POST",
        f"{api_url}/app/installations/{cfg['installation-id']}/access_tokens",
        jwt_token,
    )
