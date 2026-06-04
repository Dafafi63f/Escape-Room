# Scripts — mantenimiento del banco

Herramientas de desarrollo del TFG. **No hacen falta para jugar**; el jugador solo necesita `Juego/juego_cuestionario.py` y `Data/`.

## Entrada principal

```bash
python Files/Scripts/mantenimiento.py validar
python Files/Scripts/mantenimiento.py revision
python Files/Scripts/mantenimiento.py dataset
python Files/Scripts/mantenimiento.py plantillas pipeline
python Files/Scripts/mantenimiento.py duplicados --help
```

Ver la cabecera de [`mantenimiento.py`](mantenimiento.py) para la lista completa de subcomandos.

## Otros CLIs útiles

| Script | Uso |
|--------|-----|
| `cli_examen_historia.py` | Previsualizar plan de examen en consola (importa `Consola.generador_examen_historia`) |
| `clasificar_pregunta.py` | Clasificar una pregunta concreta |
| `auditoria.py` | Auditorías del dataset |
| `duplicados.py` | Detección y gestión de duplicados |

## Utilidades (`utils_*`)

Módulos compartidos por los scripts: lectura/escritura CSV, plantillas, orden de temas, banco cerrado, etc. No están pensados como API pública del juego; la lógica de partida vive en `Juego/Consola/`.

## Limpieza de `__pycache__`

Preferible desde la raíz del proyecto (no depende de esta carpeta):

```bash
python borrar_pycache.py
```
