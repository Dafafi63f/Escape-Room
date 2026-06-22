#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reto del día: misma secuencia pseudoaleatoria para todos en una fecha."""

from __future__ import annotations

from datetime import date, datetime, timezone

__all__ = [
    "ID_PRESET_RETO_DIA",
    "es_id_reto_dia",
    "etiqueta_fecha_reto_dia",
    "semilla_reto_dia",
]

ID_PRESET_RETO_DIA = "reto_dia_resistencia"


def es_id_reto_dia(preset_id: str) -> bool:
    return preset_id == ID_PRESET_RETO_DIA


def semilla_reto_dia(d: date | None = None) -> int:
    """Entero estable por día civil (UTC); mismo criterio que el examen del día."""
    from Comun.modos_diarios import semilla_diaria

    return semilla_diaria(d)


def etiqueta_fecha_reto_dia(d: date | None = None) -> str:
    d = d or datetime.now(timezone.utc).date()
    return d.strftime("%d/%m/%Y")
