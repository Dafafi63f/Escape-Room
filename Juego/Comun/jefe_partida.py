#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bloques de partida: 3 o 5 preguntas (puertas escape / bloques resistencia); jefe = 10."""

from __future__ import annotations

import random
from collections import Counter

from Comun.config_historia import GRUPOS_TEMATICOS, etiqueta_grupo_tematico

PREGUNTAS_POR_JEFE = 10
TAMANOS_BLOQUE_NORMAL = (3, 5)

_DIFICULTADES_VALIDAS = frozenset({"Facil", "Media", "Dificil"})

_ETIQUETA_DIFICULTAD_JEFE: dict[str, str] = {
    "facil": "fácil",
    "medio": "medio",
    "dificil": "difícil",
    "equilibrado": "equilibrado",
}

_PERFIL_POR_DIFICULTAD_JEFE: dict[str, str] = {
    "facil": "facil",
    "medio": "media",
    "dificil": "dificil",
    "equilibrado": "balanceado",
}

# Resistencia: pity de jefe (primer intento no antes de ~20 preguntas; bloque de 10).
PREGUNTA_MIN_JEFE_RESISTENCIA = 20
PROB_JEFE_BASE_RESISTENCIA = 0.035
PITY_INC_JEFE_RESISTENCIA = 0.018
PITY_MAX_BOOST_JEFE_RESISTENCIA = 0.42
PREGUNTAS_HARD_PITY_JEFE_RESISTENCIA = 22


def elegir_tamano_bloque_normal(rng: random.Random) -> int:
    """Tamaño aleatorio de bloque/puerta normal (solo 3 o 5)."""
    return rng.choice(TAMANOS_BLOQUE_NORMAL)


def tamano_coherente_bloque_o_jefe(preguntas: int, *, es_jefe: bool) -> bool:
    """True si el tamaño encaja con bloque normal (3/5) o jefe (10)."""
    if es_jefe:
        return preguntas == PREGUNTAS_POR_JEFE
    return preguntas in TAMANOS_BLOQUE_NORMAL


def sala_es_milestone_jefe(numero_sala: int) -> bool:
    """Salas 10, 20, 30… dedicadas a jefes."""
    return numero_sala > 0 and numero_sala % 10 == 0


def n_puertas_jefe_en_sala(numero_sala: int) -> int:
    if not sala_es_milestone_jefe(numero_sala):
        return 0
    return min(3, numero_sala // 10)


def clasificar_dificultad_jefe(dificultades: list[str]) -> str:
    """Clasifica un bloque según las dificultades de sus preguntas."""
    vals = [d for d in dificultades if d in _DIFICULTADES_VALIDAS]
    if not vals:
        return "equilibrado"
    total = len(vals)
    cuenta = Counter(vals)
    ratio = {k: cuenta[k] / total for k in cuenta}
    if ratio.get("Facil", 0) >= 0.6:
        return "facil"
    if ratio.get("Dificil", 0) >= 0.6:
        return "dificil"
    if ratio.get("Media", 0) >= 0.6:
        return "medio"
    return "equilibrado"


def etiqueta_dificultad_jefe(tipo: str) -> str:
    return _ETIQUETA_DIFICULTAD_JEFE.get(tipo, tipo)


def perfil_id_para_dificultad_jefe(tipo: str) -> str:
    return _PERFIL_POR_DIFICULTAD_JEFE.get(tipo, "balanceado")


def dificultades_permitidas_jefe(tipo: str) -> frozenset[str] | None:
    if tipo == "facil":
        return frozenset({"Facil"})
    if tipo == "medio":
        return frozenset({"Media"})
    if tipo == "dificil":
        return frozenset({"Dificil"})
    return None


def elegir_dificultad_jefe_escape(numero_sala: int, rng: random.Random) -> str:
    """Sesgo según progreso de la partida escape."""
    t = min(1.0, max(0.0, (numero_sala - 10) / 20.0))
    opciones: list[tuple[float, str]] = [
        (0.28 - 0.12 * t, "facil"),
        (0.32, "medio"),
        (0.22 + 0.10 * t, "equilibrado"),
        (0.10 + 0.18 * t, "dificil"),
    ]
    total = sum(p for p, _ in opciones)
    roll = rng.random() * total
    acum = 0.0
    for peso, tipo in opciones:
        acum += peso
        if roll < acum:
            return tipo
    return "equilibrado"


def elegir_dificultad_jefe_resistencia(numero_pregunta: int, rng: random.Random) -> str:
    t = min(1.0, max(0.0, (numero_pregunta - PREGUNTA_MIN_JEFE_RESISTENCIA) / 80.0))
    opciones: list[tuple[float, str]] = [
        (0.30 - 0.14 * t, "facil"),
        (0.30, "medio"),
        (0.22 + 0.08 * t, "equilibrado"),
        (0.08 + 0.20 * t, "dificil"),
    ]
    total = sum(p for p, _ in opciones)
    roll = rng.random() * total
    acum = 0.0
    for peso, tipo in opciones:
        acum += peso
        if roll < acum:
            return tipo
    return "equilibrado"


def prob_jefe_resistencia(preguntas_sin_jefe: int) -> float:
    boost = min(
        PITY_MAX_BOOST_JEFE_RESISTENCIA,
        max(0, preguntas_sin_jefe) * PITY_INC_JEFE_RESISTENCIA,
    )
    return min(0.98, PROB_JEFE_BASE_RESISTENCIA + boost)


def debe_forzar_jefe_resistencia(preguntas_sin_jefe: int) -> bool:
    return preguntas_sin_jefe >= PREGUNTAS_HARD_PITY_JEFE_RESISTENCIA


def etiqueta_jefe_grupo(grupo: str, *, dificultad: str, n: int = PREGUNTAS_POR_JEFE) -> str:
    nom = etiqueta_grupo_tematico(grupo)
    if grupo in GRUPOS_TEMATICOS:
        foco = nom
    else:
        foco = nom
    dif = etiqueta_dificultad_jefe(dificultad)
    return f"Jefe: {n} preguntas {foco} ({dif})"
