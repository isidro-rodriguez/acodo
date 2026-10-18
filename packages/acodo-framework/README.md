# acodo-framework

Biblioteca de utilidades de Acodo Framework para **Python >= 3.13**. No tiene
dependencias externas: solo usa la biblioteca estándar. El paquete que se importa
es `acodo`.

## 🚀 Instalación

Dentro del workspace se enlaza con `workspace = true`:

```toml
[project]
dependencies = ["acodo-framework"]

[tool.uv.sources]
acodo-framework = { workspace = true }
```

Para trabajar en el monorepo, desde la raíz: `uv sync --all-packages`.

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

## Licencia

[MIT](LICENSE).
