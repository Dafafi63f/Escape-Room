#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reglas de partida: vidas, tiempo, puntuación y presets.

Qué puede elegir el jugador lo decide politica_reglas.py según el contexto
(una pregunta, bloque, infinito, examen historia, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

class SistemaPuntuacion(str, Enum):
    """Cómo se evalúa el resultado."""

    ARCADE = "arcade"
    NOTA = "nota"
    PORCENTAJE = "porcentaje"
    NINGUNO = "ninguno"


@dataclass(frozen=True)
class ReglasPartida:
    """
    Configuración de una sesión de juego.

    vidas=None  → sin expulsión; se responden todas las preguntas previstas.
    tiempo_*    → None = sin límite; si ambos están definidos, aplica el más restrictivo.
    """

    vidas: int | None = None
    tiempo_por_pregunta_seg: int | None = None
    tiempo_total_seg: int | None = None
    sistema_puntuacion: SistemaPuntuacion = SistemaPuntuacion.ARCADE
    mostrar_solucion_tras_fallo: bool = True
    mostrar_aciertos_en_curso: bool = False
    correccion_al_final: bool = False
    dificultad_progresiva: bool = False

    def tiene_vidas(self) -> bool:
        return self.vidas is not None and self.vidas > 0

    def tiene_tiempo(self) -> bool:
        return (self.tiempo_por_pregunta_seg or 0) > 0 or (self.tiempo_total_seg or 0) > 0

    def describe(self) -> str:
        partes: list[str] = []
        if self.tiene_vidas():
            partes.append(f"{self.vidas} vidas")
        else:
            partes.append("sin vidas (completa todas las preguntas)")
        if self.tiempo_por_pregunta_seg:
            partes.append(f"{self.tiempo_por_pregunta_seg}s/pregunta")
        if self.tiempo_total_seg:
            partes.append(f"{self.tiempo_total_seg}s total")
        if not self.tiene_tiempo():
            partes.append("sin límite de tiempo")
        partes.append(f"puntuación: {self.sistema_puntuacion.value}")
        if self.correccion_al_final:
            partes.append("corrección al final (sin pistas durante el examen)")
        return " · ".join(partes)


def preset_libre_arcade() -> ReglasPartida:
    return ReglasPartida(
        vidas=3,
        sistema_puntuacion=SistemaPuntuacion.ARCADE,
        dificultad_progresiva=True,
    )


def preset_libre_repaso() -> ReglasPartida:
    return ReglasPartida(
        vidas=None,
        sistema_puntuacion=SistemaPuntuacion.NOTA,
        mostrar_solucion_tras_fallo=True,
    )


def preset_libre_contrarreloj() -> ReglasPartida:
    return ReglasPartida(
        vidas=None,
        tiempo_por_pregunta_seg=90,
        sistema_puntuacion=SistemaPuntuacion.PORCENTAJE,
    )


def preset_historia_examen() -> ReglasPartida:
    """Simula un examen real: sin feedback hasta el final."""
    return ReglasPartida(
        vidas=None,
        sistema_puntuacion=SistemaPuntuacion.NOTA,
        mostrar_solucion_tras_fallo=False,
        mostrar_aciertos_en_curso=False,
        correccion_al_final=True,
    )


def preset_historia_reto() -> ReglasPartida:
    return ReglasPartida(
        vidas=3,
        sistema_puntuacion=SistemaPuntuacion.ARCADE,
    )


def preset_historia_resistencia() -> ReglasPartida:
    """Varias vidas; la racha de aciertos seguidos escala la dificultad; sin tiempo al inicio."""
    return ReglasPartida(
        vidas=3,
        sistema_puntuacion=SistemaPuntuacion.ARCADE,
        mostrar_solucion_tras_fallo=True,
        dificultad_progresiva=True,
    )


def calcular_puntos_arcade(dificultad: str, acierto: bool) -> int:
    base = {"Facil": 10, "Media": 20, "Dificil": 30}.get(dificultad, 15)
    return base if acierto else -max(5, base // 2)


def nota_sobre_diez(aciertos: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(10.0 * aciertos / total, 1)


def porcentaje_aciertos(aciertos: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(100.0 * aciertos / total, 1)


def formatear_resultado_puntuacion(
    reglas: ReglasPartida,
    *,
    aciertos: int,
    total: int,
    puntos_arcade: int,
) -> str:
    if reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE:
        return f"Puntos arcade: {puntos_arcade}"
    if reglas.sistema_puntuacion == SistemaPuntuacion.NOTA:
        return f"Nota (0-10): {nota_sobre_diez(aciertos, total)}"
    if reglas.sistema_puntuacion == SistemaPuntuacion.PORCENTAJE:
        return f"Aciertos: {porcentaje_aciertos(aciertos, total)}%"
    return f"Aciertos: {aciertos}/{total}"
