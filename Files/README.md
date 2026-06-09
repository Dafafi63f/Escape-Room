# Files — herramientas del TFG

Scripts y utilidades de **mantenimiento del banco**. No son necesarios para jugar; el juego está en [`../Juego/README.md`](../Juego/README.md) (paquete [`Consola`](../Juego/Consola/README.md)).

Limpieza de artefactos temporales (`__pycache__` y `.txt`): [`../borrar_temporales.py`](../borrar_temporales.py) (raíz, no hace falta entrar aquí).

| Carpeta | Documentación |
|---------|----------------|
| [`Scripts/`](Scripts/README.md) | CLI unificada (`mantenimiento.py`), `utils_*`, auditorías, balanceo |
| [`Archivo/`](Archivo/README.md) | Scripts legado de regeneración del CSV (bloqueados salvo `TFG_PERMITIR_CSV=1`) |

## Criterio de organización

- **`Files/Scripts/`** — todo lo que usa el banco cerrado (solo lectura del CSV o mantenimiento de `plantillas.json`).
- **`Files/Archivo/`** — regeneración/reescritura histórica del CSV y CLIs sustituidos.

## Comandos habituales

```bash
python Files/Scripts/mantenimiento.py validar
python Files/Scripts/mantenimiento.py plantillas pipeline
python Files/Scripts/cli_examen_historia.py --perfil refuerzo --materias 6
# guardar salida: ... > plan_examen.txt
```

Flujo de mantenimiento completo, catálogo de scripts y objetivos de balanceo: [`Scripts/README.md`](Scripts/README.md).
