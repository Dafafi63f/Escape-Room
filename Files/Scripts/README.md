# Scripts — mantenimiento del banco

Herramientas de desarrollo del TFG. **No hacen falta para jugar**; el jugador solo necesita `Juego/juego_cuestionario.py` y `Data/`.

## Entrada principal

```bash
python Files/Scripts/mantenimiento.py validar
python Files/Scripts/mantenimiento.py revision
python Files/Scripts/mantenimiento.py dataset
python Files/Scripts/mantenimiento.py plantillas pipeline
python Files/Scripts/mantenimiento.py duplicados --help
python Files/Scripts/mantenimiento.py temporales
python Files/Scripts/mantenimiento.py temporales --dry-run
```

Ver la cabecera de [`mantenimiento.py`](mantenimiento.py) para la lista completa de subcomandos. `pycache` es un alias de `temporales --solo-pycache`.

## Otros CLIs útiles

| Script | Uso |
|--------|-----|
| `cli_examen_historia.py` | Previsualizar plan de examen en consola (importa `Consola.generador_examen_historia`) |
| `clasificar_pregunta.py` | Clasificar una pregunta concreta |
| `auditoria.py` | Auditorías del dataset |
| `duplicados.py` | Detección y gestión de duplicados |

## Utilidades (`utils_*`)

Módulos compartidos por los scripts: lectura/escritura CSV, plantillas, orden de temas, banco cerrado, etc. No están pensados como API pública del juego; la lógica de partida vive en `Juego/Consola/`.

Al finalizar, `mantenimiento.py` sigue llamando a `utils_dataset_csv.borrar_pycache_en_proyecto()` (solo `__pycache__` bajo `Files/`).

## Limpieza de temporales

Preferible desde la raíz del proyecto (abarca todo el TFG, no solo `Files/`):

```bash
python borrar_temporales.py
python borrar_temporales.py --dry-run
python borrar_temporales.py --solo-pycache
python borrar_temporales.py --solo-txt
python Files/Scripts/mantenimiento.py temporales
```
