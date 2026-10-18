"""Obtiene un token de instalación para una GitHub App.

Genera el token (por stdout y portapapeles) a partir del JSON indicado en
`[github_app]` de `acodo.toml`. Para comprobar el acceso al repositorio,
véase `gh-check`.

Uso:
    uv run acodo gh-token

Configuración (JSON):
    {
      "repository": "owner/repo",
      "app-id": "123456",
      "private-key": "private-key.pem",
      "installation-id": "12345678",
      "api-url": "https://api.github.com"
    }

    `private-key` admite ruta relativa al propio JSON, ruta absoluta
    o el contenido PEM embebido.
"""

import json
import shutil
import subprocess
import sys

import typer
from rich.markup import escape

from acodo.utils import get_env
from acodo_cli.commands_service import (
    console,
    err_console,
    generate_token,
    get_config,
    gh_config_path,
    load_gh_config,
    normalize_repo,
)

# =============================================================================
#  Portapapeles (sin dependencias Python)
# =============================================================================


def _copy_windows(text: str) -> None:
    if sys.platform != "win32":  # Estrecha el tipo: ty omite el resto en Linux/macOS.
        raise NotImplementedError("Solo disponible en Windows.")

    import ctypes

    cf_unicode_text = 13
    gmem_moveable = 0x0002

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]

    data = text.encode("utf-16-le") + b"\x00\x00"

    if not user32.OpenClipboard(None):
        raise RuntimeError("OpenClipboard falló.")
    try:
        if not user32.EmptyClipboard():
            raise RuntimeError("EmptyClipboard falló.")
        handle = kernel32.GlobalAlloc(gmem_moveable, len(data))
        if not handle:
            raise RuntimeError("GlobalAlloc falló.")
        locked = kernel32.GlobalLock(handle)
        if not locked:
            kernel32.GlobalFree(handle)
            raise RuntimeError("GlobalLock falló.")
        try:
            ctypes.memmove(locked, data, len(data))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(cf_unicode_text, handle):
            kernel32.GlobalFree(handle)
            raise RuntimeError("SetClipboardData falló.")
    finally:
        user32.CloseClipboard()


def _copy_posix(text: str) -> None:
    if sys.platform == "darwin":
        cmd = ["pbcopy"]
    else:
        if get_env("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
            cmd = ["wl-copy"]
        elif shutil.which("xclip"):
            cmd = ["xclip", "-selection", "clipboard"]
        elif shutil.which("xsel"):
            cmd = ["xsel", "--clipboard", "--input"]
        elif shutil.which("wl-copy"):
            cmd = ["wl-copy"]
        else:
            raise RuntimeError(
                "No se encontró 'wl-copy', 'xclip' ni 'xsel' en el PATH."
            )
    try:
        subprocess.run(cmd, input=text.encode("utf-8"), check=True, timeout=5)
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as exc:
        raise RuntimeError(f"No se pudo copiar al portapapeles: {exc}") from exc


def _copy_to_clipboard(text: str) -> None:
    if sys.platform == "win32":
        _copy_windows(text)
    else:
        _copy_posix(text)


def main() -> None:
    """Genera un token de instalación, lo imprime y lo copia al portapapeles."""
    file = gh_config_path(get_config())
    cfg = load_gh_config(file)

    try:
        repo_slug = normalize_repo(str(cfg["repository"]))
        body = generate_token(cfg, file)
    except ValueError as exc:
        err_console.print(f"[error]Error:[/] {escape(str(exc))}")
        raise typer.Exit(code=1) from None

    # El JSON de salida incluye el repositorio de destino.
    output = json.dumps({"repository": repo_slug, **body}, indent=2, ensure_ascii=False)
    console.print(output, markup=False)

    try:
        _copy_to_clipboard(output)
        err_console.print("[ok]✓[/] Copiado al portapapeles.")
    except RuntimeError as exc:
        err_console.print(f"[warning]Aviso:[/] {exc}")
