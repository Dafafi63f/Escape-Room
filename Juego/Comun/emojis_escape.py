#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emojis y capas de iconos del modo escape room.

Cada símbolo tiene una capa fija; el tooltip es genérico por capa y las
variantes concretas van en la descripción de la carta de puerta.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "ALTERNATIVAS_EMOJI_NIEBLA",
    "ALTERNATIVAS_EMOJI_PUERTA",
    "CAPA_EVENTO_ESCAPE",
    "CAPAS_ICONO_PROTEGIDO_ESCAPE",
    "CapaIconoEscape",
    "MAX_ICONOS_CARTA_PUERTA",
    "EMOJI_BOTIN_ESCAPE",
    "EMOJI_RECOMPENSA_VIDA",
    "EMOJI_RECOMPENSA_VIDA_MAX",
    "EMOJI_CRONO_BLOQUE",
    "EMOJI_CRONO_DOBLE",
    "EMOJI_CRONO_PREGUNTA",
    "EMOJI_DESCANSO",
    "EMOJI_TIENDA",
    "EMOJI_DIF_BALANCEADO",
    "EMOJI_DIF_DIFICIL",
    "EMOJI_DIF_FACIL",
    "EMOJI_DIF_MEDIA",
    "EMOJI_DOBLE_PUNTOS",
    "EMOJI_JEFE",
    "EMOJI_MIX_MATERIA",
    "EMOJI_MODO_ESCAPE",
    "EMOJI_NIEBLA_AMBOS",
    "EMOJI_NIEBLA_ENUNCIADO",
    "EMOJI_NIEBLA_OPCIONES",
    "EMOJI_PUERTA_GRUPO",
    "EMOJI_PUERTA_MATERIA",
    "EMOJI_TIPO_CALCULO",
    "EMOJI_TIPO_TEORIA",
    "EMOJI_TRIPLE_PUNTOS",
    "EMOJI_EVENTO_ESCAPE",
    "TOOLTIP_BOTIN",
    "TOOLTIP_BOTIN_DESCANSO",
    "PERFIL_CAPA_TIPO_PREGUNTA",
    "capa_evento_escape",
    "emoji_dificultad_perfil",
]


class CapaIconoEscape(str, Enum):
    """Capas de iconos en cartas y UI del escape room."""

    TIPO_PUERTA = "tipo_puerta"
    DIFICULTAD = "dificultad"
    TIPO_PREGUNTA = "tipo_pregunta"
    TIEMPO = "tiempo"
    NIEBLA = "niebla"
    PUNTOS = "puntos"
    BOTIN = "botin"
    DESCANSO = "descanso"
    TIENDA = "tienda"
    JEFE = "jefe"
    UI_MODO = "ui_modo"
    UI_BARRA = "ui_barra"


MAX_ICONOS_CARTA_PUERTA = 5

CAPAS_ICONO_PROTEGIDO_ESCAPE = frozenset({
    CapaIconoEscape.TIPO_PUERTA,
    CapaIconoEscape.DIFICULTAD,
    CapaIconoEscape.BOTIN,
    CapaIconoEscape.DESCANSO,
    CapaIconoEscape.TIENDA,
})


# --- Tipo de puerta (contenido) ---
EMOJI_PUERTA_MATERIA = "📕"
EMOJI_PUERTA_GRUPO = "🗃️"

# --- Capa dificultad (puerta de materia) ---
EMOJI_DIF_FACIL = "🟢"
EMOJI_DIF_MEDIA = "🟡"
EMOJI_DIF_DIFICIL = "🔴"
EMOJI_DIF_BALANCEADO = "⚖️"
EMOJI_MIX_MATERIA = "🔀"

# --- Capa tipo de pregunta ---
EMOJI_TIPO_TEORIA = "🔤"
EMOJI_TIPO_CALCULO = "🔢"

# --- Rasgos de puerta (catálogo) ---
EMOJI_DESCANSO = "💤"
EMOJI_TIENDA = "🛒"
EMOJI_BOTIN_ESCAPE = "🎁"
EMOJI_RECOMPENSA_VIDA = "❤️"
EMOJI_RECOMPENSA_VIDA_MAX = "💖"
EMOJI_NIEBLA_ENUNCIADO = "🍃"
EMOJI_NIEBLA_OPCIONES = "💨"
EMOJI_NIEBLA_AMBOS = "🌪️"
EMOJI_CRONO_PREGUNTA = "⏱️"
EMOJI_CRONO_BLOQUE = "⏰"
EMOJI_CRONO_DOBLE = "⏲️"
EMOJI_DOBLE_PUNTOS = "✨"
EMOJI_TRIPLE_PUNTOS = "💫"

# --- Jefe, menú ---
EMOJI_JEFE = "👑"
EMOJI_MODO_ESCAPE = "🔐"

# Tooltips fijos por capa de contenido
TOOLTIP_PUERTA_MATERIA = "Preguntas de una materia concreta del plan."
TOOLTIP_PUERTA_GRUPO = (
    "Preguntas de varias materias de un mismo bloque temático del plan."
)
TOOLTIP_DIF_BALANCEADO = "Cualquier dificultad de la materia."
TOOLTIP_DIF_FACIL = "Solo preguntas fáciles."
TOOLTIP_DIF_MEDIA = "Solo preguntas de dificultad media."
TOOLTIP_DIF_DIFICIL = "Solo preguntas difíciles."
TOOLTIP_MIX_MATERIA = "Dos niveles de dificultad en la materia."
TOOLTIP_TIPO_TEORIA = "Solo preguntas teóricas."
TOOLTIP_TIPO_CALCULO = "Solo preguntas de cálculo."
TOOLTIP_BOTIN = "Recompensa al superar la puerta sin fallar."
TOOLTIP_BOTIN_DESCANSO = "Recompensa al elegir esta puerta de descanso."
TOOLTIP_TIENDA = "Compra objetos con puntos arcade."

CAPA_EVENTO_ESCAPE: dict[str, CapaIconoEscape] = {
    "puerta_materia": CapaIconoEscape.TIPO_PUERTA,
    "puerta_grupo": CapaIconoEscape.TIPO_PUERTA,
    "descanso": CapaIconoEscape.DESCANSO,
    "tienda": CapaIconoEscape.TIENDA,
    "botin": CapaIconoEscape.BOTIN,
    "botin_corazon_max": CapaIconoEscape.BOTIN,
    "niebla_opciones": CapaIconoEscape.NIEBLA,
    "cronometro_pregunta": CapaIconoEscape.TIEMPO,
    "cronometro_bloque": CapaIconoEscape.TIEMPO,
    "cronometro_doble": CapaIconoEscape.TIEMPO,
    "doble_puntos": CapaIconoEscape.PUNTOS,
    "triple_puntos": CapaIconoEscape.PUNTOS,
}

EMOJI_EVENTO_ESCAPE: dict[str, str] = {
    "puerta_materia": EMOJI_PUERTA_MATERIA,
    "puerta_grupo": EMOJI_PUERTA_GRUPO,
    "descanso": EMOJI_DESCANSO,
    "tienda": EMOJI_TIENDA,
    "botin": EMOJI_BOTIN_ESCAPE,
    "botin_corazon_max": EMOJI_BOTIN_ESCAPE,
    "niebla_opciones": EMOJI_NIEBLA_OPCIONES,
    "cronometro_bloque": EMOJI_CRONO_BLOQUE,
    "cronometro_pregunta": EMOJI_CRONO_PREGUNTA,
    "cronometro_doble": EMOJI_CRONO_DOBLE,
    "doble_puntos": EMOJI_DOBLE_PUNTOS,
    "triple_puntos": EMOJI_TRIPLE_PUNTOS,
}

PERFIL_CAPA_DIFICULTAD: dict[str, tuple[CapaIconoEscape, str]] = {
    "balanceado": (CapaIconoEscape.DIFICULTAD, EMOJI_DIF_BALANCEADO),
    "facil": (CapaIconoEscape.DIFICULTAD, EMOJI_DIF_FACIL),
    "media": (CapaIconoEscape.DIFICULTAD, EMOJI_DIF_MEDIA),
    "dificil": (CapaIconoEscape.DIFICULTAD, EMOJI_DIF_DIFICIL),
    "mix_facil_media": (CapaIconoEscape.DIFICULTAD, EMOJI_MIX_MATERIA),
    "mix_facil_dificil": (CapaIconoEscape.DIFICULTAD, EMOJI_MIX_MATERIA),
    "mix_media_dificil": (CapaIconoEscape.DIFICULTAD, EMOJI_MIX_MATERIA),
}

PERFIL_CAPA_TIPO_PREGUNTA: dict[str, tuple[CapaIconoEscape, str]] = {
    "teoria": (CapaIconoEscape.TIPO_PREGUNTA, EMOJI_TIPO_TEORIA),
    "calculo": (CapaIconoEscape.TIPO_PREGUNTA, EMOJI_TIPO_CALCULO),
}

_IDS_PERFIL_MIX_MATERIA = frozenset({
    "mix_facil_media",
    "mix_facil_dificil",
    "mix_media_dificil",
})

# Alternativas guardadas (no activas; cambiar EMOJI_PUERTA_* arriba si se adoptan).
ALTERNATIVAS_EMOJI_PUERTA: dict[str, tuple[str, ...]] = {
    "materia": ("🎓", "📚", "🏷️", "📖", "🎯", "🔬", "📌"),
    "grupo": ("🗂️", "🧩", "🌐", "📦", "🔗", "🏛️", "🎛️"),
}

# Alternativas guardadas (niebla enunciado/ambos inactivos; catálogo solo niebla_opciones).
ALTERNATIVAS_EMOJI_NIEBLA: dict[str, tuple[str, ...]] = {
    "enunciado": ("🌬️", "💨", "🪶", "📝"),
    "opciones": ("🌬️", "🌀", "🎭", "🙈"),
    "ambos": ("🌀", "⛈️", "☁️"),
}

# UI barra de partida (definidos en linea_estado_ui; referencia cruzada).
EMOJIS_UI_BARRA_ESCAPE: dict[str, str] = {
    "sala": "🗺️",
    "pregunta_puerta": "📝",
    "vidas": "❤️",
    "tiempo_total": "⏰",
    "tiempo_pregunta": "⏱️",
    "puntos": "⭐",
}


def capa_evento_escape(evento_id: str) -> CapaIconoEscape | None:
    return CAPA_EVENTO_ESCAPE.get(evento_id)


def emoji_dificultad_perfil(perfil_id: str | None) -> str:
    if perfil_id and perfil_id in PERFIL_CAPA_DIFICULTAD:
        return PERFIL_CAPA_DIFICULTAD[perfil_id][1]
    return EMOJI_DIF_BALANCEADO
