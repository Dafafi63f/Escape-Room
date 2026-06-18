#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preferencias de persistencia del ranking local (modo resistencia)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from Comun.rutas import _ruta_json_escritura

__all__ = [
    "ModoRetencionRanking",
    "PreferenciasRanking",
    "cargar_preferencias",
    "guardar_preferencias",
    "ciclar_modo",
    "etiqueta_modo",
    "resolver_path_preferencias_ranking",
]

_ORDEN_MODOS = (
    "permanente",
    "sesion",
    "7_dias",
    "30_dias",
)


class ModoRetencionRanking(str, Enum):
    PERMANENTE = "permanente"
    SESION = "sesion"
    DIAS_7 = "7_dias"
    DIAS_30 = "30_dias"


@dataclass
class PreferenciasRanking:
    modo: ModoRetencionRanking = ModoRetencionRanking.PERMANENTE


_ETIQUETAS: dict[ModoRetencionRanking, str] = {
    ModoRetencionRanking.PERMANENTE: "Siempre (solo este equipo)",
    ModoRetencionRanking.SESION: "Solo hasta cerrar el juego",
    ModoRetencionRanking.DIAS_7: "7 días en este equipo",
    ModoRetencionRanking.DIAS_30: "30 días en este equipo",
}


def resolver_path_preferencias_ranking() -> Path:
    return _ruta_json_escritura("preferencias_ranking.json")


def etiqueta_modo(modo: ModoRetencionRanking) -> str:
    return _ETIQUETAS.get(modo, _ETIQUETAS[ModoRetencionRanking.PERMANENTE])


def ciclar_modo(modo: ModoRetencionRanking, delta: int) -> ModoRetencionRanking:
    orden = [ModoRetencionRanking(v) for v in _ORDEN_MODOS]
    try:
        idx = orden.index(modo)
    except ValueError:
        idx = 0
    return orden[(idx + delta) % len(orden)]


def cargar_preferencias() -> PreferenciasRanking:
    path = resolver_path_preferencias_ranking()
    if not path.is_file():
        return PreferenciasRanking()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return PreferenciasRanking()
    raw = str(data.get("modo", ModoRetencionRanking.PERMANENTE.value))
    try:
        modo = ModoRetencionRanking(raw)
    except ValueError:
        modo = ModoRetencionRanking.PERMANENTE
    return PreferenciasRanking(modo=modo)


def guardar_preferencias(prefs: PreferenciasRanking) -> None:
    path = resolver_path_preferencias_ranking()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "modo": prefs.modo.value}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
