#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Asistente de consola para configurar reglas del modo libre."""

from __future__ import annotations

from Comun.compatibilidad_reglas_libre import normalizar_vidas_y_sistema, opciones_reglas_libre
from Comun.configuracion_reglas_libre import (
    AlcanceConfigLibre,
    alcance_para_contexto,
    construir_reglas_personalizadas,
)
from Comun.reglas_partida import ReglasPartida, SistemaPuntuacion

from .consola import pedir_entero_en_rango, pedir_menu_numerado, pedir_opcion

__all__ = [
    "AlcanceConfigLibre",
    "alcance_para_contexto",
    "construir_reglas_personalizadas",
    "configurar_reglas_personalizado",
]


def _pedir_si_no(mensaje: str, *, defecto: str = "S") -> bool:
    return pedir_opcion(mensaje, ["S", "N"], default=defecto, permitir_atras=True) == "S"


def _elegir_modo_tiempo() -> tuple[int | None, int | None]:
    idx = pedir_menu_numerado(
        "Límite de tiempo:",
        [
            ("ninguno", "Sin límite"),
            ("pregunta", "Segundos por pregunta"),
            ("total", "Tiempo total del bloque"),
        ],
        defecto=1,
    )
    if idx == 2:
        seg = pedir_entero_en_rango("Segundos por pregunta: ", 1, 600, 90)
        return seg, None
    if idx == 3:
        seg = pedir_entero_en_rango("Tiempo total del bloque (segundos): ", 1, 7200, 600)
        return None, seg
    return None, None


def configurar_reglas_personalizado(
    ctx,
    *,
    modo_infinito: bool = False,
    n_preguntas: int = 10,
) -> ReglasPartida:
    """Asistente interactivo de reglas del modo libre."""
    alcance = alcance_para_contexto(ctx)
    if alcance is None:
        raise ValueError(f"Configuración personalizada no permitida para {ctx.value}")

    print(f"\n--- Reglas de partida ({alcance.titulo}) ---")

    sin_vidas = False
    sistema = SistemaPuntuacion.ARCADE
    vidas: int | None = 3

    opts = opciones_reglas_libre(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin_vidas,
        sistema=sistema,
    )
    if opts.permitir_sin_vidas and opts.permitir_con_vidas:
        modo_vidas = pedir_opcion(
            "¿Vidas? (0 = sin vidas, 1-10 = con vidas): ",
            ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            default="3",
            permitir_atras=True,
        )
        if modo_vidas == "0":
            sin_vidas = True
            vidas = None
        else:
            sin_vidas = False
            vidas = int(modo_vidas)
    elif opts.permitir_sin_vidas:
        sin_vidas = True
        vidas = None
        print("Sin vidas (obligatorio con nota o porcentaje).")
    else:
        sin_vidas = False
        vidas = pedir_entero_en_rango("Número de vidas [1-10]: ", 1, 10, 3)

    opts = opciones_reglas_libre(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin_vidas,
        sistema=sistema,
    )
    opciones_sis = []
    for sis in opts.sistemas:
        desc = {
            SistemaPuntuacion.ARCADE: "Arcade — puntos por dificultad",
            SistemaPuntuacion.NOTA: "Nota 0-10 al final del bloque",
            SistemaPuntuacion.PORCENTAJE: "Porcentaje de aciertos al final",
        }[sis]
        opciones_sis.append((sis.value, desc))
    if len(opciones_sis) == 1:
        sistema = opts.sistemas[0]
        if sistema != SistemaPuntuacion.ARCADE:
            print(f"Puntuación: {opciones_sis[0][1]} (única opción con esta configuración).")
    else:
        idx = pedir_menu_numerado("Sistema de puntuación:", opciones_sis, defecto=1)
        sistema = opts.sistemas[idx - 1]
    sin_vidas, sistema = normalizar_vidas_y_sistema(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin_vidas,
        sistema=sistema,
    )
    if sin_vidas:
        vidas = None

    tiempo_pregunta, tiempo_total = _elegir_modo_tiempo()

    mostrar_solucion = _pedir_si_no(
        "¿Mostrar la solución tras cada fallo? (S/N): ",
        defecto="S",
    )

    opts = opciones_reglas_libre(
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
        sin_vidas=sin_vidas,
        sistema=sistema,
    )
    mostrar_aciertos = False
    if opts.permitir_aciertos_en_curso:
        mostrar_aciertos = _pedir_si_no(
            "¿Mostrar aciertos/fallos en la barra de progreso? (S/N): ",
            defecto="S",
        )
    dificultad_progresiva = False
    if opts.permitir_dificultad_progresiva:
        dificultad_progresiva = _pedir_si_no(
            "¿Dificultad progresiva (sube con cada acierto)? (S/N): ",
            defecto="S",
        )

    return construir_reglas_personalizadas(
        ctx,
        vidas=vidas,
        sistema=sistema,
        tiempo_por_pregunta_seg=tiempo_pregunta,
        tiempo_total_seg=tiempo_total,
        mostrar_solucion_tras_fallo=mostrar_solucion,
        mostrar_aciertos_en_curso=mostrar_aciertos,
        dificultad_progresiva=dificultad_progresiva,
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
    )
