#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cierre de actividad con informe .txt (una actividad terminada = un archivo).

Aplica a modo libre (finito/infinito), historia, arcade, examen cerrado, etc.
Cada vez que el jugador termina o abandona con respuestas registradas se prepara
un ``CierreInformePartida`` independiente; al guardar se genera un .txt con id único.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Comun.informe_examen import RegistroRespuesta


@dataclass
class CierreInformePartida:
    """Datos para un informe .txt al cerrar una actividad concreta."""

    registros: list
    titulo: str
    total_previsto: int
    prefijo: str
    meta: dict | None = None
    stats_historicas: dict | None = None
    abandonado: bool = False


def meta_cierre_libre(
    *,
    banco: str,
    filtro: str,
    infinito: bool,
    n_preguntas: int,
) -> dict:
    tipo = "libre_infinito" if infinito else "libre_finito"
    etiqueta = (
        "Partida modo libre (infinito — sesión terminada)"
        if infinito
        else "Partida modo libre (bloque finito)"
    )
    return {
        "etiqueta_sesion": etiqueta,
        "modo": "libre",
        "tipo_actividad": tipo,
        "banco": banco,
        "filtro": filtro,
        "n_preguntas": n_preguntas,
    }


def meta_cierre_historia(
    *,
    preset_id: str,
    preset_nombre: str,
    perfil: str,
    materias: list[str],
    n_preguntas: int,
    modo_resistencia: bool = False,
    racha: int | None = None,
) -> dict:
    meta = {
        "etiqueta_sesion": f"Historia — {preset_nombre}",
        "modo": "historia",
        "tipo_actividad": "resistencia" if modo_resistencia else "historia",
        "preset": preset_id,
        "perfil": perfil,
        "materias": ", ".join(materias),
        "banco": "dataset revisado (modo seguro)",
        "n_preguntas": n_preguntas,
    }
    if modo_resistencia and racha is not None:
        meta["racha"] = racha
    return meta
