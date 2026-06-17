#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API unificada de reglas del modo libre."""

from __future__ import annotations

from Comun.configuracion_reglas_libre import alcance_para_contexto, construir_reglas_personalizadas
from Comun.politica_reglas import ContextoPartida, clasificar_libre, validar_reglas
from Comun.reglas_partida import ReglasPartida, SistemaPuntuacion

ETIQUETAS_SISTEMA: dict[SistemaPuntuacion, str] = {
    SistemaPuntuacion.ARCADE: "Arcade",
    SistemaPuntuacion.NOTA: "Nota 0-10",
    SistemaPuntuacion.PORCENTAJE: "Porcentaje",
}


def contexto_partida(*, modo_infinito: bool, n_preguntas: int) -> ContextoPartida:
    return clasificar_libre(modo_infinito=modo_infinito, n_preguntas=n_preguntas)


def reglas_desde_combinacion(
    contexto: ContextoPartida,
    *,
    vidas: int | None,
    sistema: SistemaPuntuacion,
    tiempo_por_pregunta_seg: int | None = None,
    tiempo_total_seg: int | None = None,
    mostrar_solucion_tras_fallo: bool = True,
    dificultad_progresiva: bool = False,
    modo_infinito: bool = False,
    n_preguntas: int = 10,
) -> ReglasPartida:
    reglas = construir_reglas_personalizadas(
        contexto,
        vidas=vidas,
        sistema=sistema,
        tiempo_por_pregunta_seg=tiempo_por_pregunta_seg,
        tiempo_total_seg=tiempo_total_seg,
        mostrar_solucion_tras_fallo=mostrar_solucion_tras_fallo,
        dificultad_progresiva=dificultad_progresiva,
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
    )
    return validar_reglas(
        reglas,
        contexto,
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
    )


def alcance(contexto: ContextoPartida):
    return alcance_para_contexto(contexto)
