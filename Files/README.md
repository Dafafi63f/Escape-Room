# Files — mantenimiento del banco

Scripts y utilidades de **mantenimiento del banco**. No son necesarios para jugar; el jugador solo necesita `Juego/juego_consola.py` o `Juego/juego_grafico.py` y `Data/`.

Limpieza de artefactos temporales: [`../utilidades_tfg.py`](../utilidades_tfg.py) (`--solo-limpieza`).

## Banco cerrado

`Data/Banco/Preguntas.csv` está protegido desde 2026-06-03. `guardar_filas_csv()` falla salvo `TFG_PERMITIR_CSV=1`.

Rutas canónicas: [`rutas_data.py`](rutas_data.py) (`DATA_BANCO`, `DATA_JUEGO`).

**Flujo habitual:**

1. `mantenimiento.py validar`
2. `mantenimiento.py plantillas pipeline`
3. `mantenimiento.py criterios`
4. `mantenimiento.py auditar-distractores`

## Entrada principal — `mantenimiento.py`

```bash
python Files/mantenimiento.py validar
python Files/mantenimiento.py revision
python Files/mantenimiento.py dataset
python Files/mantenimiento.py plantillas pipeline
python Files/mantenimiento.py duplicados --help
python Files/mantenimiento.py temporales
python Files/mantenimiento.py temporales --dry-run
```

| Comando | Función |
|---------|---------|
| `validar` [--detalle] | Balance y orden canónico (solo lectura) |
| `revision` / `revision --estadisticas` | Revisión del CSV |
| `dataset` [--variedad] | Validación extendida |
| `auditar-distractores` [--json RUTA] [--solo-dataset] | Auditoría de opciones A–D |
| `auditar-plantillas` | Cobertura de `plantillas.json` |
| `plantillas pipeline` | limpiar → inyectar → repuesto → dedup |
| `criterios` | Actualiza `Banco/criterios_clasificacion_materia.csv` |
| `duplicados revisar` / `plantillas` | Ver `duplicados.py` |
| `temporales` | Limpieza de `__pycache__` bajo el proyecto |

## Simulación de evaluación al azar

```bash
python Files/simulacion_evaluacion_azar.py
python Files/simulacion_evaluacion_azar.py --iteraciones 50000 --preguntas 20
```

## Otros CLIs útiles

| Script | Uso |
|--------|-----|
| `cli_examen_historia.py` | Previsualizar plan de examen en consola |
| `clasificar_pregunta.py` | Clasificar una pregunta concreta (solo lectura) |
| `auditoria.py` | Auditorías del dataset y plantillas |
| `duplicados.py` + `duplicados_lib.py` | `revisar`, `plantillas`, `todo`, `exacto`, `enunciado` |
| `plantillas_sync.py` | `inyectar`, `limpiar`, `repuesto`, `pipeline` sobre `Banco/plantillas.json` |
| `equilibrar_pool_extra_juego.py` | Pool extra para modos beta del juego (solo JSON) |
| `dedup_reemplazar_plantillas.py --inplace` | Purga sintéticas + catálogo internet + dedup |
| `validacion_dataset.py` | Revisión amplia del CSV |
| `exportar_criterios_clasificacion_materia.py` | Regenera `Banco/criterios_clasificacion_materia.csv` |
| `estadisticas_historic_qualificacions.py` | Estadísticas del histórico de qualificacions |
| `rutas_data.py` | Rutas `Data/Banco/` y `Data/Juego/` |

## Utilidades (`utils_*`)

| Módulo | Función |
|--------|---------|
| `utils_dataset_csv.py` | CSV, columnas, guardado con metadatos |
| `utils_banco_cerrado.py` | Protección del CSV cerrado |
| `objetivos_balanceo.py` | Objetivos 480, slots 12×40 |
| `balance_lib.py` | Validación y orden canónico (usado por `validar`) |
| `utils_plantillas_core.py` | Claves de contenido y expansión (compartido con `Juego/Comun/datos.py`) |
| `utils_clasificacion_pregunta.py`, `utils_puntuacion_materia.py` | Clasificación semántica |

## Seguridad — qué puede romper el juego

| Riesgo | Scripts | Protección |
|--------|---------|------------|
| **Modificar `Preguntas.csv`** | `duplicados.py` con `--inplace`, funciones de `balance_lib` | Bloqueado salvo `TFG_PERMITIR_CSV=1` |
| **Modificar `plantillas.json`** | `plantillas_sync.py`, `equilibrar_pool_extra_juego.py`, `dedup_reemplazar_plantillas.py` con `--inplace` | Afecta modos beta; no toca el CSV de 480 |
| **Solo lectura (seguros)** | `validar`, `revision`, `auditar-*`, `clasificar_pregunta.py`, `simulacion_evaluacion_azar.py` | No escriben datos del juego |

## Pruebas

Tests de mantenimiento en este directorio (plano):

| Módulo | Enfoque |
|--------|---------|
| `test_balance_validar.py` | Validación del banco (`balance_lib`) |
| `test_utils_plantillas_core.py` | Claves de contenido de plantillas |
| `test_support.py` | Bootstrap de `sys.path` para los tests |

```bash
python -m unittest discover -s Files -p "test_*.py" -v
```

Tests del juego: [`Tests/`](../Tests/README.md) (**262** tests en total). CI: `.github/workflows/tests.yml`.

## Limpieza de temporales

```bash
python utilidades_tfg.py --solo-limpieza
python Files/mantenimiento.py temporales
```
