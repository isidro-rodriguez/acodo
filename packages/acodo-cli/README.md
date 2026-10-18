# acodo-cli

CLI de desarrollo para proyectos **Python >= 3.13**, parte de Acodo Framework.
Se ejecuta desde el directorio de un proyecto (en el workspace, la raíz) y lee su
configuración del `pyproject.toml`. Construido con [Typer](https://typer.tiangolo.com) y
[Rich](https://rich.readthedocs.io).

## 🚀 Instalación

Dentro del workspace, como dependencia de desarrollo de otro miembro:

```toml
[dependency-groups]
dev = ["acodo-cli"]

[tool.uv.sources]
acodo-cli = { workspace = true }
```

Para trabajar en el monorepo, desde la raíz: `uv sync --all-packages`.

No se admite como herramienta global (`uv tool install`, `pipx` o Python del sistema): usa `ruff`,
`ty` y `pytest` del entorno del proyecto, así que aborta con un error si detecta esa instalación.

## 🛠️ Comandos

```bash
uv run acodo                      # Sin subcomando: banner de Acodo y ayuda
uv run acodo --version            # Panel con el logo, la versión y el entorno
uv run acodo --help               # Lista los comandos (también: python -m acodo_cli)
uv run acodo init                 # Añade [tool.acodo-cli], .local/gh_app.json y .local/ al .gitignore
uv run acodo doctor               # Diagnóstico del entorno y la configuración
uv run acodo check                # Calidad: ruff format, ruff check --fix, ty y pytest
uv run acodo clean                # Borra cachés y artefactos (--dry-run para ver qué)
uv run acodo todo                 # Lista TODO/FIXME/XXX/HACK (falla si alguno no tiene texto)
uv run acodo api                  # Documentación de la API en el navegador (pdoc)
uv run acodo backup               # Copia de seguridad en .local/backup.zip (-a tar.gz)
uv run acodo code-count           # Líneas de código y docstrings (-v, -t, --json)
uv run --group build acodo build  # Compila con PyInstaller (--onefile, --no-icon)
uv run acodo gh-token             # Token de instalación de una GitHub App
uv run acodo gh-check             # Comprueba el acceso al repositorio configurado
```

Consideraciones:

- `check` no se detiene en el primer fallo, muestra un resumen final.
- `build` necesita PyInstaller en el entorno del proyecto (p. ej. un grupo `build`).
- `check --cov` necesita `pytest-cov`.

### 🔑 GitHub App

`gh-token` y `gh-check` leen un JSON, por defecto `.local/gh_app.json`
(se cambia con `-f`):

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

Todo es opcional. En el `pyproject.toml` del proyecto, con los valores por defecto:

```toml
[tool.acodo-cli]
src-dir = "src"             # Código fuente (api, backup, build, code-count)
test-dir = "tests"          # Tests (backup, code-count)
python-version = ">=3.13"   # Versión de Python esperada
```

En el workspace de Acodo se usa `src-dir = "packages"` y `test-dir = "packages"`; con
ambos iguales, `code-count` cuenta los ficheros una sola vez (categoría `src`).

## 📁 Estructura

```bash
src/acodo_cli/
├── cli.py                # App Typer principal; registra los comandos
├── config.py             # load_config(): lee [tool.acodo-cli] de pyproject.toml
├── models.py             # Dataclasses y enums compartidos
├── theme.py              # Paleta Acodo, Theme de Rich y estilos de la ayuda de Typer
├── banner.py             # ASCII art con degradado y panel de --version
├── typer_options.py      # Opciones de Typer reutilizables
├── commands_service.py   # Lógica común (consolas, errores, procesos, GitHub App)
└── commands/             # un módulo por comando (api, backup, build, check, clean...)
```

## Licencia

[MIT](LICENSE).
