#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Atajos de teclado en menús y partida.

Resumen:
  Enter     → avanzar / opción por defecto (en pregunta: respuesta A); en pausa: continuar
  Retroceso → retroceder (menú principal: salir); en pausa: menú principal
  Esc       → pausa (barra fija)
  D         → diarios / examen del día (barra fija)
  H         → info del juego (barra fija)
  F         → feedback (barra fija; también con pausa abierta)
  O         → opciones globales (barra fija)
  1–4       → responder en pregunta
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import pygame

from Grafico.feedback_partida import evento_tecla_salta_espera

if TYPE_CHECKING:
    from Grafico.pantallas import Pantalla
    from Grafico.ui import Boton, BotonOpcion

_TECLAS_OPCION = (
    pygame.K_1,
    pygame.K_2,
    pygame.K_3,
    pygame.K_4,
)

_TECLAS_AVANZAR = frozenset({pygame.K_RETURN, pygame.K_KP_ENTER})
_TECLAS_RETROCESO = frozenset({pygame.K_BACKSPACE})
_FASES_PARTIDA_SIN_RETROCESO = frozenset({"pregunta", "feedback"})

_TECLAS_BARRA_FIJA: dict[str, int] = {
    "pausa": pygame.K_ESCAPE,
    "diarios": pygame.K_d,
    "ranking": pygame.K_h,
    "feedback": pygame.K_f,
    "opciones": pygame.K_o,
}


def tecla_es_avanzar(key: int) -> bool:
    return key in _TECLAS_AVANZAR


def tecla_es_retroceso(key: int) -> bool:
    return key in _TECLAS_RETROCESO


def tecla_opcion_numerica(key: int) -> int | None:
    if pygame.K_1 <= key <= pygame.K_9:
        return key - pygame.K_0
    return None


def tipo_barra_fija_para_tecla(key: int) -> str | None:
    """Tipo de icono de la barra fija asociado a la tecla, o None."""
    for tipo, tecla in _TECLAS_BARRA_FIJA.items():
        if key == tecla:
            return tipo
    return None


def pantalla_campo_texto_activo(pantalla: object) -> bool:
    """True si algún campo de texto/entero de la pantalla tiene el foco."""
    for nombre, valor in vars(pantalla).items():
        if nombre.startswith("campo_") and getattr(valor, "activo", False):
            return True
    campos = getattr(pantalla, "campos_entero", None)
    if isinstance(campos, dict):
        for campo in campos.values():
            if getattr(campo, "activo", False):
                return True
    return False


def botones_menu_pantalla(pantalla: object) -> Sequence[Boton] | None:
    """Lista numerable de botones de menú (``botones`` o ``_botones_ui()``)."""
    botones = getattr(pantalla, "botones", None)
    if botones:
        return botones
    metodo = getattr(pantalla, "_botones_ui", None)
    if callable(metodo):
        return metodo()
    return None


def pulsar_boton_si_activo(boton: Boton | None) -> bool:
    if boton is not None and boton.activo:
        boton.al_pulsar()
        return True
    return False


def pulsar_boton_indice(botones: Sequence[Boton], indice: int) -> bool:
    """Tecla 1–9 solo dispara si el botón de esa posición está activo (blanco)."""
    if not (1 <= indice <= len(botones)):
        return False
    return pulsar_boton_si_activo(botones[indice - 1])


def pulsar_primer_boton(pantalla: object, *nombres: str) -> bool:
    for nombre in nombres:
        if pulsar_boton_si_activo(getattr(pantalla, nombre, None)):
            return True
    return False


def pantalla_en_partida_activa(pantalla: object) -> bool:
    metodo = getattr(pantalla, "en_partida_activa", None)
    if callable(metodo):
        try:
            return bool(metodo())
        except TypeError:
            pass
    return getattr(pantalla, "fase", None) is not None


def navegacion_global_bloqueada_en_partida(
    pantalla: object,
    *,
    menu_pausa_abierto: bool,
) -> bool:
    """H, F y retroceso de menú no deben sacar al jugador de una partida en curso."""
    if menu_pausa_abierto:
        return False
    return pantalla_en_partida_activa(pantalla)


def atajo_avanzar_pantalla(pantalla: Pantalla) -> bool:
    metodo = getattr(pantalla, "atajo_avanzar", None)
    if callable(metodo):
        return bool(metodo())
    return pulsar_primer_boton(
        pantalla,
        "boton_empezar",
        "boton_siguiente",
        "boton_continuar",
        "boton_enviar",
    )


def atajo_retroceder_pantalla(pantalla: Pantalla) -> bool:
    metodo = getattr(pantalla, "atajo_retroceder", None)
    if callable(metodo):
        return bool(metodo())
    return pulsar_primer_boton(pantalla, "boton_volver", "boton_atras")


def atajo_opcion_numerica_pantalla(pantalla: Pantalla, indice: int) -> bool:
    metodo = getattr(pantalla, "atajo_opcion_numerica", None)
    if callable(metodo):
        return bool(metodo(indice))
    botones = botones_menu_pantalla(pantalla)
    if not botones:
        return False
    return pulsar_boton_indice(botones, indice)


def manejar_teclado_partida(
    evento: pygame.event.Event,
    *,
    fase: str,
    botones_opcion: Sequence[BotonOpcion],
    on_responder: Callable[[str], None],
    on_continuar: Callable[[], None],
) -> bool:
    """Teclas de partida: 1–4, Enter (=1ª opción) en pregunta; Enter/Espacio en feedback."""
    if evento.type != pygame.KEYDOWN:
        return False
    if fase == "pregunta":
        return _manejar_teclado_fase_pregunta(
            evento, botones_opcion=botones_opcion, on_responder=on_responder
        )
    if fase == "feedback" and evento_tecla_salta_espera(evento):
        on_continuar()
        return True
    return False


def _manejar_teclado_fase_pregunta(
    evento: pygame.event.Event,
    *,
    botones_opcion: Sequence[BotonOpcion],
    on_responder: Callable[[str], None],
) -> bool:
    if tecla_es_avanzar(evento.key):
        if botones_opcion and botones_opcion[0].activo:
            on_responder(botones_opcion[0].letra)
        return True
    for indice, tecla in enumerate(_TECLAS_OPCION):
        if evento.key != tecla:
            continue
        if indice >= len(botones_opcion):
            return True
        if not botones_opcion[indice].activo:
            return True
        on_responder(botones_opcion[indice].letra)
        return True
    return False
