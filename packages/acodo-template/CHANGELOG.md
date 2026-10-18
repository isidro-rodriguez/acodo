# Changelog

Todos los cambios relevantes de `acodo-template` se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el
proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.1.0] - 2026-10-17

### Added

- Versión inicial dentro del workspace de Acodo, adaptada desde la plantilla independiente.

### Changed

- Depende de `acodo-framework` y usa `acodo-cli` en desarrollo, ambos como miembros del workspace.
- La versión se declara solo en `pyproject.toml` y se lee con `importlib.metadata`.
- Los colores del logo se asignan sin solapes de rango y los tests usan nombres en inglés.

### Fixed

- El `py.typed` estaba fuera del paquete y no se distribuía; ahora está en `src/acodo_template/`.
