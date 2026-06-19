#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Línea de estado de partida con iconos (texto/emoji; UI gráfica)."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from Comun.motor_nucleo import EstadoPartida
from Comun.reglas_partida import SistemaPuntuacion, nota_sobre_diez, porcentaje_aciertos

__all__ = [
    "EMOJI_TIEMPO_PREG",
    "EMOJI_TIEMPO_TOTAL",
    "SegmentoEstado",
    "ascii_icono_segmento",
    "stdout_soporta_emoji",
    "emoji_candidatos_segmento",
    "formatear_linea_estado",
    "segmentos_linea_estado",
]

_SEPARADOR_TEXTO = " · "

# Iconos de la barra: tiempo activo de partida vs temporizador por pregunta.
EMOJI_TIEMPO_TOTAL = "⏰"
EMOJI_TIEMPO_PREG = "⏱️"
_ASCII_TIEMPO_TOTAL = "T·"
_ASCII_TIEMPO_PREG = "P·"

_EMOJI_ALTERNATIVOS: dict[str, tuple[str, ...]] = {
    "progreso": ("📝", "📋"),
    "racha": ("🔥", "💥"),
    "vidas": ("❤️", "❤", "🧡"),
    "tiempo_total": ("⏰", "⏳", "⌚", "🕐", "🕑"),
    "tiempo_preg": ("⏱️", "⏱", "⏳", "⌛", "⏰"),
    "puntos": ("⭐", "★", "🌟"),
    "nota": ("📊", "📈"),
    "aciertos": ("✅", "✔️"),
}

_ASCII_POR_ID: dict[str, str] = {
    "progreso": "?",
    "racha": "R·",
    "vidas": "+",
    "tiempo_total": _ASCII_TIEMPO_TOTAL,
    "tiempo_preg": _ASCII_TIEMPO_PREG,
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


def stdout_soporta_emoji() -> bool:
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    return enc in {"utf-8", "utf8", "cp65001", "cp_utf8"}


def _progreso_visible(progreso: str) -> str:
    return progreso.replace("/inf", "/∞").replace(" inf", " ∞")


def _segmento_tiempo_activo(estado: EstadoPartida) -> SegmentoEstado:
    """Tiempo activo de partida: cuenta atrás global o transcurrido (independiente del temporizador)."""
    rest = estado.tiempo_total_restante()
    if rest is not None:
        return SegmentoEstado("tiempo_total", EMOJI_TIEMPO_TOTAL, f"{rest}s")
    transcurrido = estado.tiempo_transcurrido_seg()
    return SegmentoEstado("tiempo_total", EMOJI_TIEMPO_TOTAL, f"{transcurrido}s")


def _segmento_temporizador_pregunta(segundos_restantes: int) -> SegmentoEstado:
    return SegmentoEstado(
        "tiempo_preg",
        EMOJI_TIEMPO_PREG,
        f"{segundos_restantes}s",
    )


def _segmentos_progreso_resistencia(
    numero_pregunta: int,
    racha: int,
) -> list[SegmentoEstado]:
    return [
        SegmentoEstado("progreso", "📝", f"#{numero_pregunta}"),
        SegmentoEstado("racha", "🔥", str(racha)),
    ]


def segmentos_linea_estado(
    estado: EstadoPartida,
    progreso: str,
    *,
    segundos_pregunta_restantes: int | None = None,
    vidas_max: int | None = None,
    numero_pregunta: int | None = None,
    racha: int | None = None,
) -> list[SegmentoEstado]:
    """Construye los chips de la barra; cada bloque depende solo de sus reglas.

    Orden fijo: pregunta → racha → vidas → tiempo activo (⏰) → temporizador (⏱️) → puntuación.
    En resistencia, pregunta y racha van en chips separados.
    """
    if numero_pregunta is not None and racha is not None:
        segmentos = _segmentos_progreso_resistencia(numero_pregunta, racha)
    else:
        prog = _progreso_visible(progreso)
        emoji_prog = (
            "🔥"
            if prog.lower().startswith("racha") or "racha" in prog.lower()
            else "📝"
        )
        segmentos = [SegmentoEstado("progreso", emoji_prog, prog)]

    if estado.reglas.tiene_vidas():
        n = estado.vidas_restantes or 0
        tope = vidas_max if vidas_max is not None else estado.reglas.vidas
        texto_vidas = f"{n}/{tope}" if tope else str(n)
        segmentos.append(SegmentoEstado("vidas", "❤️", texto_vidas))

    segmentos.append(_segmento_tiempo_activo(estado))

    if segundos_pregunta_restantes is not None:
        segmentos.append(_segmento_temporizador_pregunta(segundos_pregunta_restantes))

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


def ascii_icono_segmento(seg_id: str) -> str:
    """Sustituto textual del icono (emojis desactivados o terminal sin Unicode)."""
    return _ASCII_POR_ID.get(seg_id, "·")


def emoji_candidatos_segmento(seg: SegmentoEstado) -> tuple[str, ...]:
    """Glifos a probar en orden (el preferido del segmento primero)."""
    alternativas = _EMOJI_ALTERNATIVOS.get(seg.id, ())
    vistos: list[str] = []
    for glyph in (seg.emoji, *alternativas):
        if glyph and glyph not in vistos:
            vistos.append(glyph)
    return tuple(vistos)


def _icono_segmento(seg: SegmentoEstado, *, usar_emojis: bool) -> str:
    if usar_emojis:
        return seg.emoji
    return ascii_icono_segmento(seg.id)


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
    numero_pregunta: int | None = None,
    racha: int | None = None,
) -> str:
    """Atajo: segmentos + formato textual."""
    return formatear_linea_estado(
        segmentos_linea_estado(
            estado,
            progreso,
            segundos_pregunta_restantes=segundos_pregunta_restantes,
            vidas_max=vidas_max,
            numero_pregunta=numero_pregunta,
            racha=racha,
        ),
        usar_emojis=usar_emojis,
    )
