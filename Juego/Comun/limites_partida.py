#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Límites globales de tamaño de partida y examen."""

from __future__ import annotations

MIN_PREGUNTAS_PARTIDA = 5

# Repaso y simulacro (perfil balanceado): preguntas por materia en el generador.
PREGUNTAS_POR_MATERIA_HISTORIA = 4


def min_materias_para_minimo_preguntas(
    preguntas_por_materia: int = PREGUNTAS_POR_MATERIA_HISTORIA,
) -> int:
    """Materias mínimas para alcanzar ``MIN_PREGUNTAS_PARTIDA`` preguntas."""
    if preguntas_por_materia <= 0:
        return MIN_PREGUNTAS_PARTIDA
    return (MIN_PREGUNTAS_PARTIDA + preguntas_por_materia - 1) // preguntas_por_materia


def validar_total_preguntas(n: int, *, contexto: str = "") -> None:
    if n < MIN_PREGUNTAS_PARTIDA:
        msg = f"El examen debe tener al menos {MIN_PREGUNTAS_PARTIDA} preguntas."
        if contexto:
            msg = f"{msg} {contexto}"
        raise ValueError(msg)
