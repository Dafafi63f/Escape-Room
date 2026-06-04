# Data — banco de preguntas y datasets

Ficheros que usa el juego y las herramientas de mantenimiento.

| Fichero | Uso |
|---------|-----|
| `Preguntas.csv` | Banco principal (480 preguntas cerradas en producción) |
| `listado_materias.csv` | Metadatos de materias (curso, nombre, etc.) |
| `plantillas.json` | Plantillas / pool extra (modos beta del juego) |
| `criterios_clasificacion_materia.csv` | Criterios de clasificación por materia (mantenimiento) |
| `Historic_qualificacions_MatCAD_completo.csv` | Histórico de qualificacions — **modo historia** |
| `Històric_qualificacions_MatCAD.xlsx` | Fuente original del histórico; el juego usa el **CSV** |
| `revision_manual.md` | Notas de revisión manual del banco |

El juego resuelve rutas con [`Juego/Consola/rutas.py`](../Juego/Consola/rutas.py): busca una carpeta `Data/` en la raíz del proyecto, en el directorio de trabajo o junto al `.exe` (PyInstaller extrae `Data/` dentro del bundle).

## Validar el banco

```bash
python Files/Scripts/mantenimiento.py validar
```

## Empaquetado en el `.exe`

Al ejecutar `Juego/build_exe_onefile.ps1`, se incluye esta carpeta (salvo que copies datos solo en `Juego/Data/`). Conviene tener aquí al menos los CSV/JSON que uses en todos los modos.
