# -*- coding: utf-8 -*-
"""
Banco de preguntas cerrado (480 filas CSV, revisado 2026-06-03).

``plantillas.json`` cerrado (960 filas: 480 dataset + 480 extra, 2026-06-27).
Sin campo ``variaciones``: cada fila es una pregunta real y definitiva.

Pool del juego cerrado en **1000** preguntas reales (2026-06-27):
  480 revisadas (CSV) + 480 extras JSON + 40 exclusivas resistencia (embebidas en Python).
No se prevén altas ni bajas; solo revisión manual de enunciados y distractores.

Los scripts de regeneración/rebalanceo quedan desactivados para evitar
sobrescribir datos del juego por accidente.

Override de emergencia:
  set TFG_PERMITIR_CSV=1           → Preguntas.csv
  set TFG_PERMITIR_PLANTILLAS=1    → plantillas.json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

BANCO_CERRADO = True
FECHA_CIERRE = "2026-06-03"
TOTAL_PREGUNTAS = 480

PLANTILLAS_CERRADAS = True
FECHA_CIERRE_PLANTILLAS = "2026-06-27"
TOTAL_PLANTILLAS_JSON = 960
PLANTILLAS_DATASET_JSON = 480
PLANTILLAS_EXTRA_JSON = 480

POOL_JUEGO_CERRADO = True
FECHA_CIERRE_POOL_JUEGO = "2026-06-27"
TOTAL_POOL_JUEGO = 1000
EXCLUSIVAS_RESISTENCIA = 40

_ENV_OVERRIDE = "TFG_PERMITIR_CSV"
_ENV_OVERRIDE_PLANTILLAS = "TFG_PERMITIR_PLANTILLAS"

SCRIPTS_SOLO_LECTURA = (
    "mantenimiento.py",
    "utilidades_tfg.py",
    "utilidades_distribucion.py",
    "validacion_dataset.py",
    "auditoria.py",
    "clasificar_pregunta.py",
)

SCRIPTS_MUTAN_PLANTILLAS = (
    "reclasificar_plantillas.py",
    "duplicados.py",
)


def escritura_csv_permitida(*, force: bool = False) -> bool:
    if force or not BANCO_CERRADO:
        return True
    return os.environ.get(_ENV_OVERRIDE, "").strip() in ("1", "true", "yes", "si", "sí")


def rechazar_mutacion_dataset(origen: str, *, force: bool = False) -> None:
    """Impide escribir Preguntas.csv salvo override explícito."""
    if escritura_csv_permitida(force=force):
        return
    msg = (
        f"\n[BANCO CERRADO — {FECHA_CIERRE}] No se puede modificar el dataset.\n"
        f"  Origen: {origen}\n"
        f"  El banco tiene {TOTAL_PREGUNTAS} preguntas revisadas en Data/Preguntas.csv.\n"
        f"  Scripts seguros: mantenimiento.py validar | plantillas | auditar-*.\n"
        f"  Ver Files/README.md.\n"
        f"  Override de emergencia: {_ENV_OVERRIDE}=1\n"
    )
    print(msg, file=sys.stderr)
    raise SystemExit(2)


def escritura_plantillas_permitida(*, force: bool = False) -> bool:
    if force or not PLANTILLAS_CERRADAS:
        return True
    return os.environ.get(_ENV_OVERRIDE_PLANTILLAS, "").strip() in (
        "1",
        "true",
        "yes",
        "si",
        "sí",
    )


def rechazar_mutacion_plantillas(origen: str, *, force: bool = False) -> None:
    """Impide escribir plantillas.json salvo override explícito."""
    if escritura_plantillas_permitida(force=force):
        return
    msg = (
        f"\n[PLANTILLAS CERRADAS — {FECHA_CIERRE_PLANTILLAS}] "
        f"No se puede modificar plantillas.json.\n"
        f"  Origen: {origen}\n"
        f"  Estado: {TOTAL_PLANTILLAS_JSON} filas "
        f"({PLANTILLAS_DATASET_JSON} dataset_480 + {PLANTILLAS_EXTRA_JSON} extra), "
        f"sin variaciones.\n"
        f"  Pool modo resistencia: {TOTAL_POOL_JUEGO} preguntas "
        f"(480 CSV + 480 extras JSON + {EXCLUSIVAS_RESISTENCIA} exclusivas). "
        f"Cerrado {FECHA_CIERRE_POOL_JUEGO}; solo revisión manual.\n"
        f"  Solo lectura: mantenimiento.py auditar-plantillas | auditar-distractores.\n"
        f"  Ver Files/README.md.\n"
        f"  Override de emergencia: {_ENV_OVERRIDE_PLANTILLAS}=1\n"
    )
    print(msg, file=sys.stderr)
    raise SystemExit(2)


def guardar_plantillas_json(
    plantillas: dict,
    path: Path | None = None,
    *,
    permitir_escritura: bool = False,
) -> None:
    """Único punto de escritura de plantillas.json (respeta PLANTILLAS_CERRADAS)."""
    from rutas_data import PATH_PLANTILLAS

    dest = path or PATH_PLANTILLAS
    rechazar_mutacion_plantillas(
        f"guardar_plantillas_json → {dest.name}",
        force=permitir_escritura,
    )
    with dest.open("w", encoding="utf-8") as f:
        json.dump(plantillas, f, ensure_ascii=False, indent=2)
        f.write("\n")
