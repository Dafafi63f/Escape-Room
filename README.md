# Cuestionario MATCAD — TFG

**Título:** Diseño y desarrollo de un juego interactivo educativo basado en contenidos del grado en Matemática Computacional y Análisis de Datos.

**Alumno:** Daniel Fageda Figueredo · **NIU:** 1601846 · **Tutor:** Víctor Navas Portella

Sistema de cuestionarios académicos con banco de **480 preguntas**, juego en **pygame** (modos libre, historia, resistencia, escape room y feedback), y herramientas de mantenimiento del dataset. La idea original del escape room se inspira en las aventuras point-and-click de [Inka Games](https://www.inkagames.com/); el entregable las adapta al plan MatCAD (véase §1.3 de la memoria).

- **Documentación y entrega del TFG:** [`Docs/`](Docs/README.md) (`Entrega/`, `Figuras/`, changelogs)
- **Repositorio:** https://github.com/Dafafi63f/Escape-Room.git

```bash
git clone https://github.com/Dafafi63f/Escape-Room.git
```

No incluyas tokens, contraseñas ni claves privadas en archivos versionados.

## Documentación del proyecto

| Tema | Dónde |
|------|-------|
| Esquema del banco, materias, diagramas curriculares | [`Data/README.md`](Data/README.md) |
| Juego, modos y controles | [`Juego/README.md`](Juego/README.md) |
| Lógica interna (bancos, puntuación, filtros) | [`Juego/Comun/README.md`](Juego/Comun/README.md) · UI gráfica: [`Juego/Grafico/README.md`](Juego/Grafico/README.md) |
| Scripts de mantenimiento y balanceo | [`Files/README.md`](Files/README.md) |
| Pruebas unitarias | [`Tests/README.md`](Tests/README.md) |
| Banco de preguntas (480 ítems) | [`Data/README.md`](Data/README.md) |
| Documentación y entrega del TFG | [`Docs/README.md`](Docs/README.md) |

## Estructura

| Carpeta / fichero | Rol |
|------------------|-----|
| [`Juego/`](Juego/README.md) | Lanzador, [`Comun/`](Juego/Comun/README.md), [`Grafico/`](Juego/Grafico/README.md) |
| [`Data/`](Data/README.md) | CSV, plantillas, histórico de qualificacions |
| [`Files/`](Files/README.md) | Mantenimiento del banco (no necesario para jugar) |
| [`Docs/`](Docs/README.md) | Changelogs, `Entrega/` (memoria md/tex/docx), `Figuras/` |
| [`Tests/`](Tests/README.md) | Pruebas unitarias (**424** tests: 416 en `Tests/` + 8 en `Files/`) y CI |
| [`Docs/utilidades_tfg.py`](Docs/utilidades_tfg.py) | Regeneración (memoria + .exe) + limpieza final + zip portable |
| [`Juego/requirements.txt`](Juego/requirements.txt) | Solo jugar (pygame-ce) |
| [`requirements.txt`](requirements.txt) | Desarrollo completo (incluye el del juego) |
| [`Juego/COMO_JUGAR.md`](Juego/COMO_JUGAR.md) | Requisitos Python / `.exe` / zip portable |

## Memoria — exportar Word

El borrador editable está en [`Docs/Entrega/Memoria_TFG.md`](Docs/Entrega/Memoria_TFG.md). LaTeX y Word en el mismo directorio [`Docs/Entrega/`](Docs/README.md); figuras en [`Docs/Figuras/`](Docs/Figuras/README.md):

```bash
python Docs/generar_figuras_memoria.py
python Docs/utilidades_tfg.py                 # memoria + .exe → limpieza final
python Docs/utilidades_tfg.py --sin-exe       # memoria sin .exe (más rápido)
```

Genera los `.docx` en `Docs/Entrega/` (Pandoc). El PDF de entrega lo exportas desde Word tras editar. Detalle en [`Docs/README.md`](Docs/README.md).

Solo una fase: `--solo-memoria`, `--solo-exe` o `--solo-limpieza`.

## Jugar

Guía completa (Python, pip, `.exe`, PCs restringidos, zip portable): [`Juego/COMO_JUGAR.md`](Juego/COMO_JUGAR.md).

```bash
pip install -r Juego/requirements.txt
python Juego/juego_grafico.py
```

En Windows también: doble clic en [`Juego/Distribucion/Jugar.bat`](Juego/Distribucion/Jugar.bat). Diagnóstico:

```powershell
powershell -ExecutionPolicy Bypass -File Juego\Scripts\comprobar_entorno.ps1
```

Instalar Python + pygame si hace falta (usa `winget` cuando esté disponible):

```powershell
powershell -ExecutionPolicy Bypass -File Juego\Scripts\instalar_entorno.ps1
```

### Zip portable (`Juego/Distribucion/MATCAD_juego_portable.zip`)

No incluye Python, el `.exe` ni scripts `.ps1`. Tras descomprimir, lee `Juego/LEEME.txt` e instala Python manualmente.

```bash
python Docs/utilidades_tfg.py --solo-zip
```

### Ejecutable Windows (alternativa sin Python)

```powershell
pip install -r requirements.txt   # desarrollo (PyInstaller, etc.)
python Docs/utilidades_tfg.py --solo-exe
```

También: `.\Juego\Scripts\build_exe_onefile.ps1`. Salida: `Juego/Distribucion/juego_grafico.exe`. En PCs con `.exe` bloqueados, usa la vía Python. Detalle en [`Juego/README.md`](Juego/README.md) y [`Juego/COMO_JUGAR.md`](Juego/COMO_JUGAR.md).

### Datos

Ver [`Data/README.md`](Data/README.md). Imprescindibles: `Data/Banco/Preguntas.csv`, `listado_materias.csv`. Modo historia: `Historic_qualificacions_MatCAD_completo.csv`, `Data/Juego/presets.json`. Modo resistencia: `Data/Juego/preguntas_resistencia.json`, rankings en `Data/Juego/`. Modo escape room: mismos presets y banco que resistencia (`presets.json`, pool cerrado). Modo con plantillas: `Data/Banco/plantillas.json`.

Configuración privada del creador (SMTP, GitHub, etc.): `Data/Banco/creador_privado.json` (local; plantilla en [`Juego/Comun/feedback.py`](Juego/Comun/feedback.py)).

## Pruebas

```bash
python -m unittest discover -s Tests -v
```

Solo juego o solo scripts:

```bash
python -m unittest discover -s Tests -v
python -m unittest discover -s Files -p "test_*.py" -v
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
mypy Juego/Comun Juego/Grafico Files
```

## Dependencias

| Fichero | Para quién |
|---------|------------|
| [`Juego/requirements.txt`](Juego/requirements.txt) | **Jugar** (solo pygame-ce) |
| [`requirements.txt`](requirements.txt) | Desarrollo, tests, memoria y empaquetado |

Python **3.10+** y `pip`. Pandoc (binario externo) solo para exportar la memoria Word.

## Utilidades locales

Por defecto **regenera la memoria** y **limpia al final**:

```bash
python Docs/utilidades_tfg.py
python Docs/utilidades_tfg.py --sin-exe             # sin juego_grafico.exe
python Docs/utilidades_tfg.py --solo-memoria
python Docs/utilidades_tfg.py --solo-memoria --con-exe
python Docs/utilidades_tfg.py --solo-exe
python Docs/utilidades_tfg.py --solo-limpieza
python Docs/utilidades_tfg.py --dry-run            # listar limpieza sin borrar; luego exporta
```

Limpieza acotada:

```bash
python Docs/utilidades_tfg.py --solo-limpieza --solo-pycache
python Docs/utilidades_tfg.py --solo-limpieza --solo-juego
python Docs/utilidades_tfg.py --solo-limpieza --solo-txt
python Docs/utilidades_tfg.py --solo-limpieza --solo-entrega
```

La limpieza final recorre el proyecto (`__pycache__`, runtime en `Data/Juego/`, intermedios de `Docs/Entrega/`, restos de PyInstaller en `Juego/`).

Desde el juego: **borrar** `.txt`; **vaciar** preferencias y rankings (los `.json` se conservan). Presets y pool de resistencia no se tocan en ningún caso.
