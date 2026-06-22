#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modos con semilla diaria (examen del día, reto del día)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from Comun.reto_dia_resistencia import ID_PRESET_RETO_DIA, es_id_reto_dia

__all__ = [
    "ID_PRESET_RETO_DIA",
    "es_preset_diario",
    "formatear_semilla_diaria",
    "prioridad_orden_preset",
    "semilla_diaria",
]


def semilla_diaria(d: date | None = None) -> int:
    """Entero estable por día civil (UTC), formato DDMMYYYY (p. ej. 22062026)."""
    d = d or datetime.now(timezone.utc).date()
    return int(d.strftime("%d%m%Y"))


def formatear_semilla_diaria(semilla: int) -> str:
    """Representación de 8 dígitos con ceros a la izquierda (p. ej. 1012026 → 01012026)."""
    return f"{semilla:08d}"


def es_preset_diario(preset_id: str) -> bool:
    return es_id_reto_dia(preset_id)


def prioridad_orden_preset(preset_id: str) -> int:
    """0 = aparece antes en catálogos (modos diarios)."""
    return 0 if es_preset_diario(preset_id) else 1
