#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Barra superior de partida: chips con emoji o iconos dibujados (pygame)."""

from __future__ import annotations

import math

import pygame

from Comun.linea_estado_ui import (
    SegmentoEstado,
    formatear_linea_estado,
    segmentos_linea_estado,
)
from Comun.motor_nucleo import EstadoPartida
from Grafico.fuentes import fuente_disponible
from Grafico.tema import COLOR_TEXTO

_GAP_EMOJI_TEXTO = 4
_GAP_ENTRE_CHIPS = 14
_TAM_ICONO = 16
_SEPARADOR = "·"

_EMOJI_OK: bool | None = None

__all__ = [
    "SegmentoEstado",
    "dibujar_estado_partida_en_barra",
    "dibujar_linea_estado_con_iconos",
    "formatear_linea_estado",
    "segmentos_linea_estado",
]


def _emoji_renderizable(fuente_emoji: pygame.font.Font) -> bool:
    global _EMOJI_OK
    if _EMOJI_OK is not None:
        return _EMOJI_OK
    if not fuente_disponible("emoji"):
        _EMOJI_OK = False
        return False
    try:
        surf = fuente_emoji.render("❤", True, (255, 255, 255))
        _EMOJI_OK = surf.get_width() > 4
    except Exception:
        _EMOJI_OK = False
    return _EMOJI_OK


def _dibujar_icono_fallback(superficie: pygame.Surface, seg_id: str, rect: pygame.Rect) -> None:
    """Iconos vectoriales si la fuente emoji no está disponible."""
    cx, cy = rect.center
    color = COLOR_TEXTO
    if seg_id == "progreso":
        r = pygame.Rect(cx - 6, cy - 7, 12, 14)
        pygame.draw.rect(superficie, color, r, width=1, border_radius=1)
        for dy in (cy - 3, cy, cy + 3):
            pygame.draw.line(superficie, color, (cx - 4, dy), (cx + 4, dy), 1)
    elif seg_id == "vidas":
        pygame.draw.circle(superficie, color, (cx - 3, cy - 1), 4, 1)
        pygame.draw.circle(superficie, color, (cx + 3, cy - 1), 4, 1)
        pygame.draw.polygon(
            superficie,
            color,
            [(cx - 7, cy - 1), (cx, cy + 6), (cx + 7, cy - 1)],
            width=1,
        )
    elif seg_id in {"puntos", "nota"}:
        puntos: list[tuple[int, int]] = []
        for i in range(5):
            ang = math.radians(-90 + i * 72)
            rad = 7 if i % 2 == 0 else 3
            puntos.append((int(cx + rad * math.cos(ang)), int(cy + rad * math.sin(ang))))
        pygame.draw.polygon(superficie, color, puntos, width=1)
    elif seg_id in {"tiempo_total", "tiempo_preg"}:
        pygame.draw.circle(superficie, color, (cx, cy), 7, 1)
        pygame.draw.line(superficie, color, (cx, cy), (cx, cy - 4), 1)
        pygame.draw.line(superficie, color, (cx, cy), (cx + 4, cy), 1)
    elif seg_id == "aciertos":
        pygame.draw.line(superficie, color, (cx - 5, cy), (cx - 1, cy + 4), 2)
        pygame.draw.line(superficie, color, (cx - 1, cy + 4), (cx + 6, cy - 4), 2)
    else:
        pygame.draw.circle(superficie, color, (cx, cy), 5, 1)


def _ancho_chip(
    seg: SegmentoEstado,
    fuente_txt: pygame.font.Font,
    fuente_emoji: pygame.font.Font,
    usar_emoji: bool,
) -> int:
    tw = fuente_txt.size(seg.texto)[0]
    iw = fuente_emoji.size(seg.emoji)[0] if usar_emoji else _TAM_ICONO
    return iw + _GAP_EMOJI_TEXTO + tw


def _escala_fuentes(
    segmentos: list[SegmentoEstado],
    fuente_txt: pygame.font.Font,
    fuente_emoji: pygame.font.Font,
    usar_emoji: bool,
    ancho_max: int,
) -> tuple[pygame.font.Font, pygame.font.Font]:
    if not segmentos:
        return fuente_txt, fuente_emoji
    separadores = max(0, len(segmentos) - 1)
    sep_w = fuente_txt.size(_SEPARADOR)[0]
    ancho = sum(_ancho_chip(s, fuente_txt, fuente_emoji, usar_emoji) for s in segmentos)
    ancho += separadores * (_GAP_ENTRE_CHIPS + sep_w)
    if ancho <= ancho_max:
        return fuente_txt, fuente_emoji
    factor = max(0.65, ancho_max / ancho)
    tam_txt = max(12, int(fuente_txt.get_height() * factor))
    tam_emo = max(14, int(fuente_emoji.get_height() * factor))
    from Grafico.fuentes import crear_fuente

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
) -> None:
    """Dibuja los chips centrados en ``x_centro``."""
    if not segmentos:
        return

    usar_emoji = _emoji_renderizable(fuente_emoji)
    fuente_txt, fuente_emoji = _escala_fuentes(
        segmentos, fuente_txt, fuente_emoji, usar_emoji, ancho_max
    )

    sep_surf = fuente_txt.render(_SEPARADOR, True, (120, 140, 170))
    sep_w = sep_surf.get_width()
    ancho_total = sum(_ancho_chip(s, fuente_txt, fuente_emoji, usar_emoji) for s in segmentos)
    ancho_total += max(0, len(segmentos) - 1) * (_GAP_ENTRE_CHIPS + sep_w)
    x = x_centro - ancho_total // 2

    for i, seg in enumerate(segmentos):
        if i > 0:
            x += _GAP_ENTRE_CHIPS // 2
            superficie.blit(sep_surf, (x, y + 2))
            x += sep_w + _GAP_ENTRE_CHIPS // 2

        if usar_emoji:
            emoji_surf = fuente_emoji.render(seg.emoji, True, color_texto)
            ey = y + max(0, (fuente_txt.get_height() - emoji_surf.get_height()) // 2)
            superficie.blit(emoji_surf, (x, ey))
            x += emoji_surf.get_width() + _GAP_EMOJI_TEXTO
        else:
            icon_rect = pygame.Rect(x, y + 1, _TAM_ICONO, _TAM_ICONO)
            _dibujar_icono_fallback(superficie, seg.id, icon_rect)
            x += _TAM_ICONO + _GAP_EMOJI_TEXTO

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
    y: int = 18,
    segundos_pregunta_restantes: int | None = None,
    vidas_max: int | None = None,
) -> None:
    """Atajo: segmentos + dibujo centrado en la zona disponible."""
    ancho_centro = max(80, x_centro_max - x_centro_min)
    x_centro = x_centro_min + ancho_centro // 2
    segmentos = segmentos_linea_estado(
        estado,
        progreso,
        segundos_pregunta_restantes=segundos_pregunta_restantes,
        vidas_max=vidas_max,
    )
    dibujar_linea_estado_con_iconos(
        superficie,
        segmentos,
        fuente_txt=fuentes["pequena"],
        fuente_emoji=fuentes.get("icono_emoji") or fuentes["pequena"],
        x_centro=x_centro,
        y=y,
        ancho_max=ancho_centro,
    )
