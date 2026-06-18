#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modos con semilla diaria (examen del día, reto del día)."""

from __future__ import annotations

from Comun.examen_dia_historia import ID_PRESET_EXAMEN_DIA, es_id_examen_dia
from Comun.reto_dia_resistencia import ID_PRESET_RETO_DIA, es_id_reto_dia

__all__ = [
    "ID_PRESET_EXAMEN_DIA",
    "ID_PRESET_RETO_DIA",
    "es_preset_diario",
    "prioridad_orden_preset",
]

_IDS_DIARIOS = frozenset({ID_PRESET_EXAMEN_DIA, ID_PRESET_RETO_DIA})


def es_preset_diario(preset_id: str) -> bool:
    return preset_id in _IDS_DIARIOS or es_id_examen_dia(preset_id) or es_id_reto_dia(preset_id)


def prioridad_orden_preset(preset_id: str) -> int:
    """0 = aparece antes en catálogos (modos diarios)."""
    return 0 if es_preset_diario(preset_id) else 1
