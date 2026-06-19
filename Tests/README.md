# Tests — juego y scripts

Pruebas en directorio plano `Tests/` (juego, gráfico, consola). Tests de mantenimiento en [`Files/test_*.py`](../Files/README.md#pruebas).

**Suite actual:** **262 tests** (254 en `Tests/` + 8 en `Files/`).

## Ejecutar

Desde la raíz del TFG:

```bash
python -m unittest discover -s Tests -v
python -m unittest discover -s Files -p "test_*.py" -v
```

`Tests/support.py` configura `sys.path` hacia `Juego/`. Cada módulo `test_*.py` debe llamar a `ensure_juego_path()` antes de importar `Comun` o `Grafico`.

En CI (`.github/workflows/tests.yml`) se fijan `PYTHONPATH=Juego` y `SDL_VIDEODRIVER=dummy` para pygame sin pantalla.

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
| `test_consola_paridad.py` | Entrada consola y paridad consola↔gráfico |
| `test_grafico_ui.py` | Textos, tooltips, barra de estado y datos locales |
| `test_grafico_menus.py` | Menús pygame, pausa, feedback, info y hover |
| `test_resistencia_historia.py` | Pool, escalada y ranking resistencia |
| `test_resistencia_motor.py` | Motor, mecánicas, exclusivas e iconos |
| `helpers_navegacion_grafico.py` | Utilidades para tests gráficos (no es test) |
| `paridad_juegos.py` | Builders compartidos para paridad |
| `support.py` | Bootstrap de `sys.path` |
