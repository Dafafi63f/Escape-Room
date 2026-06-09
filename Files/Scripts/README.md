# Scripts — mantenimiento del banco

Herramientas de desarrollo del TFG. **No hacen falta para jugar**; el jugador solo necesita `Juego/juego_cuestionario.py` y `Data/`.

## Banco cerrado

`Data/Preguntas.csv` está protegido desde 2026-06-03. `guardar_filas_csv()` y scripts en `Files/Archivo/` fallan salvo `TFG_PERMITIR_CSV=1`.

**Flujo habitual:**

1. `mantenimiento.py validar`
2. `mantenimiento.py plantillas pipeline`
3. `mantenimiento.py criterios`
4. `mantenimiento.py auditar-distractores`

**No ejecutar** en operación normal: scripts en `Files/Archivo/`, ni `mantenimiento.py conservador|agresivo|ajustar|…`.

## Entrada principal — `mantenimiento.py`

```bash
python Files/Scripts/mantenimiento.py validar
python Files/Scripts/mantenimiento.py revision
python Files/Scripts/mantenimiento.py dataset
python Files/Scripts/mantenimiento.py plantillas pipeline
python Files/Scripts/mantenimiento.py duplicados --help
python Files/Scripts/mantenimiento.py temporales
python Files/Scripts/mantenimiento.py temporales --dry-run
```

| Comando | Función |
|---------|---------|
| `validar` [--detalle] | Balance y orden canónico (solo lectura) |
| `revision` / `revision --estadisticas` | Revisión del CSV |
| `dataset` [--variedad] | Validación extendida |
| `auditar-distractores` | Genera `Data/auditoria_distractores.md` |
| `auditar-plantillas` | Cobertura de `plantillas.json` |
| `plantillas pipeline` | limpiar → inyectar → repuesto → dedup |
| `criterios` | Actualiza `criterios_clasificacion_materia.csv` |
| `duplicados revisar` / `plantillas` | Ver `duplicados.py` |
| `temporales` | Limpieza de `__pycache__` bajo `Files/` |

Ver la cabecera de [`mantenimiento.py`](mantenimiento.py) para la lista completa. `pycache` es un alias de `temporales --solo-pycache`.

`balance.py` solo delega `validar`; el resto de comandos de balanceo antiguos están en `Archivo/`.

## Otros CLIs útiles

| Script | Uso |
|--------|-----|
| `cli_examen_historia.py` | Previsualizar plan de examen en consola |
| `clasificar_pregunta.py` | Clasificar una pregunta concreta (sin `--inplace` en banco cerrado) |
| `auditoria.py` | Auditorías del dataset y plantillas |
| `duplicados.py` + `duplicados_lib.py` | `revisar`, `plantillas`, `todo`, `exacto`, `enunciado` |
| `plantillas_sync.py` | `inyectar`, `limpiar`, `repuesto`, `pipeline` sobre `plantillas.json` |
| `equilibrar_pool_extra_juego.py` | Pool extra 24×40 para el juego (solo JSON) |
| `dedup_reemplazar_plantillas.py --inplace` | Purga sintéticas + catálogo internet + dedup |
| `validacion_dataset.py` | Revisión amplia del CSV |
| `exportar_criterios_clasificacion_materia.py` | Regenera `criterios_clasificacion_materia.csv` |
| `estadisticas_historic_qualificacions.py` | Estadísticas del histórico de qualificacions |

## Objetivos de balanceo (`objetivos_balanceo.py`)

- `TARGET_TOTAL_PREGUNTAS = 480`
- Por materia: 12 preguntas (2FT 2MT 2DT 2FC 2MC 2DC)
- Por tipo global: 240 Teoría / 240 Cálculo
- Por dificultad global: 160 / 160 / 160 (Fácil / Media / Difícil)
- Por respuesta correcta: 120 por letra A–D

**Clasificación por contenido:** `utils_clasificacion_pregunta.clasificar_pregunta(enunciado, A, B, C, D, correcta)` devuelve la mejor tripleta Materia + Tipo + Dificultad inferida del texto. La dificultad del banco canónico sigue la escalera del bloque (F/M/D); la inferida es orientativa.

## Utilidades (`utils_*`)

| Módulo | Función |
|--------|---------|
| `utils_dataset_csv.py` | CSV, columnas, guardado con metadatos, `borrar_pycache_en_proyecto` |
| `utils_banco_cerrado.py` | Protección del CSV cerrado |
| `objetivos_balanceo.py` | Objetivos 480, slots 12×40 |
| `balance_lib.py` | Validación y orden canónico (usado por `validar`) |
| `utils_orden_temas.py`, `utils_texto.py` | Orden de materias y normalización |
| `utils_deduplicacion.py` | Criterios de similitud |
| `utils_plantillas_pool.py` | Pool plantillas y etiqueta `dataset_480` |
| `utils_clasificacion_pregunta.py`, `utils_puntuacion_materia.py` | Clasificación semántica |
| `plantillas_repuesto_catalogo.py`, `catalogo_internet_plantillas.py` | Catálogos de ampliación |

No están pensados como API pública del juego; la lógica de partida vive en `Juego/Consola/`.

## Scripts unificados (nombres antiguos)

Estos nombres **ya no existen**; están cubiertos por los scripts actuales:

`validar_csv.py`, `revision_final.py`, `limpiar_plantillas.py`, `sincronizar_plantillas_repuesto.py`, `auditar_distractores.py`, `auditar_plantillas_global.py`, `asegurar_plantillas_sobre_dataset.py`, `revisar_plantillas.py`, `balancear_*.py`, `balanceo_completo.py`, `ordenar_dataset.py`, `eliminar_duplicados*.py`, `deduplicar_plantillas.py`

## Limpieza de temporales

Preferible desde la raíz del proyecto (abarca todo el TFG, no solo `Files/`):

```bash
python borrar_temporales.py
python borrar_temporales.py --dry-run
python borrar_temporales.py --solo-pycache
python borrar_temporales.py --solo-txt
python Files/Scripts/mantenimiento.py temporales
```
