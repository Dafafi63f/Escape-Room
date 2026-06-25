#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Barra superior de partida: chips con emoji (o texto ASCII si están desactivados)."""

from __future__ import annotations

import pygame

from Comun.linea_estado_ui import (
    SegmentoEstado,
    ascii_icono_segmento,
    emoji_candidatos_segmento,
    formatear_linea_estado,
    segmentos_linea_estado,
)
from Comun.motor_nucleo import EstadoPartida
from Comun.preferencias_grafico import emojis_habilitados
from Grafico.fuentes import crear_fuente, fuente_disponible, render_icono_barra
from Grafico.tema import COLOR_TEXTO, Y_ICONOS_FIJOS, alto_icono_fijo

_GAP_EMOJI_TEXTO = 4
_GAP_ENTRE_CHIPS = 10
_SEPARADOR = "·"

__all__ = [
    "SegmentoEstado",
    "dibujar_estado_partida_en_barra",
    "dibujar_linea_estado_con_iconos",
    "formatear_linea_estado",
    "segmentos_linea_estado",
]


def _emojis_activos() -> bool:
    return emojis_habilitados() and fuente_disponible("emoji")


def _superficie_icono(
    seg: SegmentoEstado,
    fuente_txt: pygame.font.Font,
    fuente_emoji: pygame.font.Font,
    color: tuple[int, int, int],
    *,
    emojis_activos: bool,
) -> pygame.Surface:
    return render_icono_barra(
        fuente_emoji,
        fuente_txt,
        emoji_candidatos_segmento(seg),
        ascii_icono_segmento(seg.id),
        color,
        usar_emoji=emojis_activos,
    )


def _ancho_chip(
    seg: SegmentoEstado,
    fuente_txt: pygame.font.Font,
    fuente_emoji: pygame.font.Font,
    *,
    emojis_activos: bool,
) -> int:
    tw = fuente_txt.size(seg.texto)[0]
    icono = _superficie_icono(
        seg, fuente_txt, fuente_emoji, COLOR_TEXTO, emojis_activos=emojis_activos
    )
    return icono.get_width() + _GAP_EMOJI_TEXTO + tw


def _escala_fuentes(
    segmentos: list[SegmentoEstado],
    fuente_txt: pygame.font.Font,
    fuente_emoji: pygame.font.Font,
    *,
    emojis_activos: bool,
    ancho_max: int,
) -> tuple[pygame.font.Font, pygame.font.Font]:
    if not segmentos:
        return fuente_txt, fuente_emoji
    separadores = max(0, len(segmentos) - 1)
    sep_w = fuente_txt.size(_SEPARADOR)[0]
    ancho = sum(
        _ancho_chip(s, fuente_txt, fuente_emoji, emojis_activos=emojis_activos)
        for s in segmentos
    )
    ancho += separadores * (_GAP_ENTRE_CHIPS + sep_w)
    if ancho <= ancho_max:
        return fuente_txt, fuente_emoji
    factor = max(0.65, ancho_max / ancho)
    tam_txt = max(12, int(fuente_txt.get_height() * factor))
    tam_emo = max(14, int(fuente_emoji.get_height() * factor))
    return (
        crear_fuente(tam_txt, familia="texto"),
        crear_fuente(tam_emo, familia="emoji"),
    )


def dibujar_linea_estado_con_iconos(
    superficie: pygame.Surface,
    segmentos: list[SegmentoEstado],
    *,
    fuente_txt: pygame.font.Font,
    fuente_emoji: pygame.font.Font,
    x_centro: int,
    y: int,
    ancho_max: int,
    color_texto: tuple[int, int, int] = COLOR_TEXTO,
    x_min: int | None = None,
    x_max: int | None = None,
) -> None:
    """Dibuja los chips centrados en ``x_centro``."""
    if not segmentos:
        return

    emojis_activos = _emojis_activos()
    fuente_txt, fuente_emoji = _escala_fuentes(
        segmentos,
        fuente_txt,
        fuente_emoji,
        emojis_activos=emojis_activos,
        ancho_max=ancho_max,
    )

    sep_surf = fuente_txt.render(_SEPARADOR, True, (120, 140, 170))
    sep_w = sep_surf.get_width()
    ancho_total = sum(
        _ancho_chip(s, fuente_txt, fuente_emoji, emojis_activos=emojis_activos)
        for s in segmentos
    )
    ancho_total += max(0, len(segmentos) - 1) * (_GAP_ENTRE_CHIPS + sep_w)
    x = x_centro - ancho_total // 2
    if x_min is not None:
        x = max(x, x_min)
    if x_max is not None:
        x = min(x, x_max - ancho_total)

    for i, seg in enumerate(segmentos):
        if i > 0:
            x += _GAP_ENTRE_CHIPS // 2
            superficie.blit(sep_surf, (x, y + 2))
            x += sep_w + _GAP_ENTRE_CHIPS // 2

        icono_surf = _superficie_icono(
            seg, fuente_txt, fuente_emoji, color_texto, emojis_activos=emojis_activos
        )
        ey = y + max(0, (fuente_txt.get_height() - icono_surf.get_height()) // 2)
        superficie.blit(icono_surf, (x, ey))
        x += icono_surf.get_width() + _GAP_EMOJI_TEXTO

        txt_surf = fuente_txt.render(seg.texto, True, color_texto)
        superficie.blit(txt_surf, (x, y))
        x += txt_surf.get_width()


def dibujar_estado_partida_en_barra(
    superficie: pygame.Surface,
    *,
    estado: EstadoPartida,
    progreso: str,
    fuentes: dict[str, pygame.font.Font],
    x_centro_min: int,
    x_centro_max: int,
    y: int | None = None,
    segundos_pregunta_restantes: int | None = None,
    vidas_max: int | None = None,
    numero_pregunta: int | None = None,
    racha: int | None = None,
    progreso_puerta: str | None = None,
    progreso_sala: str | None = None,
    mostrar_tiempo_activo: bool = True,
) -> None:
    """Atajo: segmentos + dibujo centrado en la zona disponible."""
    if y is None:
        y = Y_ICONOS_FIJOS + max(0, (alto_icono_fijo(fuentes["menu"]) - fuentes["pequena"].get_height()) // 2)
    ancho_centro = max(80, x_centro_max - x_centro_min)
    x_centro = x_centro_min + ancho_centro // 2
    segmentos = segmentos_linea_estado(
        estado,
        progreso,
        segundos_pregunta_restantes=segundos_pregunta_restantes,
        vidas_max=vidas_max,
        numero_pregunta=numero_pregunta,
        racha=racha,
        progreso_puerta=progreso_puerta,
        progreso_sala=progreso_sala,
        mostrar_tiempo_activo=mostrar_tiempo_activo,
    )
    fuente_emoji = fuentes.get("icono_emoji")
    if fuente_emoji is None:
        fuente_emoji = crear_fuente(fuentes["pequena"].get_height(), familia="emoji")
    dibujar_linea_estado_con_iconos(
        superficie,
        segmentos,
        fuente_txt=fuentes["pequena"],
        fuente_emoji=fuente_emoji,
        x_centro=x_centro,
        y=y,
        ancho_max=ancho_centro,
        x_min=x_centro_min,
        x_max=x_centro_max,
    )
