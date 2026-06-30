#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emojis del modo partida (objetos, ofertas resistencia, recompensas gratis).

Un emoji por tipo de efecto; evita reutilizar el mismo símbolo para mecánicas distintas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Comun.eventos_partida import EventoSiNo

# Bonificaciones (referencia única; objetos_partida importa estos valores).
EMOJI_AMULETO_PUNTOS = "🔮"
EMOJI_REFUERZO_VITAL = "❤️"

# Ofertas sí/no resistencia (sin artículo de catálogo).
EMOJI_SORPRESA_RESISTENCIA = "🎁"
EMOJI_PURGA_MALDICION = "🕯️"
EMOJI_RIESGO_PREGUNTA = "🎰"
EMOJI_RIESGO_ACIERTO = "✅"
EMOJI_RIESGO_FALLO = "❌"

# Recompensas gratis tras acierto (etiquetas de EventoRecompensaResistencia).
EMOJI_RECOMPENSA_VIDA = "❤️"
EMOJI_RECOMPENSA_VIDA_MAX_MAS = "💖"
EMOJI_RECOMPENSA_VIDA_MAX_MENOS = "🩶"
EMOJI_RECOMPENSA_PIERDE_VIDA = "💔"

# Fallback cuando no hay emoji concreto para un powerup/objeto.
EMOJI_OBJETO_DESCONOCIDO = "📦"

# Bloque de 3/5 preguntas con filtro amplio (avisos resistencia; 🎯 en escape si no es materia única).
EMOJI_BLOQUE_PREGUNTAS = "🎯"
EMOJI_BLOQUE_FILTRO_RESISTENCIA = EMOJI_BLOQUE_PREGUNTAS

_EMOJI_OFERTA_SI_NO: dict[str, str] = {
    "riesgo_pregunta": EMOJI_RIESGO_PREGUNTA,
    "vida": EMOJI_REFUERZO_VITAL,
    "amuleto": EMOJI_AMULETO_PUNTOS,
    "sorpresa": EMOJI_SORPRESA_RESISTENCIA,
    "purga_maldicion": EMOJI_PURGA_MALDICION,
}


def emoji_evento_si_no(evento: EventoSiNo) -> str:
    """Emoji del popup sí/no según tipo o artículo comprado."""
    if evento.tipo == "compra" and evento.articulo_id:
        from Comun.objetos_partida import articulo_por_id

        return articulo_por_id(evento.articulo_id).emoji
    return _EMOJI_OFERTA_SI_NO.get(evento.tipo, EMOJI_OBJETO_DESCONOCIDO)


def emoji_recompensa_por_etiqueta(etiqueta: str) -> str:
    """Emoji de aviso tras acierto u otra recompensa con etiqueta legible."""
    from Comun.objetos_partida import POWERUPS, emoji_powerup

    if etiqueta.startswith("Objeto: "):
        nombre = etiqueta.removeprefix("Objeto: ").strip()
        for pid, (nom, _) in POWERUPS.items():
            if nom == nombre:
                return emoji_powerup(pid)
        return EMOJI_OBJETO_DESCONOCIDO
    if "Amuleto arcade" in etiqueta:
        return EMOJI_AMULETO_PUNTOS
    if "Vida extra" in etiqueta:
        return EMOJI_RECOMPENSA_VIDA
    if "pierdes 1 vida" in etiqueta.lower():
        return EMOJI_RECOMPENSA_PIERDE_VIDA
    if "máximo +1" in etiqueta or "maximo +1" in etiqueta.lower():
        return EMOJI_RECOMPENSA_VIDA_MAX_MAS
    if "máximo −1" in etiqueta or ("maximo" in etiqueta.lower() and "−1" in etiqueta):
        return EMOJI_RECOMPENSA_VIDA_MAX_MENOS
    return EMOJI_OBJETO_DESCONOCIDO


# Alternativas guardadas (no activas; cambiar EMOJI_SORPRESA_RESISTENCIA arriba si se adoptan).
# 🎲 liberado: doble_o_nada, examen aleatorio, pack tienda, fallback eventos resistencia.
ALTERNATIVAS_EMOJI_SORPRESA_RESISTENCIA: tuple[str, ...] = (
    "🎲",
    "❓",
    "📦",
    "✨",
)
