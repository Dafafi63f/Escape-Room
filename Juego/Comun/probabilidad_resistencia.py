#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probabilidades del modo resistencia según el nº de pregunta.

Al inicio predomina lo bueno; al final, lo malo; en el punto medio ~50 % cada tirada.
"""

from __future__ import annotations

from dataclasses import dataclass

# Progreso lineal desde la pregunta 5 hasta ~180 (t=1).
PREGUNTAS_HASTA_EXTREMO_PROB = 175
PREGUNTA_MIN_EVENTOS_ALEATORIOS = 5

PROB_BUENA_INICIAL = 0.90
PROB_BUENA_FINAL = 0.03
PROB_MALA_INICIAL = 0.03
PROB_MALA_FINAL = 0.90

# Escala la prob. de evento favorable de escalada (doble/triple); la curva buena va ~90 %→3 %.
FACTOR_EVENTO_BUENO_ESCALADA = 0.18

__all__ = [
    "CuotasBancoResistencia",
    "FACTOR_EVENTO_BUENO_ESCALADA",
    "PREGUNTA_MIN_EVENTOS_ALEATORIOS",
    "PREGUNTAS_HASTA_EXTREMO_PROB",
    "PROB_BUENA_FINAL",
    "PROB_BUENA_INICIAL",
    "PROB_MALA_FINAL",
    "PROB_MALA_INICIAL",
    "cuotas_banco_resistencia",
    "factor_bueno_resistencia",
    "factor_malo_resistencia",
    "factor_progreso_banco_resistencia",
    "factor_progreso_resistencia",
    "probabilidad_buena_resistencia",
    "probabilidad_evento_bueno_escalada",
    "probabilidad_mala_resistencia",
    "progreso_probabilidad_resistencia",
]


@dataclass(frozen=True)
class CuotasBancoResistencia:
    plantillas: int
    exclusivas: int


def progreso_probabilidad_resistencia(numero_pregunta: int) -> int:
    return max(0, numero_pregunta - PREGUNTA_MIN_EVENTOS_ALEATORIOS)


def factor_progreso_resistencia(
    numero_pregunta: int,
    *,
    preguntas_hasta_extremo: int = PREGUNTAS_HASTA_EXTREMO_PROB,
) -> float:
    """0 al empezar eventos, 1 en la fase tardía (curva lineal)."""
    if numero_pregunta < PREGUNTA_MIN_EVENTOS_ALEATORIOS:
        return 0.0
    progreso = progreso_probabilidad_resistencia(numero_pregunta)
    if preguntas_hasta_extremo <= 0:
        return 1.0
    return min(1.0, progreso / preguntas_hasta_extremo)


def probabilidad_buena_resistencia(numero_pregunta: int) -> float:
    """Alta al inicio, casi nula al final (~45 % en el punto medio)."""
    t = factor_progreso_resistencia(numero_pregunta)
    return PROB_BUENA_INICIAL + (PROB_BUENA_FINAL - PROB_BUENA_INICIAL) * t


def probabilidad_evento_bueno_escalada(numero_pregunta: int) -> float:
    """Prob. de doble/triple en escalada (mucho menor que prob. buena bruta)."""
    return probabilidad_buena_resistencia(numero_pregunta) * FACTOR_EVENTO_BUENO_ESCALADA


def probabilidad_mala_resistencia(numero_pregunta: int) -> float:
    """Casi nula al inicio, alta al final (~45 % en el punto medio)."""
    t = factor_progreso_resistencia(numero_pregunta)
    return PROB_MALA_INICIAL + (PROB_MALA_FINAL - PROB_MALA_INICIAL) * t


def factor_bueno_resistencia(numero_pregunta: int) -> float:
    """Peso relativo de recompensas/eventos favorables (1 → 0)."""
    return 1.0 - factor_progreso_resistencia(numero_pregunta)


def factor_malo_resistencia(numero_pregunta: int) -> float:
    """Peso relativo de penalizaciones/eventos hostiles (0 → 1)."""
    return factor_progreso_resistencia(numero_pregunta)


def factor_progreso_banco_resistencia(
    numero_pregunta: int,
    *,
    preguntas_hasta_completo: int = PREGUNTAS_HASTA_EXTREMO_PROB,
) -> float:
    """0 en la primera pregunta; 1 cuando el banco dinámico está completo."""
    if numero_pregunta <= 1:
        return 0.0
    if preguntas_hasta_completo <= 0:
        return 1.0
    return min(1.0, (numero_pregunta - 1) / preguntas_hasta_completo)


def cuotas_banco_resistencia(
    numero_pregunta: int,
    total_plantillas: int,
    total_exclusivas: int,
) -> CuotasBancoResistencia:
    """Cuántas plantillas y exclusivas están desbloqueadas en este turno."""
    t = factor_progreso_banco_resistencia(numero_pregunta)
    if t >= 1.0:
        return CuotasBancoResistencia(
            plantillas=total_plantillas,
            exclusivas=total_exclusivas,
        )
    return CuotasBancoResistencia(
        plantillas=min(total_plantillas, int(t * total_plantillas)),
        exclusivas=min(total_exclusivas, int(t * total_exclusivas)),
    )
