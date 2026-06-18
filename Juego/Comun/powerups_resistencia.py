#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comodines del modo resistencia (inspirados en Preguntados / Trivia Crack).

Fáciles de implementar en opción múltiple A–D:
  - 50/50, bomba, saltar, tiempo extra, escudo (segunda oportunidad).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from Comun.estado_resistencia import EstadoResistencia
from Comun.modelos import Pregunta

LETRAS_OPCION = ("A", "B", "C", "D")

# Escala la prob. de premio por tirada (la curva buena va de ~90 % a ~3 %).
FACTOR_TIRADA_RECOMPENSA = 0.20
# Cupo de tiradas de recompensa tras cada acierto (independiente de eventos/popups).
MAX_TIRADAS_RECOMPENSA_ACIERTO = 2

POWERUPS: dict[str, tuple[str, str]] = {
    "fifty_fifty": ("50/50", "Quita 2 respuestas incorrectas"),
    "bomba": ("Bomba", "Destruyes una respuesta incorrecta"),
    "skip": ("Saltar", "Siguiente pregunta sin perder vida (corta la racha)"),
    "tiempo_extra": ("+Tiempo", "Añade 20 s a esta pregunta"),
    "escudo": ("Escudo", "El próximo fallo no cuesta vida ni corta la racha"),
    "cambio": ("Cambio", "Sustituye por una pregunta parecida (misma materia y tipo)"),
}

POWERUPS_LOOT = tuple(POWERUPS.keys())


@dataclass(frozen=True)
class EventoRecompensaResistencia:
    etiqueta: str
    delta_vidas: int = 0
    delta_vidas_max: int = 0
    powerup_id: str | None = None
    cantidad_powerup: int = 1


def etiqueta_powerup(powerup_id: str) -> str:
    return POWERUPS.get(powerup_id, (powerup_id, powerup_id))[0]


def descripcion_powerup(powerup_id: str) -> str:
    return POWERUPS.get(powerup_id, (powerup_id, ""))[1]


def _incorrectas(p: Pregunta) -> list[str]:
    correcta = p.correcta if p.correcta in LETRAS_OPCION else ""
    return [letra for letra in LETRAS_OPCION if letra != correcta and p.opciones.get(letra)]


def letras_ocultas_fifty_fifty(p: Pregunta, rng: random.Random | None = None) -> frozenset[str]:
    rng = rng or random.Random()
    malas = _incorrectas(p)
    rng.shuffle(malas)
    return frozenset(malas[:2])


def letras_ocultas_bomba(p: Pregunta, rng: random.Random | None = None) -> frozenset[str]:
    rng = rng or random.Random()
    malas = _incorrectas(p)
    if not malas:
        return frozenset()
    return frozenset({rng.choice(malas)})


def letras_ocultas_por_cantidad(
    p: Pregunta,
    cantidad: int,
    *,
    semilla: int,
) -> frozenset[str]:
    if cantidad <= 0:
        return frozenset()
    rng = random.Random(semilla * 31 + len(p.texto))
    malas = _incorrectas(p)
    rng.shuffle(malas)
    return frozenset(malas[: min(cantidad, len(malas))])


def texto_pregunta_visible(texto: str, fraccion: float) -> str:
    """Recorta el enunciado y tapa el resto (evento niebla)."""
    if fraccion >= 1.0 or not texto.strip():
        return texto
    fraccion = max(0.2, min(1.0, fraccion))
    corte = max(8, int(len(texto) * fraccion))
    visible = texto[:corte].rstrip()
    if len(visible) >= len(texto):
        return texto
    resto = len(texto) - len(visible)
    return f"{visible} {'▓' * min(48, max(8, resto))}"


def _generar_recompensa_aleatoria(
    rng: random.Random,
    *,
    numero_pregunta: int,
) -> EventoRecompensaResistencia:
    from Comun.probabilidad_resistencia import (
        factor_bueno_resistencia,
        factor_malo_resistencia,
    )

    factor_bueno = max(0.08, factor_bueno_resistencia(numero_pregunta))
    factor_malo = max(0.08, factor_malo_resistencia(numero_pregunta))
    tabla = [
        (0.22 * factor_bueno, EventoRecompensaResistencia("¡Vida extra!", delta_vidas=1), False),
        (0.12 * factor_bueno, EventoRecompensaResistencia("Corazón máximo +1", delta_vidas_max=1), False),
        (
            0.16 * factor_malo,
            EventoRecompensaResistencia("Corazón máximo −1", delta_vidas_max=-1),
            True,
        ),
    ]
    roll = rng.random()
    acum = 0.0
    for peso, evento, _es_malo in tabla:
        acum += peso
        if roll < acum:
            return evento
    pid = rng.choice(POWERUPS_LOOT)
    return EventoRecompensaResistencia(
        f"Objeto: {etiqueta_powerup(pid)}",
        powerup_id=pid,
    )


def tirar_recompensas_tras_acierto(
    er: EstadoResistencia,
    *,
    numero_pregunta: int,
) -> list[EventoRecompensaResistencia]:
    """Bonificaciones tras acertar; más probables al inicio, raras al final."""
    from Comun.mecanicas_resistencia import rng_partida
    from Comun.probabilidad_resistencia import probabilidad_buena_resistencia

    prob_tirada = probabilidad_buena_resistencia(numero_pregunta) * FACTOR_TIRADA_RECOMPENSA
    resultados: list[EventoRecompensaResistencia] = []
    for _ in range(MAX_TIRADAS_RECOMPENSA_ACIERTO):
        er.tiradas_recompensa += 1
        rng = rng_partida(er, er.tiradas_recompensa * 9973 + 42)
        if rng.random() > prob_tirada:
            continue
        resultados.append(_generar_recompensa_aleatoria(rng, numero_pregunta=numero_pregunta))
    return resultados
