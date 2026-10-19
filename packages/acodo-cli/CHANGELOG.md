# Changelog

Todos los cambios relevantes de `acodo-cli` se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el
proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [0.2.2] - 2026-10-19

### Changed

- README: añadida la sección «Enlaces» (repositorio, documentación y PyPI) y la instalación desde
  PyPI, ya que el paquete está publicado.
- README: el enlace a la licencia es absoluto para que funcione en la página de PyPI.

## [0.2.0] - 2026-10-18

### Added

- Configuración en `acodo.toml`: `[all]` más una sección por comando (`format`, `lint`, `types`,
  `test`, `todo`, `backup`, `api`) con `include`/`exclude`, y `[github_app]`. Así todos los
  comandos comparten las mismas rutas y se pueden ajustar sin tocar el código.
- `acodo init` copia el `acodo.toml` por defecto; sin subcomando, `acodo` ofrece inicializar si
  el directorio no tiene `acodo.toml`.
- Comandos `format`, `lint`, `types`, `tests` y `tests-cov`, que dividen el antiguo `check`; este
  sigue ejecutándolos todos.
- `api` genera la documentación en Markdown con un script interno (`ast`).
- `init` fuera de un proyecto (instalación global) ofrece clonar la plantilla
  `isidro-rodriguez/acodo-template` en la ruta indicada, por defecto `./acodo/`.

### Changed

- Los comandos ya no reciben argumentos: leen `acodo.toml` y, como mucho, preguntan (`clean`
  confirma antes de borrar y `code-count` pregunta si detallar por fichero). `cli.py` solo llama a
  los scripts de `commands/`.
- `backup` y `api` toman el destino y el formato del `target` de su sección, con la versión del
  proyecto en el nombre si `version_suffix` es `true`.
- El nombre, la versión y `requires-python` se leen del `[project]` de `pyproject.toml`, en vez de
  duplicarlos en la configuración.
- `gh-token` imprime siempre el JSON completo y lo copia al portapapeles.
- `code-count` crea una categoría por cada ruta de `[all].include`.
- `doctor` valida las rutas de `[all]` y `requires-python`.
- La instalación global ya no aborta: solo expone `init`, que ofrece clonar la plantilla.

### Removed

- La sección `[tool.acodo-cli]` del `pyproject.toml`: `src-dir`, `test-dir` y `python-version`
  se sustituyen por `acodo.toml`.
- El comando `build` (PyInstaller) y la comprobación de PyInstaller en `doctor`.
- La generación de la API con `pdoc`, que obligaba a depender de `uv run --with pdoc`.
- Las opciones `--ci`, `--cov`, `--dry-run`, `--output`, `--path`, `--file`, `--archiver`,
  `--only-token`, `--no-clipboard`, `--no-print`, `--verbose`, `--tree` y `--json`.

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
