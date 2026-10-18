"""Logger de Acodo: salida configurable a consola y fichero con rotación diaria.

Uso:

```python
from acodo.logger import Logger

log = Logger("miapp")
log.info("Procesando %(n)s ficheros", n=3)
```
"""

from .logger import Logger as Logger
