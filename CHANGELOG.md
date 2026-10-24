# Changelog

Todos los cambios relevantes de `acodo` (antes `acodo-framework`) se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el
proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [0.3.0] - 2026-10-24

### Changed

- El paquete se publica en PyPI como `acodo` en lugar de `acodo-framework`, para que el
  nombre de distribución coincida con el módulo importable. La API y el import
  (`import acodo`) no cambian; solo hay que actualizar la dependencia
  (`uv remove acodo-framework && uv add acodo`). PyPI no permite renombrar proyectos,
  así que `acodo-framework` queda obsoleto.
- Los tags de publicación pasan de `acodo-framework-vX.Y.Z` a `vX.Y.Z`, ya que el
  repositorio solo contiene un paquete.
- El repositorio deja de ser un workspace de uv y pasa a contener solo este paquete, en la
  raíz (`src/`, `tests/`, `pyproject.toml`). La CLI no aportaba lo suficiente y la plantilla
  ya vive en su propio repositorio, así que mantener un monorepo solo añadía complejidad.
  La API pública no cambia.
- README: incluye los comandos de desarrollo, que antes estaban en el README del workspace.
- Metadatos: añadidos los enlaces al repositorio, la documentación y el changelog.

## [0.2.1] - 2026-10-19

### Changed

- README: añadida la sección «Enlaces» (repositorio, documentación y PyPI) y la instalación desde PyPI, ya que el paquete está publicado.
- README: el enlace a la licencia es absoluto para que funcione en la página de PyPI.

## [0.2.0] - 2026-10-18

### Changed

- `Logger` se construye directamente con `Logger(name, *, file=None, debug=False)` y sigue siendo
  idempotente por nombre. Se simplifica la API: ya no hace falta una función auxiliar.
- La consola antepone la etiqueta del nivel (`[INFO]`, `[ERROR]`...), con color solo si la salida es
  un terminal y no está definida `NO_COLOR`. El fichero de log nunca recibe códigos ANSI.

### Removed

- `get_logger`, sustituida por el constructor de `Logger`.

## [0.1.0] - 2026-10-17

### Added

- Versión inicial: migración de `acodo-utils` 4.1.1 al workspace de Acodo.
- Paquete `acodo.utils` con los módulos `checkers`, `converters`, `getters`, `parsers`, `types` y
  `validators`.
- Paquete `acodo.logger` con `Logger` y `get_logger`, separados de `utils` para que este quede libre
  de efectos de entrada/salida.

### Changed

- El paquete importable pasa de `acodo_utils` a `acodo`; `Logger` y `get_logger` ya no se exportan
  desde `acodo.utils`, ahora están en `acodo.logger`.
- El motor de compilación pasa a `uv_build` con `module-name = "acodo"` y la configuración de Ruff,
  ty y pytest se centraliza en la raíz del workspace.
- Los tests del logger se separan de `test_getters.py` a `test_logger.py`.
