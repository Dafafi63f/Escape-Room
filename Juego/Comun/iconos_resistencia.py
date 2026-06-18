#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emojis y textos de ayuda para objetos y eventos del modo resistencia."""

from __future__ import annotations

from Comun.powerups_resistencia import POWERUPS, etiqueta_powerup

EMOJI_POWERUP: dict[str, str] = {
    "fifty_fifty": "✂️",
    "bomba": "💣",
    "skip": "⏭️",
    "tiempo_extra": "⏱️",
    "escudo": "🛡️",
    "cambio": "🔄",
}

_SEPARADOR_EMOJI = "  "


def emoji_powerup(powerup_id: str) -> str:
    return EMOJI_POWERUP.get(powerup_id, "🎁")


def etiqueta_powerup_con_emoji(powerup_id: str) -> str:
    return prefijar_emoji(etiqueta_powerup(powerup_id), emoji_powerup(powerup_id))


def prefijar_emoji(texto: str, emoji: str) -> str:
    if not emoji or not texto.strip():
        return texto
    if texto.startswith(emoji):
        return texto
    return f"{emoji}{_SEPARADOR_EMOJI}{texto}"


def separar_emoji_mensaje(mensaje: str) -> tuple[str, str]:
    """Devuelve (emoji, resto) si el mensaje lleva emoji al inicio."""
    if _SEPARADOR_EMOJI in mensaje:
        emoji, resto = mensaje.split(_SEPARADOR_EMOJI, 1)
        if resto and len(emoji) <= 4:
            return emoji.strip(), resto.strip()
    return "", mensaje


def emoji_evento_etiqueta(etiqueta: str) -> str:
    if etiqueta.startswith("Relámpago"):
        return "⚡"
    if etiqueta.startswith("Niebla:"):
        if "enunciado" in etiqueta:
            return "🙈"
        return "🌫️"
    if etiqueta == "Doble puntos":
        return "✨"
    if etiqueta == "Triple puntos":
        return "💎"
    if etiqueta == "Pregunta difícil":
        return "🔥"
    if etiqueta == "Pregunta extra difícil":
        return "☠️"
    if etiqueta.startswith("Bloque:"):
        return "📚"
    if "Maldición" in etiqueta:
        return "💀"
    if "Hito racha" in etiqueta:
        return "🏅"
    if "Doble o nada" in etiqueta or "Triple arriesgado" in etiqueta:
        return "🎰"
    return "🎲"


def descripcion_evento_etiqueta(etiqueta: str) -> str:
    if etiqueta.startswith("Relámpago"):
        seg = etiqueta.split(":")[-1].strip() if ":" in etiqueta else ""
        return f"Menos tiempo para responder{f' ({seg})' if seg else ''}."
    if etiqueta.startswith("Niebla:") and "enunciado" in etiqueta:
        return "Solo verás parte del enunciado de la pregunta."
    if etiqueta.startswith("Niebla:"):
        return "El juego ocultará una o más respuestas incorrectas."
    if etiqueta in {"Doble puntos", "Triple puntos"}:
        return f"Si aciertas, sumarás {etiqueta.lower()} en esta pregunta."
    if etiqueta == "Pregunta difícil":
        return "Esta pregunta será más difícil de lo habitual en esta fase."
    if etiqueta == "Pregunta extra difícil":
        return "Una pregunta muy exigente para esta fase de la partida."
    return etiqueta


def emoji_recompensa_etiqueta(etiqueta: str) -> str:
    if etiqueta.startswith("Objeto: "):
        nombre = etiqueta.removeprefix("Objeto: ").strip()
        for pid, (nom, _) in POWERUPS.items():
            if nom == nombre:
                return emoji_powerup(pid)
        return "🎁"
    if "Vida extra" in etiqueta:
        return "❤️"
    if "pierdes 1 vida" in etiqueta.lower():
        return "💔"
    if "máximo +1" in etiqueta or "maximo +1" in etiqueta.lower():
        return "💖"
    if "máximo −1" in etiqueta or ("maximo" in etiqueta.lower() and "−1" in etiqueta):
        return "🩶"
    return "🎁"


def emoji_aviso_exclusiva() -> str:
    return "⭐"
