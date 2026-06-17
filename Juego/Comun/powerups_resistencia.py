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

from Comun.modelos import Pregunta

LETRAS_OPCION = ("A", "B", "C", "D")

POWERUPS: dict[str, tuple[str, str]] = {
    "fifty_fifty": ("50/50", "Quita 2 respuestas incorrectas"),
    "bomba": ("Bomba", "Destruyes una respuesta incorrecta"),
    "skip": ("Saltar", "Pasa a la siguiente pregunta sin penalización"),
    "tiempo_extra": ("+Tiempo", "Añade 20 s a esta pregunta"),
    "escudo": ("Escudo", "El próximo fallo no cuesta vida ni corta la racha"),
}

POWERUPS_LOOT = tuple(POWERUPS.keys())


def etiqueta_powerup(powerup_id: str) -> str:
    return POWERUPS.get(powerup_id, (powerup_id, powerup_id))[0]


def descripcion_powerup(powerup_id: str) -> str:
    return POWERUPS.get(powerup_id, (powerup_id, ""))[1]


@dataclass(frozen=True)
class EventoRecompensaResistencia:
    etiqueta: str
    delta_vidas: int = 0
    delta_vidas_max: int = 0
    powerup_id: str | None = None
    cantidad_powerup: int = 1


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


def evento_recompensa_aleatoria(numero_pregunta: int, *, semilla: int) -> EventoRecompensaResistencia | None:
    """Tras un acierto: vida, tope de vidas u objeto de inventario."""
    if numero_pregunta < 3:
        return None
    rng = random.Random(semilla * 104729 + numero_pregunta)
    prob = min(0.55, 0.08 + numero_pregunta * 0.003)
    if rng.random() > prob:
        return None
    tabla = [
        (0.22, EventoRecompensaResistencia("¡Vida extra!", delta_vidas=1)),
        (0.10, EventoRecompensaResistencia("Golpe de mala suerte: pierdes 1 vida", delta_vidas=-1)),
        (0.12, EventoRecompensaResistencia("Corazón máximo +1", delta_vidas_max=1)),
        (0.06, EventoRecompensaResistencia("Corazón máximo −1", delta_vidas_max=-1)),
    ]
    acum = 0.0
    roll = rng.random()
    for peso, evento in tabla:
        acum += peso
        if roll < acum:
            return evento
    pid = rng.choice(POWERUPS_LOOT)
    return EventoRecompensaResistencia(
        f"Objeto: {etiqueta_powerup(pid)}",
        powerup_id=pid,
    )
