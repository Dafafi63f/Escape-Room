# Tests — juego y gráfico

Pruebas unitarias del juego en directorio plano `Tests/` (dominio `Comun/`, interfaz `Grafico/` y flujos integrados).

**Suite actual:** **616** tests.

## Ejecutar

Desde la raíz del repositorio:

```bash
python -m unittest discover -s Tests -t . -v
python Files/mantenimiento.py validar
```

`Tests/Fixtures/support.py` configura `sys.path` hacia `Juego/` (y `Docs/` cuando hace falta, p. ej. limpieza). Cada módulo `test_*.py` debe llamar a `ensure_juego_path()` antes de importar `Comun` o `Grafico`.

Comprobación integral (datos + tests + banco): [`Files/health_check.py`](../Files/health_check.py).

En CI (`.github/workflows/tests.yml`): `PYTHONPATH` absoluto a `Juego/`, `SDL_VIDEODRIVER=dummy` y fuentes Noto Color Emoji para tests de renderizado.

## CI

GitHub Actions:

- **Tests** (`.github/workflows/tests.yml`) — suite unitaria + validación de banco/health check, mypy, pre-commit
- **SonarCloud** (`.github/workflows/sonarcloud.yml`) — análisis estático en CI (requiere `SONAR_TOKEN` y Automatic Analysis desactivado)
- **Paquete jugable** (`.github/workflows/paquete-jugable.yml`) — publica `MATCAD_juego_portable.zip` en el release `juego`

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
| `test_grafico_ui.py` | Textos, tooltips, barra de estado, datos locales y limpieza (`Docs/utilidades.py`) |
| `test_grafico_menus.py` | Menús pygame, pausa, feedback, info y hover |
| `test_resistencia.py` | Modo resistencia: partida, récords en estadísticas, motor, exclusivas e iconos |
| `test_escape_room.py` | Escape room: puertas, tienda, botín, pity, inventario, semillas |
| `test_eventos_partida.py` | Catálogo de eventos compartido (escape y resistencia) |
| `test_semillas.py` | Semillas diaria, aleatoria, resolución de partida y avance de `RngPartida` |
| `test_carga_contenido.py` | Perfil de contenido y paquete mínimo/completo |
| `test_rutas.py` | Resolución de rutas a `Data/` y `Data/Juego/` |
| `test_capacidades_historia.py` | Capacidades del modo historia según perfil de contenido |
| `test_estadisticas_jugador.py` | Estadísticas locales agregadas y récords |
| `test_flujos_especiales_ui.py` | Flujos UI de escape room y resistencia (semilla fija) |
| `test_atajos_y_examen_dirigido.py` | Atajos de teclado y examen dirigido |
| `test_metadatos_inferidos.py` | Metadatos inferidos (CSV mínimo) |
| `test_jefe_partida.py` | Jefe en escape / resistencia |
| `test_maldiciones.py` | Maldiciones de resistencia |
| `test_objetos_powerups.py` | Objetos y power-ups |
| `test_pity_variedad_resistencia.py` | Pity y variedad en resistencia |
| `test_zip_portable.py` | Generación del zip jugable (contenido mínimo, sin Tests/Docs/Files) |

## `Fixtures/` (soporte, no tests)

Utilidades y fixtures usados por los `test_*.py` de la raíz. `unittest discover -s Tests` solo recoge módulos `test_*.py` en `Tests/`, no en subcarpetas.

| Fichero (`Tests/Fixtures/`) | Uso |
|---------|-----|
| `support.py` | Bootstrap de `sys.path` (`ensure_juego_path`, `ensure_docs_path`, …) |
| `adaptador_juego.py` | Adaptador de dominio para tests |
| `helpers_navegacion_grafico.py` | Utilidades para tests gráficos |
| `generar_preguntas_minimal.py` | Regenera `Data/Privado/Preguntas_minimal.csv` desde el banco |
