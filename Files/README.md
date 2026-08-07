# Files — mantenimiento del banco

Scripts y utilidades de **mantenimiento del banco**. No son necesarios para jugar; el jugador solo necesita `Juego/juego_grafico.py` y `Data/`.

Limpieza de artefactos temporales: [`borrar_temporales.py`](borrar_temporales.py) o [`../Docs/utilidades_tfg.py`](../Docs/utilidades_tfg.py) (`--solo-limpieza`).

## Bancos cerrados (pool juego: **1000** preguntas reales)

Sin campo ``variaciones`` en `plantillas.json`: cada fila es una pregunta definitiva.
No se prevén altas ni bajas; solo **revisión** de enunciados y distractores.

| Archivo | Estado | Override |
|---------|--------|----------|
| `Data/Banco/Preguntas.csv` | 480 preguntas revisadas (2026-06-03) | `TFG_PERMITIR_CSV=1` |
| `Data/Banco/plantillas.json` | 960 filas (480 revisadas + 480 extras); **repo del autor**, no zip portable | `TFG_PERMITIR_PLANTILLAS=1` |
| 40 exclusivas resistencia | `Juego/Comun/preguntas_resistencia_exclusivas_datos.py` | Editar el `.py` (pool = **1000**) |

Rutas canónicas: [`rutas_data.py`](rutas_data.py) (`DATA_BANCO`, `DATA_JUEGO`).

Toda escritura en `plantillas.json` pasa por `utils_banco_cerrado.guardar_plantillas_json()`.

### Base vs banco ampliado (qué queda por revisar)

| Pool | Filas | Revisión manual |
|------|-------|----------------|
| **Base** (`Preguntas.csv` + `uso: dataset_480` en JSON) | 480 | Completada: enunciado, distractores, materia, tipo, dificultad |
| **Ampliado** (`internet`, `repuesto`, `general`, …) | 480 | Metadatos OK; **pendiente: enunciado y opciones A–D** |

`clasificar_pregunta.py` y `plantillas reclasificar` leen `Data/Banco/criterios_clasificacion_materia.csv` (cerrado; editar a mano si hiciera falta).

```bash
python Files/mantenimiento.py auditar-distractores              # todo el JSON
python Files/mantenimiento.py auditar-distractores --solo-dataset  # solo las 480 base
python Files/mantenimiento.py auditar-plantillas
python Files/clasificar_pregunta.py --dataset --solo-incoherentes
```

**Flujo habitual (solo lectura):**

1. `mantenimiento.py validar`
2. `mantenimiento.py auditar-plantillas`
3. `mantenimiento.py auditar-distractores`

## Entrada principal — `mantenimiento.py`

```bash
python Files/mantenimiento.py validar
python Files/mantenimiento.py revision
python Files/mantenimiento.py auditar-plantillas
python Files/mantenimiento.py auditar-distractores
python Files/mantenimiento.py duplicados revisar
```

| Comando | Función |
|---------|---------|
| `validar` [--detalle] | Balance y orden canónico (solo lectura) |
| `revision` / `revision --estadisticas` | Revisión del CSV |
| `dataset` [--variedad] | Validación extendida |
| `auditar-distractores` [--json RUTA] [--solo-dataset] | Auditoría de opciones A–D |
| `auditar-plantillas` | Cobertura y balance de `plantillas.json` (960 filas) |
| `plantillas comprobar` | Comprueba 24 filas/materia (12+12) |
| `plantillas reclasificar` | Audita materia (sin `--aplicar`: solo lectura) |
| `duplicados revisar` | Informe de duplicados (sin escribir) |
| `temporales` | Limpieza de `__pycache__` bajo el proyecto |

**Bloqueados** (plantillas cerradas; requieren `TFG_PERMITIR_PLANTILLAS=1`):
`plantillas reclasificar --aplicar`, `duplicados plantillas`, `duplicados todo --inplace`, etc.

Los scripts de **regeneración del JSON** (equilibrador, catálogos repuesto/internet, pipeline de inyección) se eliminaron en 2026-06: el banco quedó materializado en `plantillas.json`. Para recuperarlos, usar el historial de git con `TFG_PERMITIR_PLANTILLAS=1`.

## Simulaciones (memoria TFG)

| Script | Uso |
|--------|-----|
| `simulacion_evaluacion_azar.py` | Monte Carlo: respuestas al azar (§5.7) |
| `simulacion_pity.py` | Análisis del sistema de pity (§5.8) |

Figuras: `python Docs/generar_figuras_memoria.py`

## Utilidades (`utils_*`)

| Módulo | Función |
|--------|---------|
| `utils_banco_cerrado.py` | Protección CSV + plantillas.json |
| `utils_dataset_csv.py` | CSV, columnas, guardado con metadatos |
| `objetivos_balanceo.py` | Objetivos 480 / 960 JSON, `USO_PLANTILLA_DATASET` |
| `balance_lib.py` | Validación y orden canónico (usado por `validar`) |
| `utils_clasificacion_pregunta.py`, `utils_puntuacion_materia.py` | Clasificación semántica (auditoría) |
| `utils_plantillas_core.py` | Reexporta `Juego/Comun/utils_plantillas_core.py` |

## Seguridad — qué puede romper el juego

| Riesgo | Protección |
|--------|------------|
| **Modificar `Preguntas.csv`** | `TFG_PERMITIR_CSV=1` |
| **Modificar `plantillas.json`** | `TFG_PERMITIR_PLANTILLAS=1` |
| **Modificar exclusivas resistencia** | Editar `Juego/Comun/preguntas_resistencia_exclusivas_datos.py` |
| **Solo lectura (seguros)** | `validar`, `revision`, `auditar-*`, `clasificar_pregunta.py`, `duplicados revisar` |

## Verificación

Validación del banco (no forma parte de la suite de tests del juego):

```bash
python Files/mantenimiento.py validar
python Files/health_check.py
```

Suite del juego: [`Tests/`](../Tests/README.md). CI: `.github/workflows/tests.yml`.

## Limpieza de temporales

```bash
python Docs/utilidades_tfg.py --solo-limpieza
python Files/mantenimiento.py temporales
```
