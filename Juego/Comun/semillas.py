#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Semillas del juego: diaria (examen del día), aleatoria de partida, derivadas y RNG estable.

Uso principal:
- ``semilla_diaria`` / ``modos_diarios.semilla_examen_dia`` — único uso diario en partida (Examen del día).
- ``semilla_partida_aleatoria`` — escape room, resistencia y examen aleatorio (partida distinta cada vez). No hay modos diarios previstos para escape ni resistencia.
- ``semilla_partida_libre`` — permutación estable de opciones en modo libre por nombre de jugador.
- ``semilla_derivada`` / ``rng_desde_semilla`` — claves locales reproducibles dentro de una partida.
"""

from __future__ import annotations

import hashlib
import random
import secrets
from datetime import date, datetime, timezone

_SEMILLA_MAX = 2**31 - 1

__all__ = [
    "formatear_semilla_diaria",
    "normalizar_semilla_base",
    "rng_desde_semilla",
    "semilla_aleatoria",
    "semilla_derivada",
    "semilla_diaria",
    "semilla_estable_texto",
    "semilla_orden_opciones",
    "semilla_partida_aleatoria",
    "semilla_partida_libre",
]


def _fecha_utc(d: date | None = None) -> date:
    return d or datetime.now(timezone.utc).date()


def semilla_diaria(d: date | None = None) -> int:
    """Entero estable por día civil (UTC), formato DDMMYYYY (p. ej. 22062026)."""
    return int(_fecha_utc(d).strftime("%d%m%Y"))


def formatear_semilla_diaria(semilla: int) -> str:
    """Representación de 8 dígitos con ceros a la izquierda (p. ej. 1012026 → 01012026)."""
    return f"{semilla:08d}"


def semilla_aleatoria() -> int:
    """Entero aleatorio criptográfico para arrancar una partida nueva."""
    return secrets.randbelow(_SEMILLA_MAX) + 1


def semilla_estable_texto(texto: str) -> int:
    """Hash determinista en [1, 2³¹−1] (no depende de ``PYTHONHASHSEED``)."""
    digest = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % _SEMILLA_MAX + 1


def semilla_partida_aleatoria() -> int:
    """Semilla de arranque aleatoria (escape room, resistencia, examen aleatorio)."""
    return semilla_aleatoria()


def semilla_partida_libre(*, nombre: str) -> int:
    """Base estable por jugador para permutar opciones en modo libre."""
    return semilla_estable_texto(f"{nombre.strip()}|libre")


def normalizar_semilla_base(semilla_base: int | None) -> int:
    return semilla_base or 0


def semilla_derivada(semilla_base: int | None, *partes: int | str) -> int:
    """Combina una semilla base con claves enteras o texto."""
    acc = normalizar_semilla_base(semilla_base)
    for parte in partes:
        if isinstance(parte, str):
            acc = (acc * 1_000_003 + semilla_estable_texto(parte)) % _SEMILLA_MAX
        else:
            acc = (acc + int(parte) * 1_009) % _SEMILLA_MAX
    return acc or 1


def semilla_orden_opciones(
    *,
    semilla_base: int | None,
    numero_turno: int,
    indice_pregunta: int = 0,
) -> int:
    """Semilla estable por turno para permutar opciones en pantalla."""
    base = normalizar_semilla_base(semilla_base)
    return base + numero_turno * 1_009 + indice_pregunta * 7_919


def rng_desde_semilla(semilla_base: int | None, clave: int) -> random.Random:
    """``Random`` reproducible a partir de la semilla de partida y una clave local."""
    base = normalizar_semilla_base(semilla_base)
    return random.Random(base * 1_000_003 + clave * 104_729)
