r"""Módulo de funciones utilitarias que pueden reutilizarse en cualquier aplicación.

Requiere **Python >= 3.13** y no introduce dependencias.


Uso rápido
----------

Forma parte de `acodo-framework` y se importa desde `acodo.utils`:

```python
from acodo.utils import get_hash, has_required_attrs, parse_slug, to_bytes, valid_email

get_hash("abc")  # ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
has_required_attrs("texto", ["upper", "lower"])  # True
parse_slug("¡Hola, Mundo! Ñandú")  # hola-mundo-nandu
to_bytes("1,5 GiB")  # 1610612736
valid_email("email_sin_punto@ejemplo-com")  # False
```


Tipos
-----

`SocialLink` (definida en `acodo.utils.types`) enumera los tipos de enlace de
red social que reconoce `valid_social_url`.


Convenio de nombrado
--------------------
Las funciones se agrupan por categoría, cada categoría empieza por un
prefijo y dentro de cada una van en orden alfabético.

| Prefijo   | Returns       | Categoría |
|-----------|---------------|-----------|
| `get_*`   | `Any`         | Obtenedores de valores del entorno, credencial, ID, ... |
| `has_*`   | `bool`        | Comprobación de presencia de claves, campos o estructura. |
| `parse_*` | `str`         | Formateado a texto legible (importes, fechas, tamaños, ...). |
| `to_*`    | `Any \| None` | Conversión de tipo o `None` si no puede. |
| `valid_*` | `bool`        | Validación de formato o de dominio de un valor. |


Errores lanzados
----------------

Solo se lanza `ValueError` ante argumentos ambiguos o inválidos:

- `get_*` (algoritmo, rango, longitud...)
- `parse_*` (`lang`),
- `valid_ip` (`version`)
- `valid_password`.


Enlaces de interés
------------------
- [Documentación de Python](https://docs.python.org/3/)
- [PEP 8: guía de estilo](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
  (estilo de los docstrings)
- Herramientas de Astral: [uv](https://docs.astral.sh/uv/),
  [Ruff](https://docs.astral.sh/ruff/) y [ty](https://docs.astral.sh/ty/)
- [pytest](https://docs.pytest.org/)
"""  # noqa: E501

from .checkers import (
    has_required_attrs as has_required_attrs,
)
from .checkers import (
    has_required_fields as has_required_fields,
)
from .checkers import (
    has_required_keys as has_required_keys,
)
from .converters import (
    to_bool as to_bool,
)
from .converters import (
    to_bytes as to_bytes,
)
from .converters import (
    to_date as to_date,
)
from .converters import (
    to_datetime as to_datetime,
)
from .converters import (
    to_decimal as to_decimal,
)
from .converters import (
    to_dict as to_dict,
)
from .converters import (
    to_float as to_float,
)
from .converters import (
    to_int as to_int,
)
from .converters import (
    to_json as to_json,
)
from .converters import (
    to_list as to_list,
)
from .converters import (
    to_path as to_path,
)
from .converters import (
    to_port as to_port,
)
from .converters import (
    to_str as to_str,
)
from .converters import (
    to_timedelta as to_timedelta,
)
from .getters import (
    get_config_dir as get_config_dir,
)
from .getters import (
    get_env as get_env,
)
from .getters import (
    get_file_hash as get_file_hash,
)
from .getters import (
    get_hash as get_hash,
)
from .getters import (
    get_hmac as get_hmac,
)
from .getters import (
    get_now as get_now,
)
from .getters import (
    get_otp as get_otp,
)
from .getters import (
    get_password_hash as get_password_hash,
)
from .getters import (
    get_random_choice as get_random_choice,
)
from .getters import (
    get_random_int as get_random_int,
)
from .getters import (
    get_random_password as get_random_password,
)
from .getters import (
    get_random_token as get_random_token,
)
from .getters import (
    get_uuid as get_uuid,
)
from .parsers import (
    parse_amount as parse_amount,
)
from .parsers import (
    parse_bool as parse_bool,
)
from .parsers import (
    parse_datetime as parse_datetime,
)
from .parsers import (
    parse_percent as parse_percent,
)
from .parsers import (
    parse_size as parse_size,
)
from .parsers import (
    parse_slug as parse_slug,
)
from .parsers import (
    parse_timedelta as parse_timedelta,
)
from .types import SocialLink as SocialLink
from .validators import (
    valid_bic as valid_bic,
)
from .validators import (
    valid_bool as valid_bool,
)
from .validators import (
    valid_cif as valid_cif,
)
from .validators import (
    valid_date as valid_date,
)
from .validators import (
    valid_datetime as valid_datetime,
)
from .validators import (
    valid_dni as valid_dni,
)
from .validators import (
    valid_domain as valid_domain,
)
from .validators import (
    valid_duration as valid_duration,
)
from .validators import (
    valid_email as valid_email,
)
from .validators import (
    valid_filename as valid_filename,
)
from .validators import (
    valid_hex_color as valid_hex_color,
)
from .validators import (
    valid_iban as valid_iban,
)
from .validators import (
    valid_ip as valid_ip,
)
from .validators import (
    valid_json as valid_json,
)
from .validators import (
    valid_mac as valid_mac,
)
from .validators import (
    valid_nie as valid_nie,
)
from .validators import (
    valid_nif as valid_nif,
)
from .validators import (
    valid_passport as valid_passport,
)
from .validators import (
    valid_password as valid_password,
)
from .validators import (
    valid_phone as valid_phone,
)
from .validators import (
    valid_port as valid_port,
)
from .validators import (
    valid_postal_code as valid_postal_code,
)
from .validators import (
    valid_slug as valid_slug,
)
from .validators import (
    valid_social_url as valid_social_url,
)
from .validators import (
    valid_url as valid_url,
)
from .validators import (
    valid_uuid as valid_uuid,
)

# pdoc documenta cada módulo en su propia página, y la del paquete solo lista los
# módulos. Las funciones y clases se reexportan con alias redundante
# (`from .x import f as f`), que es como los verificadores de tipos reconocen una
# reexportación en un paquete con `py.typed`, sin necesidad de `__all__`.
__all__ = [
    "checkers",
    "converters",
    "getters",
    "parsers",
    "types",
    "validators",
]
