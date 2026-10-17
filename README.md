# acodo

Framework Python para construir aplicaciones sin dependencias innecesarias. Cada paquete
resuelve un problema concreto y se apoya en la biblioteca estándar siempre que sea posible.

## Paquetes

- **`acodo-framework`** (`acodo`): utilidades puras — validación, parseo, formateo, logging
  y base de datos JSON con hash. Sin dependencias externas.
- **`acodo-cli`**: aplicación de consola construida con Typer.
- **`acodo-template`**: plantilla de proyecto que reúne las herramientas del framework.

## Instalación

El proyecto usa [uv](https://docs.astral.sh/uv/) y requiere Python 3.13 o superior.

```bash
# Entorno de desarrollo completo del monorepo
uv sync --all-packages

# Solo el framework (zero-dependency)
uv add acodo-framework

# Framework + CLI
uv add acodo-cli
```

## Uso básico

```python
from acodo.utils import valid_email, valid_url
from acodo.logger import Logger

log = Logger.init()

if valid_email("user@example.com"):
    log.info("Email válido")
```

La CLI se instala con `acodo-cli`:

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
```

Los hooks de `pre-commit` cubren formato, lint, tipos y tests; la etapa `pre-push` añade
cobertura y la construcción de la documentación.

## Documentación

La documentación se construye con [Zensical](https://zensical.org):

```bash
uv run zensical serve   # previsualización local
uv run zensical build   # build del sitio
```

## Licencia

MIT. Consulta el archivo [`LICENSE`](LICENSE) para el texto completo.
