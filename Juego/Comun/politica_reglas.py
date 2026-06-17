#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Políticas de reglas según el contexto de juego (sin E/S)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from Comun.compatibilidad_reglas_libre import sanitizar_reglas_libre
from Comun.reglas_partida import (
    ReglasPartida,
    preset_historia_examen,
    preset_historia_resistencia,
    preset_historia_reto,
)


class ContextoPartida(str, Enum):
    HISTORIA_SIMULACRO = "historia_simulacro"
    HISTORIA_RETO = "historia_reto"
    HISTORIA_RESISTENCIA = "historia_resistencia"
    LIBRE_INFINITO = "libre_infinito"
    LIBRE_UNA_PREGUNTA = "libre_una_pregunta"
    LIBRE_BLOQUE_CORTO = "libre_bloque_corto"
    LIBRE_BLOQUE_NORMAL = "libre_bloque_normal"
    FEEDBACK = "feedback"


@dataclass(frozen=True)
class PoliticaReglas:
    contexto: ContextoPartida
    reglas: ReglasPartida
    eleccion_jugador: bool
    mensaje: str


def clasificar_libre(*, modo_infinito: bool, n_preguntas: int) -> ContextoPartida:
    if modo_infinito:
        return ContextoPartida.LIBRE_INFINITO
    if n_preguntas <= 1:
        return ContextoPartida.LIBRE_UNA_PREGUNTA
    if n_preguntas <= 5:
        return ContextoPartida.LIBRE_BLOQUE_CORTO
    return ContextoPartida.LIBRE_BLOQUE_NORMAL


def _politica_fija(
    contexto: ContextoPartida,
    reglas: ReglasPartida,
    mensaje: str,
) -> PoliticaReglas:
    return PoliticaReglas(
        contexto=contexto,
        reglas=reglas,
        eleccion_jugador=False,
        mensaje=mensaje,
    )


def politica_historia_simulacro() -> PoliticaReglas:
    return _politica_fija(
        ContextoPartida.HISTORIA_SIMULACRO,
        preset_historia_examen(),
        "Examen cerrado: sin vidas ni pistas al responder; nota y corrección al final.",
    )


def politica_historia_reto() -> PoliticaReglas:
    return _politica_fija(
        ContextoPartida.HISTORIA_RETO,
        preset_historia_reto(),
        "Variante reto: 3 vidas y puntuación arcade (no es un simulacro de examen oficial).",
    )


def politica_historia_resistencia() -> PoliticaReglas:
    return _politica_fija(
        ContextoPartida.HISTORIA_RESISTENCIA,
        preset_historia_resistencia(),
        "Resistencia infinita: 3 vidas; la dificultad sube con el nº de pregunta; la racha solo bonifica puntos.",
    )


def _fusionar_tiempo_preset(base: ReglasPartida, reglas: ReglasPartida) -> ReglasPartida:
    if not reglas.tiempo_por_pregunta_seg and not reglas.tiempo_total_seg:
        return base
    return ReglasPartida(
        vidas=base.vidas,
        tiempo_por_pregunta_seg=reglas.tiempo_por_pregunta_seg,
        tiempo_total_seg=reglas.tiempo_total_seg,
        sistema_puntuacion=base.sistema_puntuacion,
        mostrar_solucion_tras_fallo=base.mostrar_solucion_tras_fallo,
        mostrar_aciertos_en_curso=base.mostrar_aciertos_en_curso,
        correccion_al_final=base.correccion_al_final,
        dificultad_progresiva=base.dificultad_progresiva,
    )


def validar_reglas(
    reglas: ReglasPartida,
    contexto: ContextoPartida,
    *,
    modo_infinito: bool = False,
    n_preguntas: int = 10,
) -> ReglasPartida:
    if contexto == ContextoPartida.HISTORIA_SIMULACRO:
        return _fusionar_tiempo_preset(preset_historia_examen(), reglas)
    if contexto == ContextoPartida.HISTORIA_RETO:
        return _fusionar_tiempo_preset(preset_historia_reto(), reglas)
    if contexto == ContextoPartida.HISTORIA_RESISTENCIA:
        return preset_historia_resistencia()
    if contexto in {
        ContextoPartida.LIBRE_INFINITO,
        ContextoPartida.LIBRE_UNA_PREGUNTA,
        ContextoPartida.LIBRE_BLOQUE_CORTO,
        ContextoPartida.LIBRE_BLOQUE_NORMAL,
    }:
        reglas = sanitizar_reglas_libre(
            reglas,
            modo_infinito=modo_infinito or contexto == ContextoPartida.LIBRE_INFINITO,
            n_preguntas=n_preguntas,
        )
    if reglas.correccion_al_final:
        reglas = ReglasPartida(
            vidas=reglas.vidas,
            tiempo_por_pregunta_seg=reglas.tiempo_por_pregunta_seg,
            tiempo_total_seg=reglas.tiempo_total_seg,
            sistema_puntuacion=reglas.sistema_puntuacion,
            mostrar_solucion_tras_fallo=reglas.mostrar_solucion_tras_fallo,
            mostrar_aciertos_en_curso=reglas.mostrar_aciertos_en_curso,
            correccion_al_final=False,
            dificultad_progresiva=reglas.dificultad_progresiva,
        )
    return reglas
