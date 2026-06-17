#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Feedback tras responder: espera automática y dibujo (sin botón Continuar)."""

from __future__ import annotations

import time

import pygame

from Grafico.tema import ANCHO, COLOR_AVISO, COLOR_ERROR, COLOR_OK, MARGEN
from Grafico.textos_grafico import mensaje_feedback
from Grafico.texto import dibujar_texto_centro, medir_texto_mixto
from Grafico.ui import dibujar_texto_multilinea

SEGUNDOS_FEEDBACK_ACIERTO = 1.6
SEGUNDOS_FEEDBACK_FALLO = 2.2
SEGUNDOS_FEEDBACK_CON_SOLUCION = 3.2


def solucion_feedback_grafico(_solucion: str | None) -> str | None:
    """En gráfico las opciones A–D ya se colorean; no repetir la solución en texto."""
    return None


def marcar_inicio_feedback() -> float:
    return time.monotonic()


def segundos_espera_feedback(*, solucion: str | None, acierto: bool) -> float:
    if solucion:
        return SEGUNDOS_FEEDBACK_CON_SOLUCION
    return SEGUNDOS_FEEDBACK_ACIERTO if acierto else SEGUNDOS_FEEDBACK_FALLO


def feedback_debe_avanzar(
    inicio_feedback: float,
    *,
    solucion: str | None,
    acierto: bool,
) -> bool:
    return (time.monotonic() - inicio_feedback) >= segundos_espera_feedback(
        solucion=solucion, acierto=acierto
    )


def dibujar_feedback_partida(
    superficie: pygame.Surface,
    fuentes: dict[str, pygame.font.Font],
    *,
    mensaje: str,
    solucion: str | None,
    acierto: bool,
    y_mensaje: int,
) -> None:
    """Muestra el mensaje de acierto/fallo sin botón de continuar."""
    color_fb = COLOR_OK if acierto else COLOR_ERROR
    texto_fb = mensaje_feedback(mensaje)
    tam = fuentes["subtitulo"].get_height()
    _, alto_msg = medir_texto_mixto(texto_fb, tam, bold=True, color_texto=color_fb)
    dibujar_texto_centro(
        superficie,
        texto_fb,
        (ANCHO // 2, y_mensaje + alto_msg // 2),
        tam,
        color_fb,
        bold=True,
    )
    if solucion:
        dibujar_texto_multilinea(
            superficie,
            fuentes["pequena"],
            solucion,
            pygame.Rect(
                MARGEN + 8,
                y_mensaje + alto_msg + 8,
                ANCHO - 2 * MARGEN - 16,
                120,
            ),
            COLOR_AVISO,
            alineacion_centro=True,
        )
