---
icon: lucide/leaf
---

# Acodo

**Acodo** es un framework Python para construir aplicaciones sin dependencias
innecesarias. Cada paquete resuelve un problema concreto y se apoya en la biblioteca
estándar siempre que es posible.

## Paquetes

| Paquete | Módulo | Qué ofrece |
|---------|--------|------------|
| `acodo-framework` | `acodo` | Utilidades puras: validación, conversión, parseo y logger. Sin dependencias externas. |
| `acodo-cli` | `acodo_cli` | CLI de desarrollo construida con Typer (`uv run acodo`). |
| `acodo-template` | `acodo_template` | Plantilla de proyecto que reúne las herramientas del framework. |

## Instalación

El proyecto usa [uv](https://docs.astral.sh/uv/) y requiere Python 3.13 o superior.

```bash
uv add acodo-framework        # biblioteca (PyPI)
uv add --dev acodo-cli        # CLI de desarrollo (PyPI)
```

Para trabajar en el monorepo:

```bash
git clone https://github.com/isidro-rodriguez/acodo.git
cd acodo
uv sync --all-packages
```

Dentro del workspace, los miembros se enlazan entre sí con `[tool.uv.sources]` y
`workspace = true`.

## Enlaces

- Repositorio: <https://github.com/isidro-rodriguez/acodo>
- Plantilla de proyecto: <https://github.com/isidro-rodriguez/acodo-template>
- PyPI: [`acodo-framework`](https://pypi.org/project/acodo-framework/) · [`acodo-cli`](https://pypi.org/project/acodo-cli/)

## Uso básico

```python
from acodo.logger import Logger
from acodo.utils import to_bool, valid_email

to_bool("sí")  # True
valid_email("hola")  # False

log = Logger("miapp")
log.info("Procesando %(n)s ficheros", n=3)
```

Las utilidades de `acodo.utils` se agrupan por prefijo:

| Prefijo   | Devuelve      | Categoría |
|-----------|---------------|-----------|
| `get_*`   | `Any`         | Obtienen valores del entorno, credenciales, identificadores... |
| `has_*`   | `bool`        | Comprueban la presencia de claves, campos o estructura. |
| `parse_*` | `str`         | Dan formato legible a importes, fechas, tamaños... |
| `to_*`    | `Any \| None` | Convierten el tipo o devuelven `None` si no pueden. |
| `valid_*` | `bool`        | Validan el formato o el dominio de un valor. |

## Línea de comandos

La CLI se ejecuta desde la raíz del workspace:

```bash
uv run acodo --help
uv run acodo check    # formato, lint, tipos y tests con resumen final
```

## Referencia de la API

La [referencia de la API](api/acodo/index.md) se genera al construir a partir de los
docstrings, así que siempre refleja el código actual:

- [`acodo.utils`](api/acodo/utils/index.md): validación, conversión, parseo y obtención de valores.
- [`acodo.logger`](api/acodo/logger/index.md): logger con salida a consola y/o fichero.

## Desarrollo

Los comandos de calidad se ejecutan desde la raíz del workspace:

```bash
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest
```

Para trabajar en la documentación:

```bash
uv run zensical serve              # previsualización local
uv run zensical build              # build del sitio
```

## Licencia

MIT. El texto completo está en el archivo
[`LICENSE`](https://github.com/isidro-rodriguez/acodo/blob/main/LICENSE).
