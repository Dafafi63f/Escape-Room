# -*- coding: utf-8 -*-
"""
Banco de preguntas cerrado (480 filas, revisado 2026-06-03).

Los scripts de regeneración/rebalanceo quedan desactivados para evitar
sobrescribir Data/Preguntas.csv por accidente.

Para forzar una escritura (solo mantenimiento excepcional):
  set TFG_PERMITIR_CSV=1   (Windows)
  export TFG_PERMITIR_CSV=1   (Unix)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

BANCO_CERRADO = True
FECHA_CIERRE = "2026-06-03"
TOTAL_PREGUNTAS = 480

_ENV_OVERRIDE = "TFG_PERMITIR_CSV"

SCRIPTS_SOLO_LECTURA = (
    "mantenimiento.py",
    "utilidades_tfg.py",
    "validacion_dataset.py",
    "auditoria.py",
    "clasificar_pregunta.py",
    "estadisticas_historic_qualificacions.py",
    "exportar_criterios_clasificacion_materia.py",
)

SCRIPTS_MANTENIMIENTO_PLANTILLAS = (
    "plantillas_sync.py",
    "duplicados.py",
    "equilibrar_pool_extra_juego.py",
    "dedup_reemplazar_plantillas.py",
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
