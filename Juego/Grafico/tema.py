#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Constantes visuales compartidas por la interfaz pygame."""

from __future__ import annotations

import pygame

from Grafico.fuentes import crear_fuente


ANCHO = 960
ALTO = 720
FPS = 60
TITULO_VENTANA = "Cuestionario MATCAD"
MARGEN = 40

# Velo semitransparente de popups globales (pausa, opciones).
ALPHA_OVERLAY_POPUP = 170

# Barra fija superior (pausa, diarios, ranking/info, feedback, opciones).
X_ICONOS_FIJOS = 16
Y_ICONOS_FIJOS = 14
GAP_ICONOS_FIJOS = 10
NUM_ICONOS_FIJOS = 5
ANCHO_MIN_ICONO_FIJO = 40
ALTO_MIN_ICONO_FIJO = 30
PADDING_ICONO_FIJO_X = 10
PADDING_ICONO_FIJO_Y = 6
_GAP_TRAS_ICONOS_FIJOS = 20
_MARGEN_EXTRA_BARRA_PARTIDA = 8
_ETIQUETAS_REF_ICONO_FIJO = ("II", "DI", "IN", "FB", "OP")

# Contenido de pantalla: debajo de la barra fija (iconos en y≈14, alto≈36).
_GAP_TRAS_BARRA_ICONOS = 34
Y_INICIO_TITULO = Y_ICONOS_FIJOS + ALTO_MIN_ICONO_FIJO + _GAP_TRAS_BARRA_ICONOS

# Panel modal global (opciones / pausa): no solapar iconos fijos ni pie de pantalla.
_GAP_PANEL_DEBAJO_ICONOS = 16
_MARGEN_PANEL_SOBRE_PIE = 84


def zona_segura_panel_modal(
    fuente_menu: pygame.font.Font | None = None,
) -> tuple[int, int]:
    """``(y_superior, y_inferior)`` del área blanca de opciones/pausa."""
    if fuente_menu is None:
        fuente_menu = crear_fuentes()["menu"]
    y_superior = Y_ICONOS_FIJOS + alto_icono_fijo(fuente_menu) + _GAP_PANEL_DEBAJO_ICONOS
    y_inferior = ALTO - _MARGEN_PANEL_SOBRE_PIE
    return y_superior, y_inferior


def ancho_icono_fijo(fuente_menu: pygame.font.Font) -> int:
    """Mismo criterio que ``AplicacionGrafica._crear_botones_fijos``."""
    ancho_ref = max(
        fuente_menu.size(etiqueta)[0] for etiqueta in _ETIQUETAS_REF_ICONO_FIJO
    )
    return max(ANCHO_MIN_ICONO_FIJO, ancho_ref + 2 * PADDING_ICONO_FIJO_X)


def alto_icono_fijo(fuente_menu: pygame.font.Font) -> int:
    alto_ref = max(
        fuente_menu.size(etiqueta)[1] for etiqueta in _ETIQUETAS_REF_ICONO_FIJO
    )
    return max(ALTO_MIN_ICONO_FIJO, alto_ref + 2 * PADDING_ICONO_FIJO_Y)


def borde_derecho_iconos_fijos(fuente_menu: pygame.font.Font | None = None) -> int:
    """Coordenada X justo después del último icono fijo."""
    if fuente_menu is None:
        fuente_menu = crear_fuentes()["menu"]
    ancho = ancho_icono_fijo(fuente_menu)
    return (
        X_ICONOS_FIJOS
        + NUM_ICONOS_FIJOS * ancho
        + (NUM_ICONOS_FIJOS - 1) * GAP_ICONOS_FIJOS
    )


def x_min_contenido_bajo_iconos(fuente_menu: pygame.font.Font | None = None) -> int:
    """Borde izquierdo del área útil (a la derecha de la barra fija)."""
    return borde_derecho_iconos_fijos(fuente_menu) + _GAP_TRAS_ICONOS_FIJOS


def x_min_centro_barra_partida(fuente_menu: pygame.font.Font) -> int:
    """Inicio de la zona central de la barra de partida (sin solapar iconos)."""
    return x_min_contenido_bajo_iconos(fuente_menu) + _MARGEN_EXTRA_BARRA_PARTIDA

COLOR_FONDO = (32, 72, 140)
COLOR_TITULO = (255, 255, 255)
COLOR_TEXTO = (220, 232, 248)
COLOR_AVISO = (255, 196, 96)
COLOR_OK = (72, 180, 120)
COLOR_ERROR = (220, 90, 90)
COLOR_PANEL = (26, 58, 110)
COLOR_TEXTO_PANEL = (170, 190, 220)
COLOR_ACENTO = (70, 130, 210)

TAMANO_FUENTE_PEQUENA = 16


def crear_fuentes() -> dict[str, pygame.font.Font]:
    return {
        "titulo": crear_fuente(40, familia="texto", bold=True),
        "subtitulo": crear_fuente(28, familia="texto", bold=True),
        "cuerpo": crear_fuente(22, familia="texto"),
        "menu": crear_fuente(24, familia="texto"),
        "opcion": crear_fuente(20, familia="texto"),
        "pie": crear_fuente(18, familia="texto"),
        "pequena": crear_fuente(TAMANO_FUENTE_PEQUENA, familia="texto"),
        # Iconos de la barra fija: símbolos (⏯) y emojis (📣).
        "icono": crear_fuente(22, familia="simbolos"),
        "icono_emoji": crear_fuente(22, familia="emoji"),
    }
