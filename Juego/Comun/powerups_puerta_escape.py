#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Alcance y reglas de powerups del escape room.

Inventario de pregunta: un objeto «de slot» por pregunta (bomba, 50/50, escudo…).
Saltar y Cambio no ocupan ese slot: al usarlos cambias de pregunta y se desbloquea
todo; si ya usaste otro objeto en la misma pregunta, no puedes Saltar ni Cambiar.

Inventario de sala (ids distintos): reroll, limpieza de maldiciones y salto de sala;
se usan en la pantalla de elección de puertas.

El sello de purga solo existe en resistencia (``limpieza_maldiciones`` lo sustituye en escape).
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from Comun.objetos_partida import (
    EstadoInventarioEscape,
    MENSAJE_POWERUP_YA_USADO_ESCAPE,
    POWERUPS,
    POWERUPS_INCOMPATIBLES_EN_PREGUNTA,
    POWERUPS_MULTI_USO_PREGUNTA,
    etiqueta_powerup,
    powerups_usados_slot,
    slot_powerup_ocupado,
)

if TYPE_CHECKING:
    from Comun.escape_room import PuertaEscape


class AlcancePowerupEscape(str, Enum):
    PREGUNTA = "pregunta"
    SALA = "sala"


POWERUPS_INVENTARIO_SALA_ESCAPE = frozenset({
    "reroll_puertas",
    "limpieza_maldiciones",
    "salto_sala",
})

_ALCANCE_ESCAPE: dict[str, AlcancePowerupEscape] = {
    pid: AlcancePowerupEscape.SALA for pid in POWERUPS_INVENTARIO_SALA_ESCAPE
}


def alcance_powerup_escape(articulo_id: str) -> AlcancePowerupEscape:
    return _ALCANCE_ESCAPE.get(articulo_id, AlcancePowerupEscape.PREGUNTA)


def es_powerup_inventario_puerta_escape(articulo_id: str) -> bool:
    """Powerups del inventario de sala (bolsa ``inventario_puerta``)."""
    return articulo_id in POWERUPS_INVENTARIO_SALA_ESCAPE


def es_powerup_preparacion_puerta_escape(articulo_id: str) -> bool:
    return False


def es_powerup_sala_escape(articulo_id: str) -> bool:
    return articulo_id in POWERUPS_INVENTARIO_SALA_ESCAPE


def items_inventario_puerta_para_modo(
    inventario: EstadoInventarioEscape,
    modo: str,
) -> list[tuple[str, int]]:
    """Filas visibles del inventario de sala según la fase actual."""
    if modo != "sala":
        return []
    return [
        (aid, n)
        for aid, n in inventario.items_puerta()
        if n > 0 and aid in POWERUPS_INVENTARIO_SALA_ESCAPE
    ]


def hint_alcance_powerup_escape(articulo_id: str) -> str | None:
    """Texto breve para tooltip (solo si el alcance no es el habitual)."""
    if es_powerup_sala_escape(articulo_id):
        return "Inventario de sala: úsalo al elegir puerta."
    return None


def iniciar_sala_escape(inventario: EstadoInventarioEscape) -> None:
    """Al entrar en una sala nueva (pantalla de puertas)."""
    del inventario


def iniciar_puerta_escape(inventario: EstadoInventarioEscape) -> None:
    """Al entrar en un bloque de preguntas de una puerta nueva."""
    inventario.powerups_activados_en_puerta.clear()


def _hay_puertas_malditas(puertas: tuple[PuertaEscape, ...] | None) -> bool:
    if not puertas:
        return False
    return any(p.modificadores.fin_partida_si_fallo for p in puertas)


def puede_usar_powerup_escape(
    articulo_id: str,
    inventario: EstadoInventarioEscape,
    puerta: PuertaEscape | None,
    *,
    pregunta_idx: int,
    modo: str,
    puertas_sala: tuple[PuertaEscape, ...] | None = None,
) -> str | None:
    """Valida si el powerup puede usarse ahora.

    ``modo``: ``pregunta`` o ``sala`` (elección de puertas).
    """
    del pregunta_idx, puerta
    alcance = alcance_powerup_escape(articulo_id)
    if alcance == AlcancePowerupEscape.SALA:
        if modo != "sala":
            return "Este objeto es del inventario de sala (úsalo al elegir puerta)."
        if inventario.cantidad_puerta(articulo_id) <= 0:
            return "No tienes ese objeto."
        if articulo_id == "limpieza_maldiciones" and not _hay_puertas_malditas(
            puertas_sala
        ):
            return "No hay puertas malditas en esta sala."
        return None

    if modo != "pregunta":
        return "Este objeto es del inventario de pregunta."
    if inventario.cantidad_pregunta(articulo_id) <= 0:
        return "No tienes ese objeto."
    return puede_usar_powerup_en_pregunta_escape(
        articulo_id, inventario.powerups_usados_en_pregunta
    )


def puede_usar_powerup_en_pregunta_escape(
    powerup_id: str,
    usados: set[str],
) -> str | None:
    """Escape: un slot por pregunta; Saltar/Cambio no lo ocupan pero sí lo respetan."""
    if powerup_id in POWERUPS_MULTI_USO_PREGUNTA:
        if slot_powerup_ocupado(usados):
            return MENSAJE_POWERUP_YA_USADO_ESCAPE
        return None
    if slot_powerup_ocupado(usados):
        return MENSAJE_POWERUP_YA_USADO_ESCAPE
    if powerup_id in usados:
        if powerup_id in POWERUPS:
            return f"Ya usaste {etiqueta_powerup(powerup_id)} en esta pregunta."
        return "Ya usaste este objeto en esta pregunta."
    incompatibles = POWERUPS_INCOMPATIBLES_EN_PREGUNTA.get(powerup_id, frozenset())
    for usado in powerups_usados_slot(usados):
        if usado in incompatibles:
            nom = etiqueta_powerup(powerup_id)
            otro = etiqueta_powerup(usado) if usado in POWERUPS else usado
            return f"No puedes combinar {nom} con {otro} en la misma pregunta."
    return None


def registrar_uso_powerup_escape(
    inventario: EstadoInventarioEscape,
    articulo_id: str,
) -> None:
    """Marca el uso según el alcance (llamar tras aplicar el efecto)."""
    if es_powerup_sala_escape(articulo_id):
        return
    if articulo_id not in POWERUPS_MULTI_USO_PREGUNTA:
        inventario.powerups_usados_en_pregunta.add(articulo_id)


def efectos_puerta_activos(inventario: EstadoInventarioEscape) -> tuple[str, ...]:
    """Etiquetas cortas para HUD (escudo armado…)."""
    partes: list[str] = []
    if inventario.escudo_activo:
        partes.append("🛡️ Escudo")
    if inventario.segunda_oportunidad_activa:
        partes.append("🔁 2.ª oportunidad")
    if inventario.doble_o_nada_activo:
        partes.append("🎲 Doble o nada")
    return tuple(partes)
