# acodo-cli

CLI de desarrollo para proyectos **Python >= 3.13**, parte de Acodo Framework.
Se ejecuta desde el directorio de un proyecto (en el workspace, la raíz) y lee su
configuración de `acodo.toml`. Construido con [Typer](https://typer.tiangolo.com) y
[Rich](https://rich.readthedocs.io).

## 🚀 Instalación

Desde [PyPI](https://pypi.org/project/acodo-cli/), como dependencia de desarrollo:

```bash
uv add --dev acodo-cli
```

Para trabajar en el monorepo, desde la raíz: `uv sync --all-packages`. Entre miembros se
enlaza con `acodo-cli = { workspace = true }` en `[tool.uv.sources]`.

Instalado como herramienta global (`uv tool install`, `pipx` o Python del sistema) solo
expone `init`: el resto de comandos usan `ruff`, `ty` y `pytest` del entorno del proyecto.

## 🛠️ Comandos

Los comandos no reciben argumentos: leen todo de `acodo.toml` y, como mucho, hacen
alguna pregunta interactiva.

```bash
uv run acodo                # Sin subcomando: ayuda (u ofrece inicializar si falta acodo.toml)
uv run acodo --version      # Panel con el logo, la versión y el entorno
uv run acodo --help         # Lista los comandos (también: python -m acodo_cli)
uv run acodo init           # En un proyecto: acodo.toml por defecto, .local/gh_app.json y .local/ al .gitignore
                            # Fuera de un proyecto (global): ofrece clonar la plantilla (por defecto ./acodo/)
uv run acodo doctor         # Diagnóstico del entorno y la configuración
uv run acodo format         # ruff format
uv run acodo lint           # ruff check --fix
uv run acodo types          # ty check
uv run acodo tests          # pytest
uv run acodo tests-cov      # pytest con cobertura (requiere pytest-cov)
uv run acodo check          # format, lint, types y tests
uv run acodo clean          # Borra cachés y artefactos, previa confirmación
uv run acodo todo           # Lista TODO/FIXME/XXX/HACK (falla si alguno no tiene texto)
uv run acodo api            # Documentación de la API en Markdown (target de [api])
uv run acodo backup         # Copia de seguridad (target de [backup])
uv run acodo code-count     # Líneas de código y docstrings (pregunta si detallar por fichero)
uv run acodo gh-token       # Token de instalación de una GitHub App (también al portapapeles)
uv run acodo gh-check       # Comprueba el acceso al repositorio configurado
```

Consideraciones:

- Las comprobaciones de calidad no se detienen en el primer fallo y muestran un resumen final.
- `tests-cov` necesita `pytest-cov`; la cobertura se configura en `[tool.coverage]`.
- `api` solo genera Markdown (`.md`); documenta lo público que tenga docstring, sin importar el código.

### 🔑 GitHub App

`gh-token` y `gh-check` leen el JSON indicado en `[github_app].config_file`
(por defecto `.local/gh_app.json`):

```json
{
    "repository": "owner/repo",
    "app-id": "123456",
    "private-key": "private-key.pem",
    "installation-id": "12345678",
    "api-url": "https://api.github.com"
}
```

## 🎨 Colores

Toda la salida (tablas, mensajes, ayuda de Typer y banner) usa solo la paleta
del framework Acodo, definida como `ACODO_THEME` en `theme.py`. El markup de Rich
usa los estilos del tema (`ok`, `error`, `warning`, `label`, `muted`, `title`,
`border`...), nunca colores sueltos; un test lo comprueba sobre la salida real.

## ⚙️ Configuración

Todo vive en el `acodo.toml` de la raíz del proyecto (`acodo init` copia el de por defecto;
el CLI lo busca también en los directorios superiores):

```toml
[all]                       # Común a todos los comandos
include = ["scripts/", "src/", "tests/"]
exclude = [".cache/", ".git", ".pytest_cache", ".ruff_cache", ".venv"]

[format]                    # También [lint], [types], [test], [todo], [backup] y [api]:
include = []                # añaden sus rutas a las de [all]
exclude = []

[backup]
target = ".local/backup.zip"   # zip | tar.gz
version_suffix = true          # backup-<versión>.zip

[api]
target = ".local/api.md"       # md
version_suffix = true

[github_app]
config_file = ".local/gh_app.json"
```

- Los `include` son directorios relativos a la raíz; los que no existan se ignoran.
- Un `exclude` sin `/` interior (`.venv`) casa con cualquier componente de la ruta; con `/`
  (`docs/api/`), con su comienzo.
- El nombre, la versión y `requires-python` salen del `[project]` del `pyproject.toml`.
- En el workspace de Acodo basta `include = ["packages/"]`.

## 📁 Estructura

```bash
src/acodo_cli/
├── cli.py                # App Typer: cada comando solo llama a su script
├── config.py             # load_config(): lee acodo.toml (y [project] de pyproject.toml)
├── models.py             # Dataclasses y enums compartidos
├── theme.py              # Paleta Acodo, Theme de Rich y estilos de la ayuda de Typer
├── banner.py             # ASCII art con degradado y panel de --version
├── typer_options.py      # Opción global --version
├── commands_service.py   # Lógica común (consolas, errores, procesos, alcance, GitHub App)
├── resources/acodo.toml  # Configuración por defecto que copia `acodo init`
└── commands/             # un script por comando (api, backup, check, clean...)
```

## Enlaces

- Repositorio: <https://github.com/isidro-rodriguez/acodo>
- Documentación: <https://isidro-rodriguez.github.io/acodo/>
- PyPI: <https://pypi.org/project/acodo-cli/>
- Plantilla de proyecto: <https://github.com/isidro-rodriguez/acodo-template>

## Licencia

[MIT](https://github.com/isidro-rodriguez/acodo/blob/main/LICENSE).
