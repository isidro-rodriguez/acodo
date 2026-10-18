# Changelog

Todos los cambios relevantes de `acodo-cli` se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el
proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [0.1.0] - 2026-10-17

### Added

- Versión inicial dentro del workspace de Acodo, adaptada desde el paquete independiente `acodo-cli`
  0.3.0.
- Tests de `theme.py` (solo paleta de Acodo en el markup y en la ayuda de Typer) y de `banner.py`
  (degradado y panel de `--version`).

### Changed

- Las utilidades se importan de `acodo-framework` (`acodo.utils`) como dependencia del workspace en
  vez de `acodo-utils` desde Git.
- La versión se declara solo en `pyproject.toml` y se lee con `importlib.metadata`, en vez de
  duplicarla en `__init__.py`.
- El motor de compilación pasa de `hatchling` a `uv_build`.

### Removed

- `BumpPart` y `BumpPartArgument`, que quedaron sin uso al retirarse el comando `bump`.
