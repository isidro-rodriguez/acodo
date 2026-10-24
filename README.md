# acodo

Biblioteca de utilidades de Acodo para **Python >= 3.13**. No tiene
dependencias externas: solo usa la biblioteca estándar.

> Antes se publicaba como `acodo-framework`; ese nombre queda obsoleto.

## 🚀 Instalación

Desde [PyPI](https://pypi.org/project/acodo/):

```bash
uv add acodo
```

## 🛠️ Uso

```python
from acodo.logger import Logger
from acodo.utils import to_bool, valid_email

to_bool("sí")  # True
valid_email("hola")  # False

log = Logger("miapp")
log.info("Procesando %(n)s ficheros", n=3)
```

## 📦 Módulos

- `acodo.utils`: funciones agrupadas por prefijo (`get_*`, `has_*`, `parse_*`,
  `to_*`, `valid_*`) y el tipo `SocialLink`. Convenciones y errores en el docstring
  del paquete.
- `acodo.logger`: `Logger`; consola y/o fichero con rotación diaria.

`acodo.logger` depende de `acodo.utils`, nunca al revés.

## 📁 Estructura

```bash
src/acodo/
├── utils/
│   ├── checkers.py       # has_*
│   ├── converters.py     # to_*
│   ├── getters.py        # get_*
│   ├── parsers.py        # parse_*
│   ├── types.py          # SocialLink
│   └── validators.py     # valid_*
└── logger/
    └── logger.py         # Logger
```

## 🧪 Desarrollo

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest
```

Los hooks de `pre-commit` cubren formato, lint, tipos y tests; la etapa `pre-push` añade
cobertura y la construcción de la documentación, que vive en `docs/` y se genera con
[Zensical](https://zensical.org) (`uv run zensical serve` / `uv run zensical build`).

## Enlaces

- Repositorio: <https://github.com/isidro-rodriguez/acodo>
- Documentación: <https://isidro-rodriguez.github.io/acodo/>
- PyPI: <https://pypi.org/project/acodo/>
- Plantilla de proyecto: <https://github.com/isidro-rodriguez/acodo-template>

## Licencia

[MIT](https://github.com/isidro-rodriguez/acodo/blob/main/LICENSE).
