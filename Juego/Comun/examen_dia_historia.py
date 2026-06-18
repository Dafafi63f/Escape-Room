#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Examen del día (historia): mismo plan de examen para todos en una fecha."""

from __future__ import annotations

from datetime import date

from Comun.reto_dia_resistencia import etiqueta_fecha_reto_dia, semilla_reto_dia

__all__ = [
    "ID_PRESET_EXAMEN_DIA",
    "es_id_examen_dia",
    "etiqueta_fecha_examen_dia",
    "semilla_examen_dia",
]

ID_PRESET_EXAMEN_DIA = "examen_dia_historia"


def es_id_examen_dia(preset_id: str) -> bool:
    return preset_id == ID_PRESET_EXAMEN_DIA


def semilla_examen_dia(d: date | None = None) -> int:
    """Entero estable por día civil (UTC); desplazado respecto al reto de resistencia."""
    return semilla_reto_dia(d) + 480_000


def etiqueta_fecha_examen_dia(d: date | None = None) -> str:
    return etiqueta_fecha_reto_dia(d)
