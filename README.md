# Cuestionario MATCAD

## Estructura

| Carpeta / fichero | Rol |
|------------------|-----|
| [`Juego/`](Juego/README.md) | Lanzador, paquete [`Consola/`](Juego/Consola/README.md), build opcional del `.exe` |
| [`Data/`](Data/README.md) | CSV, plantillas, histórico de qualificacions |
| [`Files/`](Files/README.md) | Mantenimiento del banco (no necesario para jugar) |
| [`borrar_temporales.py`](borrar_temporales.py) | Limpia `__pycache__` y `.txt` temporales en todo el proyecto |

Cada carpeta principal tiene su `README.md` con más detalle.

## Jugar

Requisito: Python 3.10+ (solo biblioteca estándar).

```bash
python Juego/juego_cuestionario.py
```

Modos en el menú: **libre**, **historia** (examen balanceado) y **feedback** (avisos al creador). Controles en terminal: **H** (ayuda), **F** (feedback rápido sin borrar pantalla), **Esc** (pausa), **Supr** (atrás en menús). Detalle en [`Juego/Consola/README.md`](Juego/Consola/README.md).

### Datos

Ver [`Data/README.md`](Data/README.md). Imprescindibles: `Preguntas.csv`, `listado_materias.csv`. Modo historia: `Historic_qualificacions_MatCAD_completo.csv`. Modo con plantillas: `plantillas.json`.

Configuración privada del creador (SMTP, GitHub, etc.): `Data/creador_privado.json` (local; plantilla en [`Juego/Consola/config_creador.py`](Juego/Consola/config_creador.py)).

## Ejecutable (opcional, local)

Requisitos: **Windows**, Python 3.10+ con `pip`, carpeta [`Data/`](Data/README.md) en la raíz (el script la empaqueta dentro del `.exe`).

```powershell
cd Juego
.\build_exe_onefile.ps1
```

Salida: `Juego/juego_cuestionario.exe` (ignorado en git). Al terminar, el script elimina `Juego/build/` y `juego_cuestionario.spec`.

Detalle: [`Juego/README.md`](Juego/README.md#ejecutable-opcional).

## Pruebas

```bash
python -m unittest discover -s Juego/Tests -v
```

Ver [`Juego/Tests/README.md`](Juego/Tests/README.md).

## Limpieza

```bash
python borrar_temporales.py
python borrar_temporales.py --dry-run
python borrar_temporales.py --solo-pycache
python borrar_temporales.py --solo-txt
```

Recorre todo el proyecto y omite `build/`, `.venv/` y similares. Los `.txt` de `Juego/Informes/` y `Juego/Feedback/` entran en la limpieza.
