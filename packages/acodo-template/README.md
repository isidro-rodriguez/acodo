# acodo-template

Plantilla minimalista para proyectos **Python >= 3.13**, parte de Acodo Framework.
Está pensada para las herramientas de [Astral](https://astral.sh) (`uv`, `ruff` y `ty`).

Depende de `acodo-framework` y usa `acodo-cli` como herramienta de desarrollo.

## 🚀 Instalación

Desde la raíz del workspace:

```bash
uv sync --all-packages
```

## 🛠️ Uso

```bash
uv run main                   # Imprime el logo (también: python -m acodo_template)
uv run --package acodo-template pytest packages/acodo-template
```

La configuración de Ruff, ty y pytest está en el `pyproject.toml` de la raíz del
workspace; si copias esta plantilla fuera del monorepo, llévate también esas secciones.

## 📁 Estructura

```bash
src/acodo_template/
├── resources/      # Recursos del paquete (iconos)
├── __init__.py     # Expone __version__ (leída de los metadatos)
├── __main__.py     # Permite ejecutar con `python -m acodo_template`
├── main.py         # Lógica del punto de entrada
└── py.typed        # Marca el paquete como tipado
tests/
└── test_main.py    # Ejemplo de pruebas con pytest
```

## Licencia

[MIT](LICENSE).
