#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga de fuentes por familia: texto, matemáticas, símbolos y emojis."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

import pygame

FamiliaFuente = Literal["texto", "matematicas", "simbolos", "emoji"]

_CACHE: dict[tuple[FamiliaFuente, int, bool], pygame.font.Font] = {}
_RUTAS_RESUELTAS: dict[FamiliaFuente, Path | None] = {}


def invalidar_cache_fuentes() -> None:
    """Vacía la caché tras ``pygame.quit()`` (p. ej. entre tests)."""
    _CACHE.clear()

def _windir() -> Path:
    return Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"


_LINUX_DEJAVU_TEXTO = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
]
_LINUX_DEJAVU_MATH_SIM = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
]
_LINUX_NOTO_EMOJI = [
    Path("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"),
    Path("/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf"),
]


def _candidatos_win32(familia: FamiliaFuente, bold: bool) -> list[Path]:
    fonts = _windir()
    if familia == "texto":
        if bold:
            return [fonts / "cambriab.ttf", fonts / "cambria.ttc"]
        return [fonts / "cambria.ttc", fonts / "segoeuisymbol.ttf"]
    if familia == "matematicas":
        if bold:
            return [fonts / "cambriab.ttf", fonts / "cambria.ttc"]
        return [fonts / "cambria.ttc", fonts / "cambriab.ttf"]
    if familia == "simbolos":
        return [fonts / "seguisym.ttf", fonts / "segoeuisymbol.ttf", fonts / "symbol.ttf"]
    return [fonts / "seguiemj.ttf", fonts / "segoeuiemoji.ttf"]


def _candidatos_darwin(familia: FamiliaFuente) -> list[Path]:
    if familia == "texto":
        return [
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Helvetica.ttc"),
        ]
    if familia == "matematicas":
        return [Path("/System/Library/Fonts/Supplemental/Cambria.ttc")]
    if familia == "simbolos":
        return [Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")]
    return [Path("/System/Library/Fonts/Apple Color Emoji.ttc")]


def _candidatos_linux(familia: FamiliaFuente) -> list[Path]:
    if familia == "texto":
        return list(_LINUX_DEJAVU_TEXTO)
    if familia in ("matematicas", "simbolos"):
        return list(_LINUX_DEJAVU_MATH_SIM)
    return list(_LINUX_NOTO_EMOJI)


def _candidatos(familia: FamiliaFuente, bold: bool) -> list[Path]:
    if sys.platform == "win32":
        return _candidatos_win32(familia, bold)
    if sys.platform == "darwin":
        return _candidatos_darwin(familia)
    return _candidatos_linux(familia)


def _resolver_ruta(familia: FamiliaFuente, bold: bool = False) -> Path | None:
    if not bold and familia in _RUTAS_RESUELTAS:
        return _RUTAS_RESUELTAS[familia]
    for ruta in _candidatos(familia, bold):
        if not ruta.is_file():
            continue
        if not bold:
            _RUTAS_RESUELTAS[familia] = ruta
        return ruta
    if not bold:
        _RUTAS_RESUELTAS[familia] = None
    return None


def fuente_disponible(familia: FamiliaFuente) -> bool:
    return _resolver_ruta(familia) is not None


def fuente_matematica_disponible() -> bool:
    return fuente_disponible("matematicas")


def _sysfont_fallback(familia: FamiliaFuente, tamano: int, bold: bool) -> pygame.font.Font:
    if familia == "texto":
        nombre = "segoeui,arial,dejavusans,liberationsans"
    elif familia == "matematicas":
        nombre = "cambria,dejavusans,liberationsans"
    elif familia == "simbolos":
        nombre = "segoeuisymbol,dejavusans"
    else:
        nombre = "segoeuiemoji,notocoloremoji,applecoloremoji"
    return pygame.font.SysFont(nombre, tamano, bold=bold)


def crear_fuente(
    tamano: int,
    *,
    familia: FamiliaFuente = "texto",
    bold: bool = False,
) -> pygame.font.Font:
    clave = (familia, tamano, bold)
    if clave in _CACHE:
        return _CACHE[clave]
    ruta = _resolver_ruta(familia, bold)
    if ruta is not None:
        fuente = pygame.font.Font(str(ruta), tamano)
    else:
        fuente = _sysfont_fallback(familia, tamano, bold)
    _CACHE[clave] = fuente
    return fuente


def conjunto_fuentes(tamano: int, *, bold: bool = False) -> dict[FamiliaFuente, pygame.font.Font]:
    familias: tuple[FamiliaFuente, ...] = ("texto", "matematicas", "simbolos", "emoji")
    return {f: crear_fuente(tamano, familia=f, bold=bold and f == "texto") for f in familias}


def superficie_emoji_valida(surf: pygame.Surface) -> bool:
    """True si la superficie parece un emoji a color (no tofu ni reloj en escala de grises)."""
    if surf.get_width() <= 4:
        return False
    vivid = 0
    opacos = 0
    for x in range(surf.get_width()):
        for y in range(surf.get_height()):
            c = surf.get_at((x, y))
            if c.a <= 10:
                continue
            opacos += 1
            r, g, b = c[:3]
            if max(r, g, b) - min(r, g, b) > 35:
                vivid += 1
    if opacos < 24 or vivid < 10:
        return False
    return vivid / opacos > 0.06


def render_icono_barra(
    fuente_emoji: pygame.font.Font,
    fuente_txt: pygame.font.Font,
    candidatos: tuple[str, ...],
    ascii_fallback: str,
    color: tuple[int, int, int],
    *,
    usar_emoji: bool,
) -> pygame.Surface:
    """Emoji con fuente emoji; si el glifo falla (tofu), prueba alternativas o ASCII."""
    if usar_emoji:
        for glyph in candidatos:
            for antialias in (True, False):
                try:
                    surf = fuente_emoji.render(glyph, antialias, color)
                except Exception:
                    continue
                if superficie_emoji_valida(surf):
                    return surf
    return fuente_txt.render(ascii_fallback, True, color)
