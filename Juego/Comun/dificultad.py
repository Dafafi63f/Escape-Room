#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cálculo de complejidad y dificultad progresiva (sin E/S)."""

from __future__ import annotations

from Comun.modelos import Pregunta


def dificultad_base(dificultad: str) -> int:
    return {"Facil": 1, "Media": 2, "Dificil": 3}.get(dificultad, 2)


def nivel_materia(nivel: str) -> int:
    try:
        return max(1, int(nivel))
    except (TypeError, ValueError):
        return 1


def complejidad_pregunta(pregunta: Pregunta) -> int:
    return nivel_materia(pregunta.nivel) + dificultad_base(pregunta.dificultad) - 1


def dificultad_global_actual(
    respondidas: int,
    global_inicial: int,
    max_global: int,
    cada_n: int = 40,
) -> int:
    subida = respondidas // max(1, cada_n)
    return min(global_inicial + subida, max_global)


def max_complejidad_pool(pool: list[Pregunta]) -> int:
    if not pool:
        return 1
    return max(complejidad_pregunta(p) for p in pool)
