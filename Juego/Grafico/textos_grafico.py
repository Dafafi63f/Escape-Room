#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atajos de ``textos_ui`` para pygame.

En gráfico los emojis van solo en botones y acciones (``etiqueta``, ``btn``).
Títulos, etiquetas de formulario y textos informativos se muestran sin emoji.
"""

from __future__ import annotations

from Comun.preferencias_grafico import emojis_habilitados
from Comun.textos_ui import (
    BTN_ABANDONAR,
    BTN_APUESTA_NO,
    BTN_APUESTA_SI,
    BTN_ATRAS,
    BTN_CONTINUAR,
    BTN_CONTINUAR_PARTIDA,
    BTN_EMPEZAR,
    BTN_ENVIAR,
    BTN_GUARDAR_INFORME,
    BTN_REPETIR_PARTIDA,
    BTN_CAMBIAR_OPCIONES,
    BTN_PANTALLA_TITULO,
    BTN_SALIR_PROGRAMA,
    BTN_SIGUIENTE,
    BTN_VER_RANKING,
    BTN_BORRAR_RANKING,
    BTN_BORRAR_TXT_INFORMES,
    BTN_VACIAR_PREFERENCIAS,
    BTN_VOLVER,
    BTN_VOLVER_MENU,
    EmojiPar,
    PosicionEmoji,
    con_emoji as _con_emoji,
    emoji_icono as _emoji_icono,
    etiqueta as _etiqueta,
    mensaje_feedback as _mensaje_feedback,
    posicion_emoji_navegacion,
    OpcionMenuPrincipal,
)

_CONTEXTO = "grafico"

__all__ = [
    "BTN_ABANDONAR",
    "BTN_APUESTA_NO",
    "BTN_APUESTA_SI",
    "BTN_ATRAS",
    "BTN_CONTINUAR",
    "BTN_CONTINUAR_PARTIDA",
    "BTN_EMPEZAR",
    "BTN_ENVIAR",
    "BTN_GUARDAR_INFORME",
    "BTN_REPETIR_PARTIDA",
    "BTN_CAMBIAR_OPCIONES",
    "BTN_PANTALLA_TITULO",
    "BTN_SALIR_PROGRAMA",
    "BTN_SIGUIENTE",
    "BTN_VER_RANKING",
    "BTN_BORRAR_RANKING",
    "BTN_BORRAR_TXT_INFORMES",
    "BTN_VACIAR_PREFERENCIAS",
    "BTN_VOLVER",
    "BTN_VOLVER_MENU",
    "btn",
    "con_emoji",
    "emoji_icono",
    "etiqueta",
    "etiqueta_campo",
    "etiqueta_menu",
    "info_dataset",
    "mensaje_feedback",
    "nombre_paso",
    "subtitulo",
    "titulo",
    "titulo_pantalla",
]


def con_emoji(
    texto: str,
    emoji: str | EmojiPar,
    *,
    posicion: PosicionEmoji | None = None,
) -> str:
    return _con_emoji(
        texto,
        emoji,
        usar_emojis=emojis_habilitados(),
        contexto=_CONTEXTO,
        posicion=posicion,
    )


def _posicion_etiqueta(emoji: str | EmojiPar) -> PosicionEmoji:
    return posicion_emoji_navegacion(emoji, contexto=_CONTEXTO)


def etiqueta(texto: str, emoji: str | EmojiPar) -> str:
    return _etiqueta(
        texto,
        emoji,
        usar_emojis=emojis_habilitados(),
        contexto=_CONTEXTO,
        posicion=_posicion_etiqueta(emoji),
    )


def etiqueta_menu(texto: str, emoji: str | EmojiPar) -> str:
    """Opción de menú vertical (p. ej. pausa): emojis simétricos en los tres botones."""
    return _etiqueta(
        texto,
        emoji,
        usar_emojis=emojis_habilitados(),
        contexto=_CONTEXTO,
        posicion="simetrico",
    )


def titulo(texto: str) -> str:
    return texto.strip()


def titulo_pantalla(texto: str) -> str:
    return texto.strip()


def subtitulo(texto: str, emoji: str | EmojiPar = "📋") -> str:
    return texto.strip()


def etiqueta_campo(clave: str, texto: str) -> str:
    return texto


def info_dataset(num_preguntas: int, num_materias: int) -> str:
    return f"{num_preguntas} preguntas · {num_materias} materias"


def mensaje_feedback(mensaje: str) -> str:
    return _mensaje_feedback(mensaje, usar_emojis=emojis_habilitados())


def nombre_paso(nombre: str) -> str:
    return nombre.strip()


def emoji_icono(clave: str) -> str:
    if not emojis_habilitados():
        return ""
    return _emoji_icono(clave, contexto=_CONTEXTO)


def btn(par: tuple[str, str | EmojiPar]) -> str:
    return etiqueta(par[0], par[1])


def etiqueta_opcion_menu(op: OpcionMenuPrincipal) -> str:
    return op.etiqueta(contexto=_CONTEXTO, usar_emojis=emojis_habilitados())
