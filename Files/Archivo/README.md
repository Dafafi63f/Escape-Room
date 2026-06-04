# Archivo — scripts legado del CSV

Scripts antiguos de **regeneración y reequilibrio** del dataset (`Preguntas.csv`). El banco en producción es cerrado (480 preguntas); estos comandos pueden estar bloqueados salvo que actives explícitamente la edición del CSV.

## Seguridad

Muchos scripts comprueban la variable de entorno:

```text
TFG_PERMITIR_CSV=1
```

Sin ella, las operaciones que escriben en `Data/Preguntas.csv` no deben ejecutarse en un banco ya validado.

## Ejemplos (solo mantenimiento avanzado)

| Script | Notas |
|--------|-------|
| `balance.py` | Balanceo histórico del pool |
| `ampliar_plantillas.py` | Ampliación desde plantillas |
| `crear_borrar_preguntas.py` | Alta/baja manual de filas |
| `reducir_dataset_objetivo.py` | Reducción a un tamaño objetivo |

Para el día a día del banco cerrado, usa [`../Scripts/mantenimiento.py`](../Scripts/mantenimiento.py) (`validar`, `revision`, `plantillas`, etc.).
