# Tests — suite unificada

Pruebas del juego (`Tests/Juego/`, 49 tests) y de los scripts de mantenimiento (`Tests/Scripts/`, 8 tests). **Total: 57 tests.**

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

## Ficheros

| Carpeta | Enfoque |
|---------|---------|
| `Tests/Juego/` | Informes, entrada de consola, feedback, configuración libre, compatibilidad de reglas |
| `Tests/Scripts/` | `utils_plantillas_core`, validación del banco (`balance_lib`) |

La suite anterior en `Juego/Tests/` se migró aquí en junio 2026.
