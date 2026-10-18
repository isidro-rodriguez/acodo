"""Logger de Acodo: salida configurable a consola y fichero con rotación diaria.

Uso:

```python
from acodo.logger import get_logger

log = get_logger("miapp")
log.info("Procesando %(n)s ficheros", n=3)
```
"""

from .logger import Logger as Logger
from .logger import get_logger as get_logger
