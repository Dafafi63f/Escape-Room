#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Semilla diaria del examen balanceado (4×6): misma para todos en un día civil UTC."""

from __future__ import annotations

from datetime import date

from Comun.examen_balanceado import (
    MATERIAS_EXAMEN_BALANCEADO,
    PREGUNTAS_EXAMEN_BALANCEADO,
    PREGUNTAS_POR_MATERIA_BALANCEADO,
)
from Comun.reto_dia_resistencia import etiqueta_fecha_reto_dia

__all__ = [
    "MATERIAS_EXAMEN_DIA",
    "PREGUNTAS_EXAMEN_DIA",
    "PREGUNTAS_POR_MATERIA_DIA",
    "etiqueta_fecha_examen_dia",
    "semilla_examen_dia",
]

MATERIAS_EXAMEN_DIA = MATERIAS_EXAMEN_BALANCEADO
PREGUNTAS_POR_MATERIA_DIA = PREGUNTAS_POR_MATERIA_BALANCEADO
PREGUNTAS_EXAMEN_DIA = PREGUNTAS_EXAMEN_BALANCEADO


def semilla_examen_dia(d: date | None = None) -> int:
    """Entero estable por día civil (UTC); mismo criterio que el reto del día."""
    from Comun.modos_diarios import semilla_diaria

    return semilla_diaria(d)


def etiqueta_fecha_examen_dia(d: date | None = None) -> str:
    return etiqueta_fecha_reto_dia(d)
