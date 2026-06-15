#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lectura de teclas a bajo nivel (Windows: ``msvcrt``; otros SO: fallback por línea).

La lógica de menús y contexto de ayuda está en ``entrada_menu.py``.
"""

from __future__ import annotations

import sys
from enum import Enum

TECLA_AYUDA = "H"
TECLA_FEEDBACK = "F"
TECLA_ESC = "Esc"
TECLA_ATRAS_TEXTO = TECLA_ESC
TECLA_PAUSA = TECLA_ESC


class TipoTecla(str, Enum):
    ENTER = "enter"
    DIGITO = "digito"
    LETRA = "letra"
    CARACTER = "caracter"
    BORRAR = "borrar"
    SUPR = "supr"
    ESCAPE = "escape"
    IGNORAR = "ignorar"


class EventoTecla:
    __slots__ = ("tipo", "valor")

    def __init__(self, tipo: TipoTecla, valor: str = "") -> None:
        self.tipo = tipo
        self.valor = valor


def leer_tecla_windows(*, en_pausa: bool) -> EventoTecla:
    import msvcrt

    _ = en_pausa  # reservado para variantes futuras de pausa
    b = msvcrt.getch()
    if b == b"\x03":
        raise KeyboardInterrupt
    if b == b"\x1b":
        return EventoTecla(TipoTecla.ESCAPE)
    if b in (b"\r", b"\n"):
        return EventoTecla(TipoTecla.ENTER)
    if b in (b"\x7f", b"\x08"):
        return EventoTecla(TipoTecla.SUPR)
    if b in (b"\x00", b"\xe0"):
        b2 = msvcrt.getch()
        if b2 == b"S":
            return EventoTecla(TipoTecla.SUPR)
        return EventoTecla(TipoTecla.IGNORAR)

    try:
        c = b.decode("utf-8", errors="ignore")
    except Exception:
        return EventoTecla(TipoTecla.IGNORAR)

    if not c:
        return EventoTecla(TipoTecla.IGNORAR)

    if c.isdigit():
        return EventoTecla(TipoTecla.DIGITO, c)
    if c.isalpha():
        return EventoTecla(TipoTecla.LETRA, c.upper())
    return EventoTecla(TipoTecla.IGNORAR)


def leer_tecla_texto_windows() -> EventoTecla:
    """Tecla a tecla para escribir texto (incluye espacios y símbolos)."""
    import msvcrt

    b = msvcrt.getch()
    if b == b"\x03":
        raise KeyboardInterrupt
    if b == b"\x1b":
        return EventoTecla(TipoTecla.ESCAPE)
    if b in (b"\r", b"\n"):
        return EventoTecla(TipoTecla.ENTER)
    if b in (b"\x08", b"\x7f"):
        return EventoTecla(TipoTecla.BORRAR)
    if b in (b"\x00", b"\xe0"):
        b2 = msvcrt.getch()
        if b2 in (b"S", b"s"):
            return EventoTecla(TipoTecla.SUPR)
        return EventoTecla(TipoTecla.IGNORAR)

    try:
        c = b.decode("utf-8", errors="ignore")
    except Exception:
        return EventoTecla(TipoTecla.IGNORAR)

    if not c or not c.isprintable() or c == "\t":
        return EventoTecla(TipoTecla.IGNORAR)

    if c.isalpha():
        letra = c.upper()
        if letra == TECLA_AYUDA:
            return EventoTecla(TipoTecla.LETRA, TECLA_AYUDA)
        if letra == TECLA_FEEDBACK:
            return EventoTecla(TipoTecla.LETRA, TECLA_FEEDBACK)
    return EventoTecla(TipoTecla.CARACTER, c)


def leer_tecla_fallback() -> EventoTecla:
    """Entornos sin ``msvcrt``: una línea; Enter vacío = ENTER."""
    try:
        linea = input().strip()
    except EOFError:
        from .navegacion import SalirPrograma

        raise SalirPrograma() from None
    if linea == "":
        return EventoTecla(TipoTecla.ENTER)
    if linea.isdigit() and len(linea) == 1:
        return EventoTecla(TipoTecla.DIGITO, linea)
    if len(linea) == 1 and linea.isalpha():
        return EventoTecla(TipoTecla.LETRA, linea.upper())
    return EventoTecla(TipoTecla.IGNORAR)


def leer_tecla(*, en_pausa: bool = False) -> EventoTecla:
    if sys.platform == "win32":
        return leer_tecla_windows(en_pausa=en_pausa)
    return leer_tecla_fallback()


# Alias interno usado en tests y en ``entrada_menu`` (compatibilidad).
_EventoTecla = EventoTecla
_leer_tecla_windows = leer_tecla_windows
_leer_tecla_texto_windows = leer_tecla_texto_windows
_leer_tecla_fallback = leer_tecla_fallback
