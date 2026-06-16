#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Núcleo del motor de partida (sin E/S de consola ni pygame)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from Comun.modelos import Pregunta
from Comun.reglas_partida import (
    ReglasPartida,
    SistemaPuntuacion,
    calcular_puntos_arcade,
    nota_sobre_diez,
    porcentaje_aciertos,
)


@dataclass
class EstadoPartida:
    nombre: str
    reglas: ReglasPartida
    vidas_restantes: int | None
    aciertos: int = 0
    respondidas: int = 0
    puntos_arcade: int = 0
    fallos_por_materia: dict[str, int] = field(default_factory=dict)
    inicio_total: float = field(default_factory=time.monotonic)

    def tiempo_total_restante(self) -> int | None:
        lim = self.reglas.tiempo_total_seg
        if not lim:
            return None
        rest = int(lim - (time.monotonic() - self.inicio_total))
        return max(0, rest)

    def debe_continuar(self, total_previsto: int | None) -> bool:
        if self.reglas.tiene_vidas() and (self.vidas_restantes or 0) <= 0:
            return False
        if total_previsto is not None and self.respondidas >= total_previsto:
            return False
        rest = self.tiempo_total_restante()
        if rest is not None and rest <= 0:
            return False
        return True


@dataclass
class ResultadoRespuesta:
    acierto: bool
    respuesta: str = ""
    tiempo_agotado: bool = False


@dataclass
class FeedbackRespuesta:
    mensaje: str
    solucion: str | None = None
    sin_vidas: bool = False


def texto_solucion(p: Pregunta) -> str:
    if p.correcta in {"A", "B", "C", "D"}:
        texto = p.opciones.get(p.correcta, "")
        return f"Correcta: {p.correcta}) {texto}"
    return "Correcta: (dato no disponible en esta pregunta)"


def linea_estado(
    estado: EstadoPartida,
    progreso: str,
    *,
    segundos_pregunta_restantes: int | None = None,
) -> str:
    partes = [progreso]
    if estado.reglas.tiene_vidas():
        partes.append(f"Vidas: {estado.vidas_restantes}")
    rest = estado.tiempo_total_restante()
    if rest is not None:
        partes.append(f"Tiempo restante: {rest}s")
    if segundos_pregunta_restantes is not None:
        partes.append(f"Pregunta: {segundos_pregunta_restantes}s")
    sis = estado.reglas.sistema_puntuacion
    if sis == SistemaPuntuacion.ARCADE:
        partes.append(f"Puntos: {estado.puntos_arcade}")
    elif estado.respondidas > 0:
        if sis == SistemaPuntuacion.NOTA:
            partes.append(
                f"Nota: {nota_sobre_diez(estado.aciertos, estado.respondidas)}"
            )
        elif sis == SistemaPuntuacion.PORCENTAJE:
            pct = porcentaje_aciertos(estado.aciertos, estado.respondidas)
            partes.append(f"Aciertos: {pct}%")
        elif estado.reglas.mostrar_aciertos_en_curso:
            partes.append(f"Aciertos: {estado.aciertos}/{estado.respondidas}")
    return " | ".join(partes)


def evaluar_respuesta(
    p: Pregunta,
    estado: EstadoPartida,
    resultado: ResultadoRespuesta,
) -> FeedbackRespuesta:
    estado.respondidas += 1
    reglas = estado.reglas

    if reglas.correccion_al_final:
        if resultado.tiempo_agotado or not resultado.acierto:
            estado.fallos_por_materia[p.materia] = estado.fallos_por_materia.get(p.materia, 0) + 1
        else:
            estado.aciertos += 1
        return FeedbackRespuesta(mensaje="Respuesta registrada.")

    if resultado.tiempo_agotado:
        if reglas.tiene_vidas():
            estado.vidas_restantes = (estado.vidas_restantes or 0) - 1
        estado.fallos_por_materia[p.materia] = estado.fallos_por_materia.get(p.materia, 0) + 1
        solucion = texto_solucion(p) if reglas.mostrar_solucion_tras_fallo else None
        return FeedbackRespuesta(
            mensaje="Tiempo agotado — cuenta como fallo",
            solucion=solucion,
            sin_vidas=reglas.tiene_vidas() and (estado.vidas_restantes or 0) <= 0,
        )

    if resultado.acierto:
        estado.aciertos += 1
        if reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE:
            delta = calcular_puntos_arcade(p.dificultad, True)
            estado.puntos_arcade += delta
            return FeedbackRespuesta(mensaje=f"Correcto (+{delta} puntos)")
        return FeedbackRespuesta(mensaje="Correcto")

    if reglas.tiene_vidas():
        estado.vidas_restantes = (estado.vidas_restantes or 0) - 1
    estado.fallos_por_materia[p.materia] = estado.fallos_por_materia.get(p.materia, 0) + 1
    if reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE:
        delta = calcular_puntos_arcade(p.dificultad, False)
        estado.puntos_arcade += delta
        mensaje = f"Incorrecto ({delta} puntos)"
    else:
        mensaje = "Incorrecto"
    solucion = texto_solucion(p) if reglas.mostrar_solucion_tras_fallo else None
    return FeedbackRespuesta(
        mensaje=mensaje,
        solucion=solucion,
        sin_vidas=reglas.tiene_vidas() and (estado.vidas_restantes or 0) <= 0,
    )
