# Cuestionario MATCAD — TFG

**Título provisional:** Diseño y desarrollo de un videojuego educativo basado en contenidos del grado en Matemática Computacional y Análisis de Datos.

**Alumno:** Daniel Fageda Figueredo · **NIU:** 1601846 · **Tutor:** Víctor Navas Portella

Sistema de cuestionarios académicos con banco de **480 preguntas**, juego en consola (modos libre, historia y feedback) y herramientas de mantenimiento del dataset. La capa gráfica escape room / novela queda como evolución futura.

- **Memoria académica (borrador):** [`Memoria_TFG.md`](Memoria_TFG.md)
- **Repositorio:** https://github.com/Dafafi63f/Escape-Room.git

```bash
git clone https://github.com/Dafafi63f/Escape-Room.git
```

No incluyas tokens, contraseñas ni claves privadas en archivos versionados.

## Documentación del proyecto

| Tema | Dónde |
|------|-------|
| Esquema del banco, materias, diagramas curriculares | [`Data/README.md`](Data/README.md) |
| Juego, modos, controles, `.exe` | [`Juego/README.md`](Juego/README.md) |
| Lógica interna (bancos, puntuación, filtros) | [`Juego/Consola/README.md`](Juego/Consola/README.md) |
| Scripts de mantenimiento y balanceo | [`Files/README.md`](Files/README.md) → [`Files/Scripts/README.md`](Files/Scripts/README.md) |
| Scripts legado de regeneración CSV | [`Files/Archivo/README.md`](Files/Archivo/README.md) |
| Pruebas unitarias | [`Juego/Tests/README.md`](Juego/Tests/README.md) |
| Trazabilidad revisión manual | [`Data/revision_manual.md`](Data/revision_manual.md) |

## Estructura

| Carpeta / fichero | Rol |
|------------------|-----|
| [`Juego/`](Juego/README.md) | Lanzador, paquete [`Consola/`](Juego/Consola/README.md), build opcional del `.exe` |
| [`Data/`](Data/README.md) | CSV, plantillas, histórico de qualificacions |
| [`Files/`](Files/README.md) | Mantenimiento del banco (no necesario para jugar) |
| [`borrar_temporales.py`](borrar_temporales.py) | Limpia `__pycache__` y `.txt` temporales en todo el proyecto |

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
