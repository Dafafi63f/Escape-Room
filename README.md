# Cuestionario MATCAD

## Estructura

| Carpeta / fichero | Rol |
|------------------|-----|
| [`Juego/`](Juego/README.md) | Lanzador, paquete [`Consola/`](Juego/Consola/README.md), build opcional del `.exe` |
| [`Data/`](Data/README.md) | CSV, plantillas, histórico de qualificacions |
| [`Files/`](Files/README.md) | Mantenimiento del banco (no necesario para jugar) |
| [`borrar_pycache.py`](borrar_pycache.py) | Limpia `__pycache__` (autónomo, sin depender de `Files/`) |

Cada carpeta principal tiene su `README.md` con más detalle.

## Jugar

Requisito: Python 3.10+ (solo biblioteca estándar).

```bash
python Juego/juego_cuestionario.py
```

### Datos

Ver [`Data/README.md`](Data/README.md). Imprescindibles: `Preguntas.csv`, `listado_materias.csv`. Modo historia: `Historic_qualificacions_MatCAD_completo.csv`. Modo con plantillas: `plantillas.json`.

## Ejecutable (opcional, local)

Requisitos: **Windows**, Python 3.10+ con `pip`, carpeta [`Data/`](Data/README.md) en la raíz (el script la empaqueta dentro del `.exe`).

```powershell
cd Juego
.\build_exe_onefile.ps1
```

Salida: `Juego/juego_cuestionario.exe`. No se versiona (`*.exe` en `.gitignore`). Al terminar, el script elimina `Juego/build/` y `juego_cuestionario.spec`.

Detalle: [`Juego/README.md`](Juego/README.md#ejecutable-opcional).

## Pruebas

```bash
python -m unittest discover -s Juego/Tests -v
```

Ver [`Juego/Tests/README.md`](Juego/Tests/README.md).

## Limpieza

```bash
python borrar_pycache.py
python borrar_pycache.py --dry-run
```

Omite `build/`, `.venv/` y similares.
