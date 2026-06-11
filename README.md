# Cuestionario MATCAD — TFG

**Título:** Diseño y desarrollo de un juego interactivo educativo basado en contenidos del grado en Matemática Computacional y Análisis de Datos.

**Alumno:** Daniel Fageda Figueredo · **NIU:** 1601846 · **Tutor:** Víctor Navas Portella

Sistema de cuestionarios académicos con banco de **480 preguntas**, juego en consola (modos libre, historia y feedback) y herramientas de mantenimiento del dataset. La capa gráfica escape room / novela queda como evolución futura.

- **Memoria académica (borrador):** [`Memoria_TFG.md`](Memoria_TFG.md)
- **Memoria para entrega (Word y LaTeX):** [`Entrega/`](Entrega/README.md)
- **Estado del proyecto y feedback del tutor:** [`Revision/ESTADO.md`](Revision/ESTADO.md)
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
| Trazabilidad revisión manual del banco | [`Revision/revision_manual_banco.md`](Revision/revision_manual_banco.md) |
| Estado, feedback tutor, pendientes | [`Revision/ESTADO.md`](Revision/ESTADO.md) |
| Exportación Word de la memoria | [`Entrega/README.md`](Entrega/README.md) |

## Estructura

| Carpeta / fichero | Rol |
|------------------|-----|
| [`Juego/`](Juego/README.md) | Lanzador, paquete [`Consola/`](Juego/Consola/README.md), build opcional del `.exe` |
| [`Data/`](Data/README.md) | CSV, plantillas, histórico de qualificacions |
| [`Files/`](Files/README.md) | Mantenimiento del banco (no necesario para jugar) |
| [`Entrega/`](Entrega/README.md) | `Memoria/` (LaTeX, Word), `Figuras/`, scripts de exportación |
| [`Revision/`](Revision/ESTADO.md) | Estado del proyecto, feedback tutor; PDF anotados locales (gitignored) |
| [`Memoria_TFG.md`](Memoria_TFG.md) | Borrador Markdown de la memoria (raíz) |
| [`borrar_temporales.py`](borrar_temporales.py) | Limpia `__pycache__` y `.txt` temporales en todo el proyecto |

## Memoria — exportar Word

El borrador editable está en [`Memoria_TFG.md`](Memoria_TFG.md). Ficheros de entrega en [`Entrega/Memoria/`](Entrega/README.md); figuras en [`Entrega/Figuras/`](Entrega/Figuras/README.md):

```bash
python Entrega/generar_figuras_memoria.py
python Entrega/exportar_memoria.py
```

Genera los `.docx` en `Entrega/Memoria/` (Pandoc). El PDF de entrega lo exportas desde Word tras editar. Detalle en [`Entrega/README.md`](Entrega/README.md).

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
