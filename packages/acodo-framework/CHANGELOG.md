# Changelog

Todos los cambios relevantes de `acodo-framework` se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el
proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [0.2.0] - 2026-10-18

### Changed

- `Logger` se construye directamente con `Logger(name, *, file=None, debug=False)` y sigue siendo idempotente por nombre. Se simplifica la API: ya no hace falta una función auxiliar.
- La consola antepone la etiqueta del nivel (`[INFO]`, `[ERROR]`...), con color solo si la salida es un terminal y no está definida `NO_COLOR`. El fichero de log nunca recibe códigos ANSI.

### Removed

- `get_logger`, sustituida por el constructor de `Logger`.

## [0.1.0] - 2026-10-17

### Added

- Versión inicial: migración de `acodo-utils` 4.1.1 al workspace de Acodo.
- Paquete `acodo.utils` con los módulos `checkers`, `converters`, `getters`, `parsers`, `types` y `validators`.
- Paquete `acodo.logger` con `Logger` y `get_logger`, separados de `utils` para que este quede libre de efectos de entrada/salida.

### Changed

- El paquete importable pasa de `acodo_utils` a `acodo`; `Logger` y `get_logger` ya no se exportan desde `acodo.utils`, ahora están en `acodo.logger`.
- El motor de compilación pasa a `uv_build` con `module-name = "acodo"` y la configuración de Ruff, ty y pytest se centraliza en la raíz del workspace.
- Los tests del logger se separan de `test_getters.py` a `test_logger.py`.
