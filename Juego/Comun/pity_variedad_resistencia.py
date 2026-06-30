#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pity de variedad entre partidas cortas de resistencia (persistido en estadísticas)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from Comun.resistencia_motor import EstadoResistencia

__all__ = [
    "CATEGORIAS_VARIEDAD_RESISTENCIA",
    "PREGUNTA_HARD_PITY_EVENTO_SI_NO_RESISTENCIA",
    "PREGUNTA_SOFT_PITY_BLOQUE_RESISTENCIA",
    "PREGUNTA_SOFT_PITY_MALDICION_RESISTENCIA",
    "PityVariedadResistencia",
    "cargar_pity_variedad_resistencia",
    "debe_forzar_bloque_resistencia",
    "debe_forzar_evento_si_no_resistencia",
    "guardar_pity_variedad_resistencia",
    "min_pregunta_jefe_resistencia",
    "preguntas_hard_pity_jefe_resistencia",
    "preguntas_hard_pity_maldicion_resistencia",
    "registrar_variedad_resistencia",
    "registrar_variedad_resistencia_partida",
    "umbral_prob_evento_si_no_resistencia",
]

CATEGORIAS_VARIEDAD_RESISTENCIA: tuple[str, ...] = (
    "escalada_hostil",
    "escalada_buena",
    "bloque",
    "jefe",
    "maldicion",
    "evento_si_no",
)

PREGUNTA_SOFT_PITY_MALDICION_RESISTENCIA = 28
PREGUNTA_SOFT_PITY_BLOQUE_RESISTENCIA = 14
PREGUNTA_HARD_PITY_EVENTO_SI_NO_RESISTENCIA = 11

_PITY_BOOST_POR_PARTIDA_SIN = 0.34
_PITY_MAX_BOOST_CROSS = 0.55


@dataclass
class PityVariedadResistencia:
    """Partidas seguidas sin ver cada categoría; sube pesos al iniciar la siguiente."""

    partidas: int = 0
    sin_por_categoria: dict[str, int] = field(default_factory=dict)

    def partidas_sin(self, categoria: str) -> int:
        return int(self.sin_por_categoria.get(categoria, 0))

    def peso_boost(self, categoria: str) -> float:
        return 1.0 + self.partidas_sin(categoria) * _PITY_BOOST_POR_PARTIDA_SIN

    def boost_prob(self, categoria: str) -> float:
        return min(
            _PITY_MAX_BOOST_CROSS,
            self.partidas_sin(categoria) * (_PITY_BOOST_POR_PARTIDA_SIN * 0.45),
        )

    def registrar_partida(self, visto: set[str] | frozenset[str]) -> None:
        self.partidas += 1
        for cat in CATEGORIAS_VARIEDAD_RESISTENCIA:
            if cat in visto:
                self.sin_por_categoria[cat] = 0
            else:
                self.sin_por_categoria[cat] = self.partidas_sin(cat) + 1

    def a_dict(self) -> dict[str, Any]:
        return {
            "partidas": self.partidas,
            "sin_por_categoria": dict(self.sin_por_categoria),
        }

    @classmethod
    def desde_dict(cls, datos: dict[str, Any] | None) -> PityVariedadResistencia:
        if not isinstance(datos, dict):
            return cls()
        sin_raw = datos.get("sin_por_categoria")
        sin: dict[str, int] = {}
        if isinstance(sin_raw, dict):
            for cat in CATEGORIAS_VARIEDAD_RESISTENCIA:
                if cat in sin_raw:
                    try:
                        sin[cat] = max(0, int(sin_raw[cat]))
                    except (TypeError, ValueError):
                        sin[cat] = 0
        try:
            partidas = max(0, int(datos.get("partidas", 0)))
        except (TypeError, ValueError):
            partidas = 0
        return cls(partidas=partidas, sin_por_categoria=sin)


def _cargar_estadisticas_raw() -> dict[str, Any]:
    from Comun.estadisticas_jugador import resolver_path_estadisticas_jugador

    path = resolver_path_estadisticas_jugador()
    if not path.is_file():
        return {}
    try:
        datos = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return datos if isinstance(datos, dict) else {}


def _guardar_estadisticas_raw(datos: dict[str, Any]) -> None:
    from Comun.estadisticas_jugador import resolver_path_estadisticas_jugador

    path = resolver_path_estadisticas_jugador()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def cargar_pity_variedad_resistencia() -> PityVariedadResistencia:
    datos = _cargar_estadisticas_raw()
    return PityVariedadResistencia.desde_dict(datos.get("resistencia_variedad"))


def guardar_pity_variedad_resistencia(pity: PityVariedadResistencia) -> None:
    datos = _cargar_estadisticas_raw()
    datos["resistencia_variedad"] = pity.a_dict()
    _guardar_estadisticas_raw(datos)


def registrar_variedad_resistencia(er: EstadoResistencia, categoria: str) -> None:
    if categoria in CATEGORIAS_VARIEDAD_RESISTENCIA:
        er.variedad_vista.add(categoria)


def registrar_variedad_resistencia_partida(
    er: EstadoResistencia,
    eventos_escalada: tuple[object, ...] | None = None,
) -> None:
    """Actualiza el pity entre partidas con lo visto en la sesión."""
    from Comun.resistencia_partida import kind_de_evento_resistencia

    visto = set(er.variedad_vista)
    if eventos_escalada:
        for evento in eventos_escalada:
            kind = kind_de_evento_resistencia(evento)
            if kind in ("relampago", "opciones_ocultas"):
                visto.add("escalada_hostil")
            elif kind == "doble":
                visto.add("escalada_buena")
    if not hasattr(er, "pity_variedad") or er.pity_variedad is None:
        er.pity_variedad = cargar_pity_variedad_resistencia()
    er.pity_variedad.registrar_partida(visto)
    guardar_pity_variedad_resistencia(er.pity_variedad)


def preguntas_hard_pity_maldicion_resistencia(
    pity_variedad: PityVariedadResistencia | None,
) -> int:
    from Comun.maldiciones_partida import PREGUNTA_HARD_PITY_MALDICION_RESISTENCIA

    umbral = PREGUNTA_HARD_PITY_MALDICION_RESISTENCIA
    if pity_variedad is None:
        return umbral
    sin = pity_variedad.partidas_sin("maldicion")
    if sin >= 2:
        return min(umbral, 22)
    if sin >= 1:
        return min(umbral, 32)
    return umbral


def min_pregunta_jefe_resistencia(
    pity_variedad: PityVariedadResistencia | None,
) -> int:
    from Comun.jefe_partida import PREGUNTA_MIN_JEFE_RESISTENCIA

    if pity_variedad is not None and pity_variedad.partidas_sin("jefe") >= 2:
        return min(PREGUNTA_MIN_JEFE_RESISTENCIA, 15)
    return PREGUNTA_MIN_JEFE_RESISTENCIA


def preguntas_hard_pity_jefe_resistencia(
    pity_variedad: PityVariedadResistencia | None,
) -> int:
    from Comun.jefe_partida import PREGUNTAS_HARD_PITY_JEFE_RESISTENCIA

    umbral = PREGUNTAS_HARD_PITY_JEFE_RESISTENCIA
    if pity_variedad is None:
        return umbral
    sin = pity_variedad.partidas_sin("jefe")
    if sin >= 2:
        return min(umbral, 17)
    if sin >= 1:
        return min(umbral, 19)
    return umbral


def debe_forzar_bloque_resistencia(er: EstadoResistencia) -> bool:
    return er.preguntas_sin_bloque >= PREGUNTA_SOFT_PITY_BLOQUE_RESISTENCIA


def debe_forzar_evento_si_no_resistencia(er: EstadoResistencia) -> bool:
    return er.preguntas_sin_evento_si_no >= PREGUNTA_HARD_PITY_EVENTO_SI_NO_RESISTENCIA


def umbral_prob_evento_si_no_resistencia(
    er: EstadoResistencia,
    prob_base: float,
) -> float:
    prob = prob_base
    if er.pity_variedad is not None:
        prob += er.pity_variedad.boost_prob("evento_si_no")
    if debe_forzar_evento_si_no_resistencia(er):
        return 1.0
    from Comun.eventos_partida import PITY_INC_EVENTO_SI_NO, PITY_MAX_BOOST_EVENTO_SI_NO

    boost = min(
        PITY_MAX_BOOST_EVENTO_SI_NO,
        er.preguntas_sin_evento_si_no * PITY_INC_EVENTO_SI_NO,
    )
    return min(0.98, prob + boost)
