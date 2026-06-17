# Archivo — scripts legado del CSV (solo consulta histórica)

> **No usar en el día a día del TFG.** Este directorio conserva scripts de regeneración del banco cerrado (2026-06). Para validar o mantener datos actuales, usa siempre [`../Scripts/mantenimiento.py`](../Scripts/mantenimiento.py).

Scripts antiguos de **regeneración y reequilibrio** del dataset (`Data/CSV/Preguntas.csv`). El banco en producción es cerrado (480 preguntas); estos comandos están bloqueados salvo `TFG_PERMITIR_CSV=1`.

Para el día a día del banco cerrado, usa [`../Scripts/mantenimiento.py`](../Scripts/mantenimiento.py) (`validar`, `revision`, `plantillas`, etc.).

## Seguridad

```text
TFG_PERMITIR_CSV=1
```

Sin esta variable, las operaciones que escriben en `Data/CSV/Preguntas.csv` no deben ejecutarse en un banco ya validado. La comprobación está en `utils_banco_cerrado.py`.

## Catálogo de scripts legado

| Script | Motivo en Archivo |
|--------|-------------------|
| `dataset_pipeline.py` | Regeneración masiva del CSV |
| `fix_final_materias.py` | Reclasificación y guardado del banco (histórico) |
| `aplicar_clasificacion_optima.py`, `aplicar_correcciones_materia.py` | Sustitución/regeneración por contenido |
| `ampliar_dataset_480.py` | Ampliación 400→480 (ya aplicada) |
| `ampliar_plantillas.py`, `ampliar_plantillas_desde_web.py` | Ampliación antigua del JSON (sustituido por `equilibrar` + `catalogo_internet`) |
| `reducir_dataset_objetivo.py`, `crear_borrar_preguntas.py` | Ajuste de tamaño del CSV |
| `recategorizar_y_equilibrar.py`, `reparar_materia_algoritmes.py` | Movimientos puntuales de Ids |
| `limpiar_duplicados_csv.py`, `revisar_castellano_csv.py` | Limpieza/ortografía CSV |
| `revisar_materia_contenido.py` | Revisión/sustitución por materia |
| `variedad_materias.py` + `utils_variedad.py` | Variedad temática (Jaccard) |
| `dataset_plantillas_cli.py`, `materias_cli.py` | Enrutadores CLI antiguos |
| `sync_plantillas_materias.py` | Reubica plantillas (sustituido por `plantillas pipeline`) |
| `balance.py` | Copia legacy de validación; usar `Files/Scripts/balance.py` o `mantenimiento.py validar` |

## Ejemplos (solo mantenimiento avanzado)

| Script | Notas |
|--------|-------|
| `balance.py` | Balanceo histórico del pool |
| `ampliar_plantillas.py` | Ampliación desde plantillas |
| `crear_borrar_preguntas.py` | Alta/baja manual de filas |
| `reducir_dataset_objetivo.py` | Reducción a un tamaño objetivo |
