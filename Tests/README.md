# Tests — suite unificada

Pruebas del juego (`Tests/Juego/`, **123 tests**) y de los scripts de mantenimiento (`Tests/Scripts/`, **8 tests**). **Total: 131 tests.**

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

| Módulo | Enfoque |
|--------|---------|
| `test_compatibilidad_reglas_libre.py` | Combinaciones de reglas modo libre |
| `test_configuracion_libre.py` | Wizard y presets libre |
| `test_informe_examen.py` | Informes al cerrar partida |
| `test_feedback.py` | Modo feedback consola |
| `test_robustez_entrada.py` | Entrada de consola |
| `test_textos_ui.py` | Etiquetas y emojis compartidos (consola) |
| `test_presets_historia.py` | Catálogo modo historia |
| `test_resistencia_historia.py` | Eventos y escalada resistencia |
| `test_motor_resistencia_comun.py` | Turnos, racha, powerups |
| `test_preguntas_exclusivas_resistencia.py` | Pool exclusivo resistencia |
| `test_iconos_resistencia.py` | Emojis eventos/objetos |
| `test_rango_complejidad_libre.py` | Dificultad progresiva libre |

## Ficheros — `Tests/Scripts/`

| Módulo | Enfoque |
|--------|---------|
| `test_balance_validar.py` | Validación del banco (`balance_lib`) |
| `test_utils_plantillas_core.py` | Claves de contenido de plantillas |

La suite anterior en `Juego/Tests/` se migró aquí en junio 2026.
