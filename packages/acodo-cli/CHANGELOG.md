# Changelog

Todos los cambios relevantes de `acodo-cli` se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el
proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.1.0] - 2026-10-17

### Added

- Versión inicial dentro del workspace de Acodo, adaptada desde el paquete independiente `acodo-cli` 0.3.0.
- Módulo `theme.py` con la paleta de Acodo como `ACODO_THEME` de Rich y estilos para la ayuda de Typer.
- Módulo `banner.py` con el ASCII art con degradado y el panel de `--version`, que faltaban aunque `cli.py` ya los importaba.

### Changed

- Las utilidades se importan de `acodo-framework` (`acodo.utils`) como dependencia del workspace en vez de `acodo-utils` desde Git.
- La versión se declara solo en `pyproject.toml` y se lee con `importlib.metadata`, en vez de duplicarla en `__init__.py`.
- El motor de compilación pasa de `hatchling` a `uv_build`.

### Removed

- `BumpPart` y `BumpPartArgument`, que quedaron sin uso al retirarse el comando `bump`.
