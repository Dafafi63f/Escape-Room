#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reglas del modo libre: compatibilidad, configuración y API unificada."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from Comun.reglas_partida import (
    MIN_PREGUNTAS_PARTIDA,
    ReglasPartida,
    SistemaPuntuacion,
)

if TYPE_CHECKING:
    from Comun.politica_reglas import ContextoPartida

MIN_PREGUNTAS_CALIFICACION = MIN_PREGUNTAS_PARTIDA

ETIQUETAS_SISTEMA: dict[SistemaPuntuacion, str] = {
    SistemaPuntuacion.ARCADE: "Arcade",
    SistemaPuntuacion.NOTA: "Nota 0-10",
    SistemaPuntuacion.PORCENTAJE: "Porcentaje",
}


@dataclass(frozen=True)
class OpcionesReglasLibre:
    """Qué controles están habilitados según la selección actual."""

    sistemas: tuple[SistemaPuntuacion, ...]
    permitir_sin_vidas: bool
    permitir_con_vidas: bool
    permitir_dificultad_progresiva: bool
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
        and (modo_infinito or n_preguntas >= MIN_PREGUNTAS_PARTIDA)
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
        mostrar_solucion_tras_fallo=True,
        mostrar_aciertos_en_curso=False,
        correccion_al_final=False,
        dificultad_progresiva=dif,
    )


_TITULOS_LIBRE: dict[object, str] = {}


def _titulos_libre() -> dict[object, str]:
    global _TITULOS_LIBRE
    if not _TITULOS_LIBRE:
        from Comun.politica_reglas import ContextoPartida

        _TITULOS_LIBRE = {
            ContextoPartida.LIBRE_BLOQUE_CORTO: f"Bloque mínimo ({MIN_PREGUNTAS_PARTIDA} preguntas)",
            ContextoPartida.LIBRE_BLOQUE_NORMAL: "Bloque amplio (6+ preguntas)",
            ContextoPartida.LIBRE_INFINITO: "Modo infinito",
        }
    return _TITULOS_LIBRE


@dataclass(frozen=True)
class AlcanceConfigLibre:
    """Opciones disponibles en el asistente de reglas del modo libre."""

    contexto: object
    titulo: str
    permitir_sin_vidas: bool = True
    min_vidas: int = 1
    max_vidas: int = 10
    sistemas: tuple[SistemaPuntuacion, ...] = (
        SistemaPuntuacion.ARCADE,
        SistemaPuntuacion.NOTA,
        SistemaPuntuacion.PORCENTAJE,
    )
    permitir_tiempo_pregunta: bool = True
    permitir_tiempo_total: bool = True
    permitir_dificultad_progresiva: bool = True


def alcance_para_contexto(ctx) -> AlcanceConfigLibre | None:
    titulo = _titulos_libre().get(ctx)
    if titulo is None:
        return None
    return AlcanceConfigLibre(contexto=ctx, titulo=titulo)


def construir_reglas_personalizadas(
    ctx,
    *,
    vidas: int | None,
    sistema: SistemaPuntuacion,
    tiempo_por_pregunta_seg: int | None = None,
    tiempo_total_seg: int | None = None,
    dificultad_progresiva: bool = False,
    modo_infinito: bool = False,
    n_preguntas: int = 10,
) -> ReglasPartida:
    if alcance_para_contexto(ctx) is None:
        raise ValueError(f"Configuración personalizada no permitida para {ctx.value}")

    reglas = ReglasPartida(
        vidas=vidas,
        tiempo_por_pregunta_seg=tiempo_por_pregunta_seg,
        tiempo_total_seg=tiempo_total_seg,
        sistema_puntuacion=sistema,
        mostrar_solucion_tras_fallo=True,
        mostrar_aciertos_en_curso=False,
        correccion_al_final=False,
        dificultad_progresiva=dificultad_progresiva,
    )
    return sanitizar_reglas_libre(
        reglas,
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
    )


def contexto_partida(*, modo_infinito: bool, n_preguntas: int) -> ContextoPartida:
    from Comun.politica_reglas import clasificar_libre

    return clasificar_libre(modo_infinito=modo_infinito, n_preguntas=n_preguntas)


def reglas_desde_combinacion(
    contexto: ContextoPartida,
    *,
    vidas: int | None,
    sistema: SistemaPuntuacion,
    tiempo_por_pregunta_seg: int | None = None,
    tiempo_total_seg: int | None = None,
    dificultad_progresiva: bool = False,
    modo_infinito: bool = False,
    n_preguntas: int = 10,
) -> ReglasPartida:
    from Comun.politica_reglas import validar_reglas

    reglas = construir_reglas_personalizadas(
        contexto,
        vidas=vidas,
        sistema=sistema,
        tiempo_por_pregunta_seg=tiempo_por_pregunta_seg,
        tiempo_total_seg=tiempo_total_seg,
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
