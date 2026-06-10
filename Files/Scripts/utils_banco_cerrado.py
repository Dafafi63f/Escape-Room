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

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent

import os
import sys
from pathlib import Path

BANCO_CERRADO = True
FECHA_CIERRE = "2026-06-03"
TOTAL_PREGUNTAS = 480

_ENV_OVERRIDE = "TFG_PERMITIR_CSV"

SCRIPTS_SOLO_LECTURA = (
    "mantenimiento.py",
    "balance.py",
    "borrar_temporales.py",
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

SCRIPTS_BLOQUEADOS = (
    "fix_final_materias.py",
    "aplicar_clasificacion_optima.py",
    "aplicar_correcciones_materia.py",
    "ampliar_dataset_480.py",
    "ampliar_plantillas.py",
    "ampliar_plantillas_desde_web.py",
    "recategorizar_y_equilibrar.py",
    "reparar_materia_algoritmes.py",
    "revisar_materia_contenido.py",
    "crear_borrar_preguntas.py",
    "reducir_dataset_objetivo.py",
    "limpiar_duplicados_csv.py",
    "variedad_materias.py",
    "dataset_plantillas_cli.py",
    "materias_cli.py",
    "sync_plantillas_materias.py",
    "revisar_castellano_csv.py",
    "aplicar_clasificacion_optima.py",
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
        f"  Ver Files/Scripts/README.md.\n"
        f"  Override de emergencia: {_ENV_OVERRIDE}=1\n"
    )
    print(msg, file=sys.stderr)
    raise SystemExit(2)


def rechazar_script_deprecado(nombre: str) -> None:
    """Al ejecutar un script de regeneración obsoleto."""
    rechazar_mutacion_dataset(f"script bloqueado: {nombre}")


def mensaje_comando_balance_bloqueado(comando: str) -> str:
    return (
        f"El comando 'balance.py {comando}' está deshabilitado (banco cerrado).\n"
        f"Usa: python Files/Scripts/mantenimiento.py validar [--detalle]\n"
        f"Mantenimiento de plantillas: ver Files/Scripts/README.md"
    )
