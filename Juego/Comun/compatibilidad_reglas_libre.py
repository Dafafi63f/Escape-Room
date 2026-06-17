#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibilidad entre opciones de reglas del modo libre."""

from __future__ import annotations

from dataclasses import dataclass

from Comun.reglas_partida import ReglasPartida, SistemaPuntuacion

MIN_PREGUNTAS_CALIFICACION = 4


@dataclass(frozen=True)
class OpcionesReglasLibre:
    """Qué controles están habilitados según la selección actual."""

    sistemas: tuple[SistemaPuntuacion, ...]
    permitir_sin_vidas: bool
    permitir_con_vidas: bool
    permitir_dificultad_progresiva: bool
    permitir_solucion_tras_fallo: bool = True
    permitir_tiempo_pregunta: bool = True
    permitir_tiempo_total: bool = True


def _calificacion_viable(*, modo_infinito: bool, n_preguntas: int) -> bool:
    return not modo_infinito and n_preguntas >= MIN_PREGUNTAS_CALIFICACION


def sistemas_disponibles(
    *,
    modo_infinito: bool,
    n_preguntas: int,
    sin_vidas: bool,
) -> tuple[SistemaPuntuacion, ...]:
    if modo_infinito or not sin_vidas:
        return (SistemaPuntuacion.ARCADE,)
    if not _calificacion_viable(modo_infinito=modo_infinito, n_preguntas=n_preguntas):
        return (SistemaPuntuacion.ARCADE,)
    return (
        SistemaPuntuacion.ARCADE,
        SistemaPuntuacion.NOTA,
        SistemaPuntuacion.PORCENTAJE,
    )


def normalizar_vidas_y_sistema(
    *,
    modo_infinito: bool,
    n_preguntas: int,
    sin_vidas: bool,
    sistema: SistemaPuntuacion,
) -> tuple[bool, SistemaPuntuacion]:
    if modo_infinito:
        return sin_vidas, SistemaPuntuacion.ARCADE
    if not sin_vidas:
        return False, SistemaPuntuacion.ARCADE

    sis = sistema
    if sis in {SistemaPuntuacion.NOTA, SistemaPuntuacion.PORCENTAJE}:
        if not _calificacion_viable(modo_infinito=modo_infinito, n_preguntas=n_preguntas):
            sis = SistemaPuntuacion.ARCADE
    return True, sis


def opciones_reglas_libre(
    *,
    modo_infinito: bool,
    n_preguntas: int,
    sin_vidas: bool,
    sistema: SistemaPuntuacion,
) -> OpcionesReglasLibre:
    sin, sis = normalizar_vidas_y_sistema(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin_vidas,
        sistema=sistema,
    )
    sistemas = sistemas_disponibles(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin,
    )
    progresiva = (
        sis == SistemaPuntuacion.ARCADE
        and (modo_infinito or n_preguntas > 1)
    )
    return OpcionesReglasLibre(
        sistemas=sistemas,
        permitir_sin_vidas=True,
        permitir_con_vidas=sis == SistemaPuntuacion.ARCADE,
        permitir_dificultad_progresiva=progresiva,
    )


def sanitizar_reglas_libre(
    reglas: ReglasPartida,
    *,
    modo_infinito: bool,
    n_preguntas: int,
) -> ReglasPartida:
    sin = reglas.vidas is None
    sin, sis = normalizar_vidas_y_sistema(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin,
        sistema=reglas.sistema_puntuacion,
    )
    opts = opciones_reglas_libre(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin,
        sistema=sis,
    )
    vidas = None if sin else (reglas.vidas if reglas.vidas and reglas.vidas > 0 else 3)
    dif = reglas.dificultad_progresiva if opts.permitir_dificultad_progresiva else False
    return ReglasPartida(
        vidas=vidas,
        tiempo_por_pregunta_seg=reglas.tiempo_por_pregunta_seg,
        tiempo_total_seg=reglas.tiempo_total_seg,
        sistema_puntuacion=sis,
        mostrar_solucion_tras_fallo=reglas.mostrar_solucion_tras_fallo,
        mostrar_aciertos_en_curso=False,
        correccion_al_final=False,
        dificultad_progresiva=dif,
    )
