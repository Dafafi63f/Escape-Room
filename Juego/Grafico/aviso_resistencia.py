#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Avisos emergentes del modo resistencia antes de cada pregunta."""

from __future__ import annotations

import time

import pygame

from Comun.iconos_resistencia import separar_emoji_mensaje
from Grafico.fuentes import crear_fuente
from Grafico.tema import ALTO, ANCHO, COLOR_ACENTO, COLOR_AVISO, COLOR_FONDO, COLOR_TITULO, MARGEN
from Grafico.texto import dibujar_texto_centro, preparar_texto_ui
from Grafico.ui import dibujar_panel, dibujar_texto_multilinea

SEGUNDOS_AVISO_RESISTENCIA = 2.4


def marcar_inicio_aviso() -> float:
    return time.monotonic()


def aviso_debe_avanzar(inicio_aviso: float) -> bool:
    return (time.monotonic() - inicio_aviso) >= SEGUNDOS_AVISO_RESISTENCIA


def dibujar_contenido_aviso_resistencia(
    superficie: pygame.Surface,
    fuentes: dict[str, pygame.font.Font],
    *,
    mensaje: str,
    indice: int = 0,
    total: int = 1,
) -> None:
    """Panel del aviso de resistencia (sin velo; lo aplica la app)."""
    panel = pygame.Rect(ANCHO // 2 - 280, ALTO // 2 - 108, 560, 216)
    dibujar_panel(superficie, panel)

    titulo = "Evento" if total == 1 else f"Evento ({indice + 1}/{total})"
    dibujar_texto_centro(
        superficie,
        titulo,
        (ANCHO // 2, panel.y + 24),
        fuentes["subtitulo"].get_height(),
        COLOR_ACENTO,
        bold=True,
    )

    emoji, texto = separar_emoji_mensaje(mensaje)
    y_contenido = panel.y + 52
    if emoji:
        fuente_emoji = crear_fuente(44, familia="emoji")
        icono = fuente_emoji.render(emoji, True, COLOR_TITULO)
        superficie.blit(icono, icono.get_rect(midtop=(ANCHO // 2, y_contenido)))
        y_contenido += icono.get_height() + 6

    texto = preparar_texto_ui(texto)
    dibujar_texto_multilinea(
        superficie,
        fuentes["cuerpo"],
        texto,
        pygame.Rect(panel.x + 20, y_contenido, panel.width - 40, panel.bottom - y_contenido - 36),
        COLOR_TITULO,
        alineacion_centro=True,
    )

    pie = fuentes["pequena"].render(
        preparar_texto_ui("La pregunta empezará en un momento…"),
        True,
        COLOR_AVISO,
    )
    superficie.blit(pie, pie.get_rect(midbottom=(ANCHO // 2, panel.bottom - 14)))


def dibujar_aviso_resistencia(
    superficie: pygame.Surface,
    fuentes: dict[str, pygame.font.Font],
    *,
    mensaje: str,
    indice: int = 0,
    total: int = 1,
) -> None:
    """Popup completo con velo (p. ej. tests o uso fuera de la app)."""
    overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    overlay.fill((8, 12, 22, 200))
    superficie.blit(overlay, (0, 0))
    dibujar_contenido_aviso_resistencia(
        superficie,
        fuentes,
        mensaje=mensaje,
        indice=indice,
        total=total,
    )
