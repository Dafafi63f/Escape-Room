# Cuestionario MATCAD — TFG

**Título:** Diseño y desarrollo de un juego interactivo educativo basado en contenidos del grado en Matemática Computacional y Análisis de Datos.

**Alumno:** Daniel Fageda Figueredo · **NIU:** 1601846 · **Tutor:** Víctor Navas Portella

Sistema de cuestionarios académicos con banco de **480 preguntas**, juego en **pygame** (modos libre, historia, resistencia y feedback), y herramientas de mantenimiento del dataset. La capa narrativa escape room queda como evolución futura.

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
| [`Tests/`](Tests/README.md) | Pruebas unitarias (**246** tests: 238 en `Tests/` + 8 en `Files/`) y CI |
| [`utilidades_tfg.py`](utilidades_tfg.py) | Limpieza + exportación Word (por defecto ambas) |
| [`requirements.txt`](requirements.txt) | Dependencias (pandas, matplotlib, pyinstaller, pygame-ce, mypy, pre-commit) |

## Memoria — exportar Word

El borrador editable está en [`Docs/Entrega/Memoria_TFG.md`](Docs/Entrega/Memoria_TFG.md). LaTeX y Word en el mismo directorio [`Docs/Entrega/`](Docs/README.md); figuras en [`Docs/Figuras/`](Docs/Figuras/README.md):

```bash
python Docs/generar_figuras_memoria.py
python utilidades_tfg.py
```

Genera los `.docx` en `Docs/Entrega/` (Pandoc). El PDF de entrega lo exportas desde Word tras editar. Detalle en [`Docs/README.md`](Docs/README.md).

Solo una tarea: `python utilidades_tfg.py --solo-limpieza` o `--solo-memoria`.

## Jugar

```bash
pip install -r requirements.txt
python Juego/juego_grafico.py
```

### Ejecutable Windows (opcional)

```powershell
pip install -r requirements.txt
.\Juego\build_exe_onefile.ps1
```

Salida: `Juego/juego_grafico.exe`. Detalle en [`Juego/README.md`](Juego/README.md).

### Datos

Ver [`Data/README.md`](Data/README.md). Imprescindibles: `Data/Banco/Preguntas.csv`, `listado_materias.csv`. Modo historia: `Historic_qualificacions_MatCAD_completo.csv`, `Data/Juego/presets_historia.json`. Modo resistencia: `Data/Juego/preguntas_resistencia.json`, rankings en `Data/Juego/`. Modo con plantillas: `Data/Banco/plantillas.json`.

Configuración privada del creador (SMTP, GitHub, etc.): `Data/Banco/creador_privado.json` (local; plantilla en [`Juego/Comun/config_creador.py`](Juego/Comun/config_creador.py)).

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

El juego necesita Python 3.10+ y las dependencias de `requirements.txt` (pygame-ce, etc.). Para scripts de mantenimiento y figuras de la memoria:

```bash
pip install -r requirements.txt
```

Pandoc (binario externo) para la exportación Word (`utilidades_tfg.py`).

## Utilidades locales

Por defecto limpia temporales **y** regenera los Word de la memoria:

```bash
python utilidades_tfg.py
python utilidades_tfg.py --dry-run          # listar limpieza sin borrar; luego exporta
python utilidades_tfg.py --solo-limpieza
python utilidades_tfg.py --solo-memoria
```

Limpieza acotada:

```bash
python utilidades_tfg.py --solo-limpieza --solo-pycache
python utilidades_tfg.py --solo-limpieza --solo-juego
python utilidades_tfg.py --solo-limpieza --solo-txt
```

Recorre todo el proyecto para `__pycache__` y cachés. En `Data/Juego/` **elimina del disco** lo generado al jugar (`preferencias_*.json`, `ranking_*.json`, `*.txt`).

Desde el juego: **borrar** `.txt`; **vaciar** preferencias y rankings (los `.json` se conservan). Presets y pool de resistencia no se tocan en ningún caso.
