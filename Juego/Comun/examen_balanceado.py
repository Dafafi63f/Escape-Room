#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plantilla de examen balanceado 4×6 (compartida por día y aleatorio)."""

from __future__ import annotations

__all__ = [
    "MATERIAS_EXAMEN_BALANCEADO",
    "PREGUNTAS_EXAMEN_BALANCEADO",
    "PREGUNTAS_POR_MATERIA_BALANCEADO",
]

MATERIAS_EXAMEN_BALANCEADO = 4
PREGUNTAS_POR_MATERIA_BALANCEADO = 6
PREGUNTAS_EXAMEN_BALANCEADO = MATERIAS_EXAMEN_BALANCEADO * PREGUNTAS_POR_MATERIA_BALANCEADO
