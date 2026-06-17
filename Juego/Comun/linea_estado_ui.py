#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Línea de estado de partida con iconos (texto/emoji; compartido consola y gráfico)."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from Comun.motor_nucleo import EstadoPartida
from Comun.reglas_partida import SistemaPuntuacion, nota_sobre_diez, porcentaje_aciertos

__all__ = [
    "SegmentoEstado",
    "consola_soporta_emoji",
    "formatear_linea_estado",
    "segmentos_linea_estado",
]

_SEPARADOR_TEXTO = " · "

_ASCII_POR_ID: dict[str, str] = {
    "progreso": "?",
    "vidas": "+",
    "tiempo_total": "T",
    "tiempo_preg": "t",
    "puntos": "*",
    "nota": "%",
    "aciertos": "OK",
}


@dataclass(frozen=True)
class SegmentoEstado:
    """Un bloque de la barra de estado (icono + texto)."""

    id: str
    emoji: str
    texto: str


def consola_soporta_emoji() -> bool:
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    return enc in {"utf-8", "utf8", "cp65001", "cp_utf8"}


def _progreso_visible(progreso: str) -> str:
    return progreso.replace("/inf", "/∞").replace(" inf", " ∞")


def segmentos_linea_estado(
    estado: EstadoPartida,
    progreso: str,
    *,
    segundos_pregunta_restantes: int | None = None,
    vidas_max: int | None = None,
) -> list[SegmentoEstado]:
    """Construye los chips de la barra a partir del estado de partida."""
    prog = _progreso_visible(progreso)
    emoji_prog = "🔥" if prog.lower().startswith("racha") else "📝"
    segmentos = [SegmentoEstado("progreso", emoji_prog, prog)]

    if estado.reglas.tiene_vidas():
        n = estado.vidas_restantes or 0
        tope = vidas_max if vidas_max is not None else estado.reglas.vidas
        texto_vidas = f"{n}/{tope}" if tope else str(n)
        segmentos.append(SegmentoEstado("vidas", "❤️", texto_vidas))

    rest = estado.tiempo_total_restante()
    if rest is not None:
        segmentos.append(SegmentoEstado("tiempo_total", "⏱️", f"{rest}s"))

    if segundos_pregunta_restantes is not None:
        segmentos.append(
            SegmentoEstado("tiempo_preg", "⏳", f"{segundos_pregunta_restantes}s")
        )

    sis = estado.reglas.sistema_puntuacion
    if sis == SistemaPuntuacion.ARCADE:
        segmentos.append(SegmentoEstado("puntos", "⭐", f"{estado.puntos_arcade}"))
    elif estado.respondidas > 0:
        if sis == SistemaPuntuacion.NOTA:
            segmentos.append(
                SegmentoEstado(
                    "nota",
                    "📊",
                    f"{nota_sobre_diez(estado.aciertos, estado.respondidas)}",
                )
            )
        elif sis == SistemaPuntuacion.PORCENTAJE:
            pct = porcentaje_aciertos(estado.aciertos, estado.respondidas)
            segmentos.append(SegmentoEstado("aciertos", "✅", f"{pct}%"))
    return segmentos


def _icono_segmento(seg: SegmentoEstado, *, usar_emojis: bool) -> str:
    if usar_emojis:
        return seg.emoji
    return _ASCII_POR_ID.get(seg.id, "·")


def formatear_linea_estado(
    segmentos: list[SegmentoEstado],
    *,
    usar_emojis: bool = True,
) -> str:
    """Texto de la barra: ``📝 Pregunta 1/∞ · ❤️ 3/3 · ⭐ 0``."""
    if not segmentos:
        return ""
    partes = [
        f"{_icono_segmento(s, usar_emojis=usar_emojis)} {s.texto}" for s in segmentos
    ]
    return _SEPARADOR_TEXTO.join(partes)


def linea_estado_con_iconos(
    estado: EstadoPartida,
    progreso: str,
    *,
    segundos_pregunta_restantes: int | None = None,
    usar_emojis: bool = True,
    vidas_max: int | None = None,
) -> str:
    """Atajo: segmentos + formato textual."""
    return formatear_linea_estado(
        segmentos_linea_estado(
            estado,
            progreso,
            segundos_pregunta_restantes=segundos_pregunta_restantes,
            vidas_max=vidas_max,
        ),
        usar_emojis=usar_emojis,
    )
