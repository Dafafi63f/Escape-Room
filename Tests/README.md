# Tests — juego y scripts

Pruebas en directorio plano `Tests/` (juego y gráfico). Tests de mantenimiento en [`Files/test_*.py`](../Files/README.md#pruebas).

**Suite actual:** **258 tests** (250 en `Tests/` + 8 en `Files/`).

## Ejecutar

Desde la raíz del TFG:

```bash
python -m unittest discover -s Tests -t . -v
python -m unittest discover -s Files -p "test_*.py" -v
```

`Tests/support.py` configura `sys.path` hacia `Juego/`. Cada módulo `test_*.py` debe llamar a `ensure_juego_path()` antes de importar `Comun` o `Grafico`.

```bash
python -m unittest discover -s Tests -t . -v
python -m unittest discover -s Files -p "test_*.py" -v
python Files/mantenimiento.py validar
```

En CI (`.github/workflows/tests.yml`): `PYTHONPATH` absoluto a `Juego/`, `SDL_VIDEODRIVER=dummy` y fuentes Noto Color Emoji para tests de renderizado.

## CI

GitHub Actions (`.github/workflows/tests.yml`):

- **Run Unit Tests** — `Tests/` y `Files/test_*.py`
- **Run Integration Tests** — ambas suites + `Files/mantenimiento.py validar`

## Ficheros

| Módulo | Enfoque |
|--------|---------|
| `test_libre.py` | Reglas, wizard y complejidad del modo libre |
| `test_presets_historia.py` | Catálogo historia y modos especiales |
| `test_informe_feedback.py` | Informes y feedback |
| `test_changelog_juego.py` | Carga de changelogs desde `Docs/` |
| `test_comun_servicios.py` | Config creador, cierre de informe e imports migrados |
| `test_lanzador_grafico.py` | Arranque de `juego_grafico.py` sin ventana |
| `test_dominio_juego.py` | Dominio del juego gráfico (datos, reglas, evaluación) |
| `test_grafico_ui.py` | Textos, tooltips, barra de estado y datos locales |
| `test_grafico_menus.py` | Menús pygame, pausa, feedback, info y hover |
| `test_resistencia_historia.py` | Pool, escalada y ranking resistencia |
| `test_resistencia_motor.py` | Motor, mecánicas, exclusivas e iconos |
| `helpers_navegacion_grafico.py` | Utilidades para tests gráficos (no es test) |
| `adaptador_juego.py` | Adaptador de dominio para tests |
| `support.py` | Bootstrap de `sys.path` |
