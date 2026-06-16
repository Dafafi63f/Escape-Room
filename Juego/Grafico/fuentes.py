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


def _windir() -> Path:
    return Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"


def _candidatos(familia: FamiliaFuente, bold: bool) -> list[Path]:
    rutas: list[Path] = []
    if sys.platform == "win32":
        fonts = _windir()
        if familia == "texto":
            if bold:
                # Mantiene el estilo anterior (Cambria para texto normal).
                rutas.extend([fonts / "cambriab.ttf", fonts / "cambria.ttc"])
            else:
                rutas.extend([fonts / "cambria.ttc", fonts / "segoeuisymbol.ttf"])
        elif familia == "matematicas":
            if bold:
                rutas.extend([fonts / "cambriab.ttf", fonts / "cambria.ttc"])
            else:
                rutas.extend([fonts / "cambria.ttc", fonts / "cambriab.ttf"])
        elif familia == "simbolos":
            rutas.extend(
                [
                    fonts / "seguisym.ttf",
                    fonts / "segoeuisymbol.ttf",
                    fonts / "symbol.ttf",
                ]
            )
        elif familia == "emoji":
            rutas.extend([fonts / "seguiemj.ttf", fonts / "segoeuiemoji.ttf"])
    elif sys.platform == "darwin":
        if familia == "texto":
            rutas.extend(
                [
                    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
                    Path("/System/Library/Fonts/Helvetica.ttc"),
                ]
            )
        elif familia == "matematicas":
            rutas.extend([Path("/System/Library/Fonts/Supplemental/Cambria.ttc")])
        elif familia == "simbolos":
            rutas.extend([Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")])
        elif familia == "emoji":
            rutas.extend([Path("/System/Library/Fonts/Apple Color Emoji.ttc")])
    else:
        if familia == "texto":
            rutas.extend(
                [
                    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                    Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
                    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
                ]
            )
        elif familia == "matematicas":
            rutas.extend(
                [
                    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
                ]
            )
        elif familia == "simbolos":
            rutas.extend(
                [
                    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
                ]
            )
        elif familia == "emoji":
            rutas.extend(
                [
                    Path("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"),
                    Path("/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf"),
                ]
            )
    return rutas


def _resolver_ruta(familia: FamiliaFuente, bold: bool = False) -> Path | None:
    if not bold:
        if familia in _RUTAS_RESUELTAS:
            return _RUTAS_RESUELTAS[familia]
    for ruta in _candidatos(familia, bold):
        if ruta.is_file():
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
