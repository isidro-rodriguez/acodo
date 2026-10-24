---
icon: lucide/leaf
---

# Acodo

**Acodo** es una biblioteca Python de utilidades puras —validación, conversión, parseo
y logger— sin dependencias externas: solo usa la biblioteca estándar. Se instala y se importa
como `acodo` (antes se publicaba como `acodo-framework`).

## Instalación

Requiere Python 3.13 o superior.

```bash
uv add acodo
```

## Enlaces

- Repositorio: <https://github.com/isidro-rodriguez/acodo>
- Plantilla de proyecto: <https://github.com/isidro-rodriguez/acodo-template>
- PyPI: [`acodo`](https://pypi.org/project/acodo/)

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

## Referencia de la API

La [referencia de la API](api/acodo/index.md) se genera al construir a partir de los
docstrings, así que siempre refleja el código actual:

- [`acodo.utils`](api/acodo/utils/index.md): validación, conversión, parseo y obtención de valores.
- [`acodo.logger`](api/acodo/logger/index.md): logger con salida a consola y/o fichero.

## Desarrollo

```bash
git clone https://github.com/isidro-rodriguez/acodo.git
cd acodo
uv sync

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
