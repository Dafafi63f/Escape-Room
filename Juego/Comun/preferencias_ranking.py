#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Política interna de retención del ranking (sin fichero ni UI).

Las preferencias visibles del jugador están solo en ``preferencias_grafico.json``
(menú de opciones). Este módulo conserva la lógica de retención para el motor
de rankings y para tests; por defecto el historial es permanente en el equipo.
"""

from __future__ import annotations

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
]

_ORDEN_MODOS = (
    "permanente",
    "sesion",
    "7_dias",
    "30_dias",
)

_modo_actual: ModoRetencionRanking


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

_modo_actual = ModoRetencionRanking.PERMANENTE
_legado_eliminado = False


def _eliminar_legado_si_existe() -> None:
    global _legado_eliminado
    if _legado_eliminado:
        return
    _legado_eliminado = True
    legado = _ruta_json_escritura("preferencias_ranking.json")
    if legado.is_file():
        legado.unlink(missing_ok=True)


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
    _eliminar_legado_si_existe()
    return PreferenciasRanking(modo=_modo_actual)


def guardar_preferencias(prefs: PreferenciasRanking) -> None:
    global _modo_actual
    _modo_actual = prefs.modo
