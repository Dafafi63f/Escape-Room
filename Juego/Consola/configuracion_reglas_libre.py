#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración personalizada de reglas en modo libre.

Solo se ofrece donde `politica_reglas` lo permite (bloque normal, bloque corto,
una pregunta). Infinito e historia mantienen reglas fijas del creador.
"""

from __future__ import annotations

from dataclasses import dataclass

from .consola import pedir_entero_en_rango, pedir_menu_numerado, pedir_opcion
from .reglas_partida import ReglasPartida, SistemaPuntuacion


def _ctx():
    from .politica_reglas import ContextoPartida

    return ContextoPartida


@dataclass(frozen=True)
class AlcanceConfigLibre:
    """Qué puede tocar el jugador en el asistente personalizado."""

    contexto: object  # ContextoPartida (evita import circular)
    titulo: str
    permitir_sin_vidas: bool = False
    min_vidas: int = 1
    max_vidas: int = 10
    sistemas: tuple[SistemaPuntuacion, ...] = (SistemaPuntuacion.ARCADE,)
    permitir_tiempo_pregunta: bool = False
    permitir_tiempo_total: bool = False
    permitir_dificultad_progresiva: bool = False
    permitir_solucion_tras_fallo: bool = True
    permitir_correccion_al_final: bool = False
    permitir_aciertos_en_curso: bool = True


def alcance_para_contexto(ctx) -> AlcanceConfigLibre | None:
    C = _ctx()
    if ctx == C.LIBRE_BLOQUE_NORMAL:
        return AlcanceConfigLibre(
            contexto=ctx,
            titulo="Bloque amplio (6+ preguntas)",
            permitir_sin_vidas=True,
            min_vidas=1,
            max_vidas=10,
            sistemas=(
                SistemaPuntuacion.ARCADE,
                SistemaPuntuacion.NOTA,
                SistemaPuntuacion.PORCENTAJE,
            ),
            permitir_tiempo_pregunta=True,
            permitir_tiempo_total=True,
            permitir_dificultad_progresiva=True,
            permitir_correccion_al_final=True,
        )
    if ctx == C.LIBRE_BLOQUE_CORTO:
        return AlcanceConfigLibre(
            contexto=ctx,
            titulo="Bloque corto (2-5 preguntas)",
            permitir_sin_vidas=False,
            min_vidas=1,
            max_vidas=5,
            sistemas=(SistemaPuntuacion.ARCADE,),
            permitir_solucion_tras_fallo=True,
            permitir_aciertos_en_curso=True,
        )
    if ctx == C.LIBRE_UNA_PREGUNTA:
        return AlcanceConfigLibre(
            contexto=ctx,
            titulo="Una sola pregunta",
            permitir_sin_vidas=False,
            min_vidas=1,
            max_vidas=10,
            sistemas=(SistemaPuntuacion.ARCADE,),
            permitir_solucion_tras_fallo=True,
            permitir_aciertos_en_curso=False,
        )
    return None


def _pedir_si_no(mensaje: str, *, defecto: str = "S") -> bool:
    return pedir_opcion(mensaje, ["S", "N"], default=defecto, permitir_atras=True) == "S"


def _elegir_sistema(alcance: AlcanceConfigLibre) -> SistemaPuntuacion:
    if len(alcance.sistemas) == 1:
        return alcance.sistemas[0]
    opciones = []
    for i, sis in enumerate(alcance.sistemas, start=1):
        desc = {
            SistemaPuntuacion.ARCADE: "Arcade — puntos por dificultad",
            SistemaPuntuacion.NOTA: "Nota 0-10 al final del bloque",
            SistemaPuntuacion.PORCENTAJE: "Porcentaje de aciertos al final",
        }.get(sis, sis.value)
        opciones.append((sis.value, desc))
    idx = pedir_menu_numerado("Sistema de puntuación:", opciones, defecto=1)
    return alcance.sistemas[idx - 1]


def _elegir_vidas(alcance: AlcanceConfigLibre) -> int | None:
    if alcance.permitir_sin_vidas:
        modo = pedir_opcion(
            "¿Cuántas vidas? (0 = sin vidas, completas todo el bloque): ",
            ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            default="3",
            permitir_atras=True,
        )
        if modo == "0":
            return None
        return int(modo)
    return pedir_entero_en_rango(
        f"Número de vidas [{alcance.min_vidas}-{alcance.max_vidas}]: ",
        alcance.min_vidas,
        alcance.max_vidas,
        3,
    )


def configurar_reglas_personalizado(ctx) -> ReglasPartida:
    """Asistente interactivo; las combinaciones incoherentes las corrige validar_reglas."""
    alcance = alcance_para_contexto(ctx)
    if alcance is None:
        raise ValueError(f"Configuración personalizada no permitida para {ctx.value}")

    print(f"\n--- Reglas personalizadas ({alcance.titulo}) ---")
    print("Solo se muestran opciones válidas para este tipo de partida.")

    vidas = _elegir_vidas(alcance)
    sistema = _elegir_sistema(alcance)

    tiempo_pregunta: int | None = None
    tiempo_total: int | None = None
    if alcance.permitir_tiempo_pregunta:
        seg = pedir_entero_en_rango(
            "Segundos por pregunta (0 = sin límite): ",
            0,
            600,
            0,
        )
        tiempo_pregunta = seg if seg > 0 else None
    if alcance.permitir_tiempo_total:
        seg = pedir_entero_en_rango(
            "Tiempo total del bloque en segundos (0 = sin límite): ",
            0,
            7200,
            0,
        )
        tiempo_total = seg if seg > 0 else None

    sin_vidas = vidas is None
    mostrar_solucion = (
        _pedir_si_no("¿Mostrar la solución tras cada fallo? (S/N): ", defecto="S")
        if alcance.permitir_solucion_tras_fallo
        else True
    )
    correccion_al_final = False
    if alcance.permitir_correccion_al_final and sin_vidas:
        correccion_al_final = _pedir_si_no(
            "¿Examen cerrado? (sin pistas hasta el final) (S/N): ",
            defecto="N",
        )
        if correccion_al_final:
            mostrar_solucion = False

    mostrar_aciertos = True
    if alcance.permitir_aciertos_en_curso and not correccion_al_final:
        mostrar_aciertos = _pedir_si_no(
            "¿Mostrar aciertos/fallos en la barra de progreso? (S/N): ",
            defecto="S" if sistema != SistemaPuntuacion.NOTA else "N",
        )
    elif correccion_al_final or sistema == SistemaPuntuacion.NOTA:
        mostrar_aciertos = False

    dificultad_progresiva = False
    if alcance.permitir_dificultad_progresiva and sistema == SistemaPuntuacion.ARCADE:
        dificultad_progresiva = _pedir_si_no(
            "¿Dificultad progresiva (sube con cada acierto)? (S/N): ",
            defecto="S",
        )

    return ReglasPartida(
        vidas=vidas,
        tiempo_por_pregunta_seg=tiempo_pregunta,
        tiempo_total_seg=tiempo_total,
        sistema_puntuacion=sistema,
        mostrar_solucion_tras_fallo=mostrar_solucion and not correccion_al_final,
        mostrar_aciertos_en_curso=mostrar_aciertos,
        correccion_al_final=correccion_al_final,
        dificultad_progresiva=dificultad_progresiva,
    )
