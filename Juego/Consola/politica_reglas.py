#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Políticas de reglas según el contexto de juego.

Una sola pregunta, un bloque finito, infinito o un examen de historia
no comparten las mismas reglas pedagógicas; aquí se acota qué puede elegir el jugador.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .configuracion_reglas_libre import configurar_reglas_personalizado
from .consola import pedir_menu_numerado
from .reglas_partida import (
    ReglasPartida,
    SistemaPuntuacion,
    preset_historia_examen,
    preset_historia_reto,
    preset_libre_arcade,
    preset_libre_contrarreloj,
    preset_libre_repaso,
)


class ContextoPartida(str, Enum):
    """Situación de juego definida por el creador del modo."""

    HISTORIA_SIMULACRO = "historia_simulacro"
    HISTORIA_RETO = "historia_reto"
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


def politica_libre_infinito() -> PoliticaReglas:
    return _politica_fija(
        ContextoPartida.LIBRE_INFINITO,
        preset_libre_arcade(),
        "Modo infinito: partida arcade con vidas y dificultad progresiva "
        "(no admite nota de examen ni bloque finito).",
    )


def politica_libre_una_pregunta() -> PoliticaReglas:
    return _politica_fija(
        ContextoPartida.LIBRE_UNA_PREGUNTA,
        ReglasPartida(
            vidas=3,
            sistema_puntuacion=SistemaPuntuacion.ARCADE,
            dificultad_progresiva=False,
            mostrar_solucion_tras_fallo=True,
        ),
        "Una sola pregunta: práctica rápida con vidas (sin nota de examen).",
    )


def politica_libre_bloque_corto() -> PoliticaReglas:
    return _politica_fija(
        ContextoPartida.LIBRE_BLOQUE_CORTO,
        ReglasPartida(
            vidas=3,
            sistema_puntuacion=SistemaPuntuacion.ARCADE,
            dificultad_progresiva=False,
        ),
        "Bloque corto (2-5 preguntas): arcade con vidas; la nota 0-10 no está disponible "
        "con tan pocas respuestas.",
    )


def _menu_reglas_con_personalizar(
    titulo: str,
    opciones_preset: list[tuple[str, str]],
    *,
    contexto: ContextoPartida,
) -> ReglasPartida:
    """Presets del creador + personalizar (solo si el contexto lo permite)."""
    opciones = [*opciones_preset, ("custom", "Personalizar — eliges solo lo permitido aquí")]
    idx = pedir_menu_numerado(titulo, opciones, defecto=1)
    if opciones_preset and idx <= len(opciones_preset):
        return _resolver_preset_por_indice(contexto, idx)
    return configurar_reglas_personalizado(contexto)


def _resolver_preset_por_indice(ctx: ContextoPartida, idx: int) -> ReglasPartida:
    if ctx == ContextoPartida.LIBRE_BLOQUE_NORMAL:
        if idx == 1:
            return ReglasPartida(
                vidas=3,
                sistema_puntuacion=SistemaPuntuacion.ARCADE,
                dificultad_progresiva=True,
            )
        if idx == 2:
            return preset_libre_repaso()
        return preset_libre_contrarreloj()
    if ctx == ContextoPartida.LIBRE_BLOQUE_CORTO:
        return politica_libre_bloque_corto().reglas
    if ctx == ContextoPartida.LIBRE_UNA_PREGUNTA:
        return politica_libre_una_pregunta().reglas
    raise ValueError(f"Preset no definido para {ctx}")


def _elegir_reglas_bloque_normal() -> ReglasPartida:
    return _menu_reglas_con_personalizar(
        "Estilo del bloque (modo libre, 6+ preguntas):",
        [
            ("arcade", "Arcade — 3 vidas y puntos"),
            ("repaso", "Repaso — sin vidas, nota 0-10 al final"),
            ("crono", "Contrarreloj — 90 s por pregunta, porcentaje al final"),
        ],
        contexto=ContextoPartida.LIBRE_BLOQUE_NORMAL,
    )


def _elegir_reglas_bloque_corto() -> ReglasPartida:
    return _menu_reglas_con_personalizar(
        "Reglas del bloque corto (2-5 preguntas):",
        [
            ("std", "Arcade estándar — 3 vidas, feedback inmediato"),
        ],
        contexto=ContextoPartida.LIBRE_BLOQUE_CORTO,
    )


def _elegir_reglas_una_pregunta() -> ReglasPartida:
    return _menu_reglas_con_personalizar(
        "Reglas (una sola pregunta):",
        [
            ("std", "Arcade — 3 vidas, ver solución si fallas"),
        ],
        contexto=ContextoPartida.LIBRE_UNA_PREGUNTA,
    )


def resolver_politica_libre(*, modo_infinito: bool, n_preguntas: int) -> PoliticaReglas:
    ctx = clasificar_libre(modo_infinito=modo_infinito, n_preguntas=n_preguntas)
    if ctx == ContextoPartida.LIBRE_INFINITO:
        return politica_libre_infinito()
    if ctx == ContextoPartida.LIBRE_UNA_PREGUNTA:
        reglas = _elegir_reglas_una_pregunta()
        return PoliticaReglas(
            contexto=ctx,
            reglas=reglas,
            eleccion_jugador=True,
            mensaje="Una pregunta: preset arcade o personalizar (vidas y pistas).",
        )
    if ctx == ContextoPartida.LIBRE_BLOQUE_CORTO:
        reglas = _elegir_reglas_bloque_corto()
        return PoliticaReglas(
            contexto=ctx,
            reglas=reglas,
            eleccion_jugador=True,
            mensaje="Bloque corto: arcade fijo o personalizar vidas/pistas (sin nota 0-10).",
        )
    reglas = _elegir_reglas_bloque_normal()
    return PoliticaReglas(
        contexto=ctx,
        reglas=reglas,
        eleccion_jugador=True,
        mensaje="Bloque 6+: arcade, repaso, contrarreloj o personalizar.",
    )


def resolver_politica_historia() -> PoliticaReglas:
    idx = pedir_menu_numerado(
        "Modo historia — reglas del creador:",
        [
            ("sim", "Simulacro de examen [recomendado]"),
            ("reto", "Variante reto (vidas + arcade)"),
        ],
        defecto=1,
    )
    return politica_historia_simulacro() if idx == 1 else politica_historia_reto()


def aplicar_politica(politica: PoliticaReglas) -> ReglasPartida:
    """Muestra el marco del creador y devuelve reglas ya validadas."""
    print(f"\n>>> {politica.mensaje}")
    if not politica.eleccion_jugador:
        print("(Configuración fija para este tipo de partida.)")
    print(f">>> {politica.reglas.describe()}")
    return validar_reglas(politica.reglas, politica.contexto)


def validar_reglas(reglas: ReglasPartida, contexto: ContextoPartida) -> ReglasPartida:
    """Refuerzo: impide combinaciones incoherentes aunque se alteren presets."""
    if contexto == ContextoPartida.HISTORIA_SIMULACRO:
        return preset_historia_examen()
    if contexto == ContextoPartida.HISTORIA_RETO:
        return preset_historia_reto()
    if contexto == ContextoPartida.LIBRE_INFINITO:
        return preset_libre_arcade()
    if contexto == ContextoPartida.LIBRE_UNA_PREGUNTA:
        return politica_libre_una_pregunta().reglas
    if contexto == ContextoPartida.LIBRE_BLOQUE_CORTO:
        return politica_libre_bloque_corto().reglas
    # LIBRE_BLOQUE_NORMAL: coherencia mínima
    if contexto == ContextoPartida.LIBRE_BLOQUE_CORTO:
        if reglas.sistema_puntuacion != SistemaPuntuacion.ARCADE or not reglas.tiene_vidas():
            return politica_libre_bloque_corto().reglas
        return reglas

    if reglas.sistema_puntuacion == SistemaPuntuacion.NOTA and reglas.tiene_vidas():
        reglas = ReglasPartida(
            vidas=None,
            tiempo_por_pregunta_seg=reglas.tiempo_por_pregunta_seg,
            tiempo_total_seg=reglas.tiempo_total_seg,
            sistema_puntuacion=SistemaPuntuacion.NOTA,
            mostrar_solucion_tras_fallo=reglas.mostrar_solucion_tras_fallo,
            mostrar_aciertos_en_curso=False,
            correccion_al_final=reglas.correccion_al_final,
            dificultad_progresiva=False,
        )

    if reglas.correccion_al_final:
        if reglas.tiene_vidas():
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
        else:
            return ReglasPartida(
                vidas=None,
                tiempo_por_pregunta_seg=reglas.tiempo_por_pregunta_seg,
                tiempo_total_seg=reglas.tiempo_total_seg,
                sistema_puntuacion=reglas.sistema_puntuacion,
                mostrar_solucion_tras_fallo=False,
                mostrar_aciertos_en_curso=False,
                correccion_al_final=True,
                dificultad_progresiva=False,
            )
    if reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE and not reglas.tiene_vidas():
        return ReglasPartida(
            vidas=3,
            sistema_puntuacion=SistemaPuntuacion.ARCADE,
            dificultad_progresiva=reglas.dificultad_progresiva,
            mostrar_solucion_tras_fallo=reglas.mostrar_solucion_tras_fallo,
            correccion_al_final=False,
        )
    if contexto == ContextoPartida.LIBRE_UNA_PREGUNTA and not reglas.tiene_vidas():
        return politica_libre_una_pregunta().reglas
    return reglas
