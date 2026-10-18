"""Compila un binario mediante PyInstaller.

Uso (PyInstaller debe estar en el entorno del proyecto, p. ej. grupo `build`):
    uv run --group build acodo build
    uv run --group build acodo build --onefile --output dist
    uv run --group build acodo build --no-icon

Genera (``<o>`` es el directorio de salida, ``<p>`` el nombre del paquete):
    Con --onefile: ``<o>/<p>`` (``<o>/<p>.exe`` en Windows).
    Sin --onefile: carpeta ``<o>/<p>/`` con el ejecutable ``<p>`` (``<p>.exe``
    en Windows) y sus dependencias.

El nombre del paquete se toma del directorio ``src/<paquete>``. Incluye el
icono desde ``<paquete>/resources`` y valida que el nombre sea seguro como
nombre de fichero en Windows.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from acodo.utils import valid_filename
from acodo_cli.commands_service import (
    console,
    discover_package_name,
    fail,
    get_config,
)
from acodo_cli.typer_options import BuildOutputOption, NoIconOption, OneFileOption


def _get_icon(resources: Path) -> Path:
    """Devuelve la ruta del icono apropiado para la plataforma actual."""
    filename = "icon.ico" if sys.platform == "win32" else "icon.png"
    return resources / filename


def _get_executable_name(package_name: str) -> str:
    """Devuelve el nombre del ejecutable generado para la plataforma actual."""
    if sys.platform == "win32":
        return f"{package_name}.exe"

    return package_name


def _remove(path: Path) -> None:
    """Elimina un fichero o directorio si existe."""
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def _run_pyinstaller(cmd: list[str]) -> None:
    """Ejecuta PyInstaller y aborta con un mensaje claro si falla."""
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        fail(
            f"PyInstaller terminó con código {exc.returncode}. "
            "¿Ejecutas con `uv run --group build`?"
        )


def main(
    output: BuildOutputOption = None,
    onefile: OneFileOption = False,
    no_icon: NoIconOption = False,
) -> None:
    """Compila el paquete como ejecutable con PyInstaller."""
    cfg = get_config()
    src = cfg.src
    output = output or cfg.root / "build"

    package_name = discover_package_name(src)
    if not valid_filename(package_name):
        fail(f"Nombre de paquete inválido para Windows: {package_name}")

    entry = src / package_name / "main.py"
    if not entry.exists():
        fail(f"No se encontró el punto de entrada: {entry}")

    executable_name = _get_executable_name(package_name)
    pyinstaller_dir = output / "_pyinstaller"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        package_name,
        "--console",
        f"--collect-all={package_name}",
        f"--paths={src}",
        f"--distpath={pyinstaller_dir / 'dist'}",
        f"--workpath={pyinstaller_dir / 'work'}",
        f"--specpath={pyinstaller_dir / 'spec'}",
    ]

    if onefile:
        cmd.append("--onefile")

    if not no_icon:
        icon = _get_icon(src / package_name / "resources")
        if not icon.exists():
            fail(f"No se encontró el icono: {icon}")
        cmd.append(f"--icon={icon}")
        console.print(f"Icono:      {icon}")

    cmd.append(str(entry))

    console.print(f"Plataforma: {sys.platform}")
    console.print(f"Paquete:    {package_name}")
    console.print("Compilando con PyInstaller... (esto puede tardar algunos minutos)")

    _run_pyinstaller(cmd)

    # Con --onefile PyInstaller genera un fichero; sin él, una carpeta con el
    # ejecutable dentro.
    artifact_name = executable_name if onefile else package_name
    produced = pyinstaller_dir / "dist" / artifact_name
    if not produced.exists():
        fail(f"No se encontró {produced}. Revisa la salida de PyInstaller.")

    final_path = output / artifact_name
    output.mkdir(parents=True, exist_ok=True)
    _remove(final_path)
    produced.replace(final_path)

    executable = final_path if onefile else final_path / executable_name
    console.print(f"[ok]✓[/] Listo: {executable}")
