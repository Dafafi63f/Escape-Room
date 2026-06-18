# Tests — suite unificada

Pruebas del juego (`Tests/Juego/`) y de los scripts de mantenimiento (`Tests/Scripts/`).

Los tests de la interfaz gráfica (`Juego/Grafico/`) viven en la rama `feature/juego-grafico-pygame`.

## Ejecutar

Desde la raíz del TFG:

```bash
python -m unittest discover -s Tests -v
```

Solo un bloque:

```bash
python -m unittest discover -s Tests/Juego -v
python -m unittest discover -s Tests/Scripts -v
```

`Tests/support.py` configura `sys.path` hacia `Juego/` y `Files/Scripts/`.

Los subdirectorios llevan `__init__.py` para que `discover -s Tests` encuentre todos los módulos de test.

## CI

GitHub Actions (`.github/workflows/tests.yml`): en PRs se ejecuta con `pull_request`; en `main`, tras el merge, con `push`.

- **Pre-Commits** — hooks de formato y YAML
- **Run Unit Tests** — `Tests/Juego/` y `Tests/Scripts/` (Python 3.14, ver `.python-version`)
- **Run Integration Tests** — suite completa + `mantenimiento.py validar`
- **Run MyPy** — tipado en `Juego/Comun/`, `Juego/Consola/` y `Files/Scripts/`
- **tests-summary** — agrega el resultado de los jobs anteriores

También: **PR-Agent** (`OPENAI_KEY`) y **SonarCloud** (`SONAR_TOKEN`).

## Ficheros — `Tests/Juego/`

Los módulos `test_*.py` agrupan tests relacionados (cada fichero puede contener varias clases `Test*`).

| Módulo | Enfoque |
|--------|---------|
| `test_libre.py` | Reglas, wizard y complejidad del modo libre |
| `test_presets_historia.py` | Catálogo historia y modos especiales |
| `test_informe_feedback.py` | Informes y feedback |
| `test_consola_paridad.py` | Entrada consola y paridad de dominio |
| `test_resistencia_historia.py` | Pool, escalada y ranking resistencia |
| `test_resistencia_motor.py` | Motor, mecánicas, exclusivas e iconos |
| `paridad_juegos.py` | Builders compartidos para paridad |

## Ficheros — `Tests/Scripts/`

| Módulo | Enfoque |
|--------|---------|
| `test_balance_validar.py` | Validación del banco (`balance_lib`) |
| `test_utils_plantillas_core.py` | Claves de contenido de plantillas |

La suite anterior en `Juego/Tests/` se migró aquí en junio 2026. Los ficheros individuales muy pequeños se agruparon en los módulos de la tabla.
