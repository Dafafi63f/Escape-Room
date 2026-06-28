#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Semillas del juego: diaria (examen del día), aleatoria de partida y RNG único.

La **semilla** identifica la partida; el **azar** sale de un único ``RngPartida`` creado
al inicio. Cada ``.random()``, ``.shuffle()``, etc. consume el generador y devuelve
un valor distinto aunque la semilla no cambie. Recrear ``Random(semilla)`` a mitad de
partida reiniciaría la secuencia: por eso solo se instancia ``RngPartida`` una vez.
"""

from __future__ import annotations

import hashlib
import random
import secrets
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

_SEMILLA_MAX = 2**31 - 1

__all__ = [
    "RngPartida",
    "crear_rng_partida",
    "formatear_semilla_diaria",
    "resolver_semillas_partida",
    "semilla_aleatoria",
    "semilla_diaria",
    "semilla_estable_texto",
    "semilla_partida_aleatoria",
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
    """Semilla de arranque aleatoria para una partida nueva."""
    return semilla_aleatoria()


@dataclass
class RngPartida:
    """Generador de partida: una semilla, un ``Random`` que avanza hasta fin de sesión."""

    semilla: int
    _rng: random.Random = field(repr=False, compare=False)

    @classmethod
    def desde_semilla(cls, semilla: int) -> RngPartida:
        """Crea el único generador de la partida a partir de su semilla."""
        return cls(semilla=semilla, _rng=random.Random(semilla))

    @classmethod
    def continuar(cls, semilla: int, rng: random.Random) -> RngPartida:
        """Reutiliza un ``Random`` ya consumido (p. ej. tras ``generar_examen``)."""
        return cls(semilla=semilla, _rng=rng)

    @property
    def interno(self) -> random.Random:
        """Acceso al ``Random`` subyacente (misma instancia siempre)."""
        return self._rng

    def __getattr__(self, name: str) -> Any:
        return getattr(self._rng, name)


def crear_rng_partida(semilla: int) -> RngPartida:
    """Alias de ``RngPartida.desde_semilla``; usar solo al arrancar la partida."""
    return RngPartida.desde_semilla(semilla)


def resolver_semillas_partida(
    *,
    preset_id: str,
    cfg: object | None = None,
    semilla_override: int | None = None,
    orden_preguntas: str = "aleatorio",
) -> int:
    """Devuelve la semilla de partida (única fuente de azar de la sesión).

    - Examen del día con orden fijo: semilla diaria.
    - Examen del día con orden variable: semilla aleatoria nueva cada partida
      (el contenido fijo del día se fija aparte con ``semilla_diaria``).
    - Resto: semilla aleatoria o manual según configuración.
    """
    if semilla_override is not None:
        return semilla_override

    from Comun.modos_diarios import (
        es_id_examen_fijo,
        origen_semilla_desde_config,
        semilla_contenido_examen_fijo,
        semilla_defecto_examen_fijo,
    )

    if cfg is not None and es_id_examen_fijo(preset_id):
        origen = origen_semilla_desde_config(cfg)
        if origen == "diario":
            if orden_preguntas == "variar":
                return semilla_partida_aleatoria()
            return semilla_contenido_examen_fijo(cfg)
        if origen == "semilla":
            return cfg.get_int("semilla", semilla_defecto_examen_fijo())
        return semilla_partida_aleatoria()

    return semilla_partida_aleatoria()
