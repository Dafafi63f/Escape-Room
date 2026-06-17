#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configuración de reglas del modo libre (sin E/S)."""

from __future__ import annotations

from dataclasses import dataclass

from Comun.compatibilidad_reglas_libre import sanitizar_reglas_libre
from Comun.reglas_partida import ReglasPartida, SistemaPuntuacion


def _ctx():
    from Comun.politica_reglas import ContextoPartida

    return ContextoPartida


_TITULOS_LIBRE: dict[object, str] = {}


def _titulos_libre() -> dict[object, str]:
    global _TITULOS_LIBRE
    if not _TITULOS_LIBRE:
        C = _ctx()
        _TITULOS_LIBRE = {
            C.LIBRE_BLOQUE_NORMAL: "Bloque amplio (6+ preguntas)",
            C.LIBRE_BLOQUE_CORTO: "Bloque corto (2-5 preguntas)",
            C.LIBRE_UNA_PREGUNTA: "Una sola pregunta",
            C.LIBRE_INFINITO: "Modo infinito",
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
    permitir_solucion_tras_fallo: bool = True


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
    mostrar_solucion_tras_fallo: bool = True,
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
        mostrar_solucion_tras_fallo=mostrar_solucion_tras_fallo,
        mostrar_aciertos_en_curso=False,
        correccion_al_final=False,
        dificultad_progresiva=dificultad_progresiva,
    )
    return sanitizar_reglas_libre(
        reglas,
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
    )
