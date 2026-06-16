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
| Lógica interna (bancos, puntuación, filtros) | [`Juego/Comun/README.md`](Juego/Comun/README.md) · UI terminal: [`Juego/Consola/README.md`](Juego/Consola/README.md) |
| Scripts de mantenimiento y balanceo | [`Files/README.md`](Files/README.md) → [`Files/Scripts/README.md`](Files/Scripts/README.md) |
| Scripts legado de regeneración CSV | [`Files/Archivo/README.md`](Files/Archivo/README.md) |
| Pruebas unitarias | [`Tests/README.md`](Tests/README.md) |
| Trazabilidad revisión manual del banco | [`Revision/revision_manual_banco.md`](Revision/revision_manual_banco.md) |
| Estado, feedback tutor, pendientes | [`Revision/ESTADO.md`](Revision/ESTADO.md) |
| Exportación Word de la memoria | [`Entrega/README.md`](Entrega/README.md) |

## Estructura

| Carpeta / fichero | Rol |
|------------------|-----|
| [`Juego/`](Juego/README.md) | Lanzadores, [`Comun/`](Juego/Comun/README.md), [`Consola/`](Juego/Consola/README.md), [`Grafico/`](Juego/Grafico/README.md), build opcional del `.exe` |
| [`Data/`](Data/README.md) | CSV, plantillas, histórico de qualificacions |
| [`Files/`](Files/README.md) | Mantenimiento del banco (no necesario para jugar) |
| [`Entrega/`](Entrega/README.md) | `Memoria/` (LaTeX, Word), `Figuras/`, scripts de exportación |
| [`Revision/`](Revision/ESTADO.md) | Estado del proyecto, feedback tutor; PDF anotados locales (gitignored) |
| [`Memoria_TFG.md`](Memoria_TFG.md) | Borrador Markdown de la memoria (raíz) |
| [`Tests/`](Tests/README.md) | Pruebas unitarias (74 tests) y CI |
| [`borrar_temporales.py`](borrar_temporales.py) | Limpia `__pycache__` y `.txt` de `Juego/Informes/` y `Juego/Feedback/` |
| [`requirements.txt`](requirements.txt) | Dependencias (pandas, matplotlib, pyinstaller, pygame-ce, mypy, pre-commit) |

## Memoria — exportar Word

El borrador editable está en [`Memoria_TFG.md`](Memoria_TFG.md). Ficheros de entrega en [`Entrega/Memoria/`](Entrega/README.md); figuras en [`Entrega/Figuras/`](Entrega/Figuras/README.md):

```bash
python Entrega/generar_figuras_memoria.py
python Entrega/exportar_memoria.py
```

Genera los `.docx` en `Entrega/Memoria/` (Pandoc). El PDF de entrega lo exportas desde Word tras editar. Detalle en [`Entrega/README.md`](Entrega/README.md).

## Jugar

Dos versiones en paralelo (ver [`Juego/README.md`](Juego/README.md)):

```bash
# Terminal — completa, solo stdlib
python Juego/juego_consola.py

# Gráfico — pygame (en desarrollo)
pip install -r requirements.txt
python Juego/juego_grafico.py
```

La consola sigue siendo la referencia funcional hasta que el gráfico alcance paridad; entonces se retirará la UI terminal.

### Datos

Ver [`Data/README.md`](Data/README.md). Imprescindibles: `Preguntas.csv`, `listado_materias.csv`. Modo historia: `Historic_qualificacions_MatCAD_completo.csv`. Modo con plantillas: `plantillas.json`.

Configuración privada del creador (SMTP, GitHub, etc.): `Data/creador_privado.json` (local; plantilla en [`Juego/Consola/config_creador.py`](Juego/Consola/config_creador.py)).

## Ejecutable (opcional, local)

Requisitos: **Windows**, Python 3.10+ con `pip`, carpeta [`Data/`](Data/README.md) en la raíz (el script la empaqueta dentro del `.exe`).

```powershell
cd Juego
.\build_exe_onefile.ps1
```

Salida: `Juego/juego_consola.exe` (ignorado en git). Al terminar, el script elimina `Juego/build/` y `juego_consola.spec`.

Detalle: [`Juego/README.md`](Juego/README.md#ejecutable-opcional).

## Pruebas

```bash
python -m unittest discover -s Tests -v
```

Solo juego o solo scripts:

```bash
python -m unittest discover -s Tests/Juego -v
python -m unittest discover -s Tests/Scripts -v
```

Ver [`Tests/README.md`](Tests/README.md).

## CI

GitHub Actions:

| Workflow | Jobs |
|----------|------|
| **Tests** | Pre-Commits, Unit Tests, Integration Tests, MyPy, tests-summary (Python 3.14) |
| **PR-Agent** | Revisión automática de PR (requiere `OPENAI_KEY`) |
| **SonarCloud** | Análisis de calidad (requiere proyecto en [SonarCloud](https://sonarcloud.io) y secreto `SONAR_TOKEN`) |

Ficheros: `.github/workflows/tests.yml`, `pr_agent.yml`, `sonarcloud.yml`, `.pre-commit-config.yaml`, `mypy.ini`, `sonar-project.properties`, `.python-version`.

**SonarCloud (una vez):** inicia sesión en SonarCloud con GitHub → importa `Escape-Room` → copia `sonar.organization` y `sonar.projectKey` a `sonar-project.properties` si difieren → genera un token de organización → añádelo en GitHub como `SONAR_TOKEN`. Sin ese secreto, el job se omite y no bloquea la PR.

```bash
pre-commit run --all-files
mypy Juego/Consola Files/Scripts
```

## Dependencias

El juego en consola solo necesita Python 3.10+ (stdlib). Para scripts de mantenimiento, figuras de la memoria, build del `.exe` y la versión gráfica (pygame):

```bash
pip install -r requirements.txt
```

Pandoc (binario externo) para `Entrega/exportar_memoria.py`.

## Limpieza

```bash
python borrar_temporales.py
python borrar_temporales.py --dry-run
python borrar_temporales.py --solo-pycache
python borrar_temporales.py --solo-txt
```

Recorre todo el proyecto para `__pycache__`. Los `.txt` solo en `Juego/Informes/` y `Juego/Feedback/`.
