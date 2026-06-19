#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atajos de ``textos_ui`` para la consola (fondo oscuro, un emoji al inicio)."""

from __future__ import annotations

from Comun.linea_estado_ui import consola_soporta_emoji
from Comun.textos_ui import (
    BTN_ABANDONAR,
    BTN_ATRAS,
    BTN_CONTINUAR,
    BTN_CONTINUAR_PARTIDA,
    BTN_EMPEZAR,
    BTN_GUARDAR_INFORME,
    BTN_PANTALLA_TITULO,
    BTN_SALIR_PROGRAMA,
    BTN_SIGUIENTE,
    BTN_VER_RANKING,
    BTN_VOLVER,
    BTN_VOLVER_MENU,
    ContextoUi,
    EmojiPar,
    PosicionEmoji,
    con_emoji as _con_emoji,
    etiqueta as _etiqueta,
    etiqueta_campo as _etiqueta_campo,
    info_dataset as _info_dataset,
    mensaje_feedback as _mensaje_feedback,
    nombre_paso as _nombre_paso,
    subtitulo as _subtitulo,
    titulo_flexible as _titulo_flexible,
    titulo_pantalla as _titulo_pantalla,
    posicion_emoji_navegacion,
    OpcionMenuPrincipal,
    resolver_emoji,
)

_CONTEXTO: ContextoUi = "consola"

__all__ = [
    "BTN_ABANDONAR",
    "BTN_ATRAS",
    "BTN_CONTINUAR",
    "BTN_CONTINUAR_PARTIDA",
    "BTN_EMPEZAR",
    "BTN_GUARDAR_INFORME",
    "BTN_PANTALLA_TITULO",
    "BTN_SALIR_PROGRAMA",
    "BTN_SIGUIENTE",
    "BTN_VER_RANKING",
    "BTN_VOLVER",
    "BTN_VOLVER_MENU",
    "banner",
    "btn",
    "campo",
    "con_emoji",
    "etiqueta",
    "etiqueta_opcion_menu",
    "feedback",
    "info_dataset",
    "nombre_paso",
    "subtitulo",
    "titulo",
    "usar_emojis",
]


def usar_emojis() -> bool:
    return consola_soporta_emoji()


def _posicion_etiqueta(emoji: str | EmojiPar) -> PosicionEmoji:
    pos = posicion_emoji_navegacion(emoji, contexto=_CONTEXTO)
    return "inicio" if pos == "simetrico" else pos


def con_emoji(texto: str, emoji: str | EmojiPar) -> str:
    return _con_emoji(
        texto,
        emoji,
        usar_emojis=usar_emojis(),
        posicion=_posicion_etiqueta(emoji),
        contexto=_CONTEXTO,
    )


def etiqueta(texto: str, emoji: str | EmojiPar) -> str:
    return _etiqueta(
        texto,
        emoji,
        usar_emojis=usar_emojis(),
        posicion=_posicion_etiqueta(emoji),
        contexto=_CONTEXTO,
    )


def titulo(texto: str) -> str:
    return _titulo_flexible(
        texto, usar_emojis=usar_emojis(), simetrico=False, contexto=_CONTEXTO
    )


def subtitulo(texto: str, emoji: str | EmojiPar = "📋") -> str:
    return _subtitulo(
        texto, emoji, usar_emojis=usar_emojis(), contexto=_CONTEXTO
    )


def campo(clave: str, texto: str) -> str:
    return _etiqueta_campo(
        clave, texto, usar_emojis=usar_emojis(), contexto=_CONTEXTO
    )


def feedback(mensaje: str) -> str:
    return _mensaje_feedback(mensaje, usar_emojis=usar_emojis())


def nombre_paso(nombre: str) -> str:
    return _nombre_paso(nombre, usar_emojis=usar_emojis(), contexto=_CONTEXTO)


def info_dataset(num_preguntas: int, num_materias: int) -> str:
    return _info_dataset(
        num_preguntas, num_materias, usar_emojis=usar_emojis(), contexto=_CONTEXTO
    )


def btn(par: tuple[str, str | EmojiPar]) -> str:
    return etiqueta(par[0], par[1])


def etiqueta_opcion_menu(op: OpcionMenuPrincipal) -> str:
    """Etiqueta de opción del menú principal (un emoji al inicio)."""
    if not usar_emojis():
        return op.texto
    return f"{resolver_emoji(op.emoji, contexto=_CONTEXTO)} {op.texto}"


def banner(texto: str) -> str:
    """Línea tipo «=== TÍTULO ===» con emoji si aplica."""
    return f"=== {titulo(texto)} ==="
