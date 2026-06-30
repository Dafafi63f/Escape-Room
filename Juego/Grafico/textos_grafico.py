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
    BTN_EXAMEN_DIRIGIDO,
    BTN_PANTALLA_TITULO,
    BTN_SALIR_PROGRAMA,
    BTN_SIGUIENTE,
    BTN_BORRAR_TXT_INFORMES,
    BTN_VACIAR_PREFERENCIAS,
    BTN_VACIAR_ESTADISTICAS,
    BTN_VOLVER,
    BTN_VOLVER_MENU,
    ContextoUi,
    EmojiPar,
    PosicionEmoji,
    con_emoji as _con_emoji,
    emoji_icono as _emoji_icono,
    etiqueta as _etiqueta,
    mensaje_feedback as _mensaje_feedback,
    posicion_emoji_navegacion,
    OpcionMenuPrincipal,
)

_CONTEXTO: ContextoUi = "grafico"

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
    "BTN_EXAMEN_DIRIGIDO",
    "BTN_PANTALLA_TITULO",
    "BTN_SALIR_PROGRAMA",
    "BTN_SIGUIENTE",
    "BTN_BORRAR_TXT_INFORMES",
    "BTN_VACIAR_PREFERENCIAS",
    "BTN_VACIAR_ESTADISTICAS",
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
    "texto_controles_juego_grafico",
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


def subtitulo(texto: str, _emoji: str | EmojiPar = "📋") -> str:
    return texto.strip()


def etiqueta_campo(_clave: str, texto: str) -> str:
    return texto


def info_dataset(num_preguntas: int, num_materias: int) -> str:
    return f"{num_preguntas} preguntas  {num_materias} materias"


def texto_controles_juego_grafico() -> str:
    """Texto informativo de ratón y atajos de teclado (pantalla Info)."""
    return (
        "Ratón: navegar, pulsar botones y elegir respuestas.\n"
        "\n"
        "Teclado en partida y menús:\n"
        "· Durante una partida: solo Esc (pausa) y 1–4 para responder; "
        "el resto de la barra y atajos D/H/F/O/retroceso quedan bloqueados hasta pausar.\n"
        "· En menús y configuración: barra completa y atajos D, H, F, O, retroceso, 1–9.\n"
        "· Barra fija (solo si el icono está activo/blanco; pulsar otra vez cierra ese menú):\n"
        "  Esc — pausa (otra vez en pausa: salir del programa)  D — diarios  H — info  "
        "F — feedback  O — opciones.\n"
        "· Con opciones abiertas: Esc abre la pausa (guarda antes los cambios).\n"
        "· 1–4 — responder (opción 1 a 4 en pantalla).\n"
        "· Enter — avanzar (en pregunta: primera opción); en pausa: continuar.\n"
        "· Retroceso (tecla de borrar texto) — volver atrás; en menú principal: salir del juego; "
        "en pausa: menú principal.\n"
        "· En el menú de pausa, Esc o el icono de pausa otra vez — salir del programa.\n"
        "· 1–9 — elegir la opción numerada en menús con lista.\n"
        "\n"
        "En campos de texto (nombre, feedback…): la misma tecla borra caracteres; "
        "no retrocede de pantalla mientras el campo tiene el foco."
    )


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
