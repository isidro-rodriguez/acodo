# acodo

Framework Python para construir aplicaciones sin dependencias innecesarias. Cada paquete
resuelve un problema concreto y se apoya en la biblioteca estándar siempre que sea posible.

## Paquetes

- **`acodo-framework`** (`acodo`): utilidades puras — validación, conversión, parseo y
  logger (`acodo.utils` y `acodo.logger`). Sin dependencias externas.
- **`acodo-cli`**: CLI de desarrollo construida con Typer (`uv run acodo`).
- **`acodo-template`**: plantilla de proyecto que reúne las herramientas del framework.

## Instalación

El proyecto usa [uv](https://docs.astral.sh/uv/) y requiere Python 3.13 o superior.

```bash
# Entorno de desarrollo completo del monorepo
uv sync --all-packages

# Ejecutar un comando contra un miembro concreto
uv run --package acodo-cli acodo --version
```

Los paquetes aún no están publicados en PyPI: entre miembros se enlazan con
`[tool.uv.sources]` y `workspace = true`.

## Uso básico

```python
from acodo.logger import Logger
from acodo.utils import valid_email

log = Logger("miapp")

if valid_email("user@example.com"):
    log.info("Email válido")
```

La CLI se ejecuta desde la raíz del workspace:

```bash
uv run acodo --help
```

## Calidad

Los comandos se ejecutan desde la raíz del workspace:

```bash
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest

# Equivalente, con resumen final
uv run acodo check
```

Los hooks de `pre-commit` cubren formato, lint, tipos y tests; la etapa `pre-push` añade
cobertura, la regeneración de la API y la construcción de la documentación.

## Documentación

La documentación vive en `docs/` y se construye con [Zensical](https://zensical.org).
La referencia de la API se genera al construir, a partir de los docstrings:

```bash
uv run zensical serve              # previsualización local
uv run zensical build              # build del sitio
```

## Licencia

MIT. Consulta el archivo [`LICENSE`](LICENSE) para el texto completo.
