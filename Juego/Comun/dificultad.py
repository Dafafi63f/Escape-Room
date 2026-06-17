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


def niveles_en_pool(pool: list[Pregunta]) -> frozenset[int]:
    if not pool:
        return frozenset({1})
    return frozenset(complejidad_pregunta(p) for p in pool)


def normalizar_niveles_seleccionados(
    seleccion: set[int] | frozenset[int] | None,
    pool: list[Pregunta],
) -> frozenset[int]:
    disponibles = niveles_en_pool(pool)
    if not seleccion:
        return disponibles
    elegidos = frozenset(n for n in seleccion if n in disponibles)
    return elegidos if elegidos else disponibles


def niveles_seleccion_ordenados(niveles: frozenset[int]) -> list[int]:
    return sorted(niveles)


def describe_niveles_seleccion(niveles: frozenset[int]) -> str:
    ordenados = niveles_seleccion_ordenados(niveles)
    if len(ordenados) == 1:
        return str(ordenados[0])
    return ",".join(str(n) for n in ordenados)


def techo_complejidad_partida(
    *,
    dificultad_progresiva: bool,
    respondidas: int,
    niveles_seleccion: frozenset[int],
    cada_n: int = 40,
) -> int:
    ordenados = niveles_seleccion_ordenados(niveles_seleccion)
    if not ordenados:
        return 1
    if not dificultad_progresiva or len(ordenados) == 1:
        return ordenados[-1]
    indice = min(respondidas // max(1, cada_n), len(ordenados) - 1)
    return ordenados[indice]


def debe_filtrar_por_nivel(
    pool: list[Pregunta],
    niveles_seleccion: frozenset[int],
    dificultad_progresiva: bool,
) -> bool:
    disponibles = niveles_en_pool(pool)
    if len(disponibles) <= 1:
        return False
    if dificultad_progresiva:
        return bool(niveles_seleccion)
    return niveles_seleccion != disponibles


def pregunta_permitida_por_nivel(
    pregunta: Pregunta,
    *,
    niveles_seleccion: frozenset[int],
    techo: int,
    dificultad_progresiva: bool,
) -> bool:
    complejidad = complejidad_pregunta(pregunta)
    if complejidad not in niveles_seleccion:
        return False
    if dificultad_progresiva:
        return complejidad <= techo
    return True
