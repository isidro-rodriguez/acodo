# acodo-framework

Biblioteca de utilidades de Acodo Framework para **Python >= 3.13**. No tiene
dependencias externas: solo usa la biblioteca estándar. El paquete que se importa
es `acodo`.

## 🚀 Instalación

Desde [PyPI](https://pypi.org/project/acodo-framework/):

```bash
uv add acodo-framework
```

Para trabajar en el monorepo, desde la raíz: `uv sync --all-packages`. Entre miembros se
enlaza con `acodo-framework = { workspace = true }` en `[tool.uv.sources]`.

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

## Enlaces

- Repositorio: <https://github.com/isidro-rodriguez/acodo>
- Documentación: <https://isidro-rodriguez.github.io/acodo/>
- PyPI: <https://pypi.org/project/acodo-framework/>
- Plantilla de proyecto: <https://github.com/isidro-rodriguez/acodo-template>

## Licencia

[MIT](https://github.com/isidro-rodriguez/acodo/blob/main/LICENSE).
