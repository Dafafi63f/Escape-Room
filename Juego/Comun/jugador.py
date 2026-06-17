#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nombre de jugador por defecto (consola y gráfico)."""

from __future__ import annotations

__all__ = [
    "NOMBRE_JUGADOR_DEFECTO",
    "es_nombre_anonimo",
    "nombre_jugador_efectivo",
]

NOMBRE_JUGADOR_DEFECTO = "Anonimo"


def nombre_jugador_efectivo(texto: str) -> str:
    limpio = (texto or "").strip()
    return limpio or NOMBRE_JUGADOR_DEFECTO


def es_nombre_anonimo(nombre: str) -> bool:
    return nombre_jugador_efectivo(nombre) == NOMBRE_JUGADOR_DEFECTO
