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

COLOR_FONDO = (32, 72, 140)
COLOR_TITULO = (255, 255, 255)
COLOR_TEXTO = (220, 232, 248)
COLOR_AVISO = (255, 196, 96)
COLOR_OK = (72, 180, 120)
COLOR_ERROR = (220, 90, 90)
COLOR_PANEL = (26, 58, 110)
COLOR_ACENTO = (70, 130, 210)


def crear_fuentes() -> dict[str, pygame.font.Font]:
    return {
        "titulo": crear_fuente(40, familia="texto", bold=True),
        "subtitulo": crear_fuente(28, familia="texto", bold=True),
        "cuerpo": crear_fuente(22, familia="texto"),
        "menu": crear_fuente(24, familia="texto"),
        "opcion": crear_fuente(20, familia="texto"),
        "pie": crear_fuente(18, familia="texto"),
        "pequena": crear_fuente(16, familia="texto"),
        # Iconos de la barra fija: símbolos (⏸) y emojis (💬).
        "icono": crear_fuente(22, familia="simbolos"),
        "icono_emoji": crear_fuente(22, familia="emoji"),
    }
