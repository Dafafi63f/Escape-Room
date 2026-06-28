#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Núcleo del motor de partida (sin E/S de pygame ni terminal)."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from Comun.modelos import Pregunta
from Comun.reglas import (
    ReglasPartida,
    SistemaPuntuacion,
    calcular_puntos_arcade,
    nota_sobre_diez,
    porcentaje_aciertos,
    sumar_puntos_arcade,
)
TEXTO_OPCION_NIEBLA = "???"


def formatear_duracion_seg(segundos: int) -> str:
    """Texto legible para informes y estadísticas (p. ej. ``12 min 5 s``)."""
    s = max(0, int(segundos))
    if s < 60:
        return f"{s} s"
    minutos, resto = divmod(s, 60)
    if minutos < 60:
        return f"{minutos} min {resto} s" if resto else f"{minutos} min"
    horas, min_rest = divmod(minutos, 60)
    if min_rest:
        return f"{horas} h {min_rest} min"
    return f"{horas} h"


def texto_opcion_visible_pantalla(
    texto: str,
    letra_dataset: str,
    *,
    letras_eliminadas: frozenset[str],
    letras_niebla: frozenset[str],
) -> str | None:
    """Texto del botón en pantalla; None si la opción no se muestra (bomba/50-50)."""
    if letra_dataset in letras_eliminadas:
        return None
    if letra_dataset in letras_niebla:
        return TEXTO_OPCION_NIEBLA
    return texto


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

    def tiempo_transcurrido_seg(self) -> int:
        """Segundos desde el inicio de la partida (tiempo activo sin límite global)."""
        return max(0, int(time.monotonic() - self.inicio_total))

    def duracion_partida_seg(self) -> int:
        return self.tiempo_transcurrido_seg()

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


LETRAS_OPCION = ("A", "B", "C", "D")


@dataclass(frozen=True)
class PresentacionOpcionesPregunta:
    """Opciones permutadas y reetiquetadas A–D en pantalla (mapeo al dataset)."""

    filas: tuple[tuple[str, str, str], ...]  # (etiqueta, texto, letra_dataset)

    @classmethod
    def construir(cls, pregunta: Pregunta, *, rng: random.Random) -> PresentacionOpcionesPregunta:
        originales = [letra for letra in LETRAS_OPCION if pregunta.opciones.get(letra)]
        if len(originales) <= 1:
            filas = tuple(
                (letra, pregunta.opciones.get(letra, ""), letra) for letra in originales
            )
            return cls(filas=filas)
        permutadas = list(originales)
        rng.shuffle(permutadas)
        filas = tuple(
            (
                LETRAS_OPCION[i],
                pregunta.opciones.get(permutadas[i], ""),
                permutadas[i],
            )
            for i in range(len(permutadas))
        )
        return cls(filas=filas)

    def letra_dataset(self, etiqueta: str) -> str:
        for etiq, _, origen in self.filas:
            if etiq == etiqueta:
                return origen
        return etiqueta

    def etiqueta_visual(self, letra_dataset: str) -> str | None:
        for etiq, _, origen in self.filas:
            if origen == letra_dataset:
                return etiq
        return None


def presentacion_opciones_pantalla(
    pregunta: Pregunta,
    *,
    rng: random.Random,
) -> PresentacionOpcionesPregunta:
    """Permuta textos y muestra siempre A, B, C, D en orden vertical."""
    return PresentacionOpcionesPregunta.construir(pregunta, rng=rng)


def orden_letras_opciones_pantalla(
    pregunta: Pregunta,
    *,
    rng: random.Random,
) -> tuple[str, ...]:
    """Etiquetas visuales en pantalla (A–D en orden)."""
    return tuple(etiq for etiq, _, _ in presentacion_opciones_pantalla(pregunta, rng=rng).filas)


def marcar_botones_opciones_tras_respuesta(
    botones,
    *,
    presentacion: PresentacionOpcionesPregunta,
    correcta_dataset: str,
    respuesta_dataset: str,
    acierto: bool,
) -> None:
    correcta_vis = presentacion.etiqueta_visual(correcta_dataset)
    respuesta_vis = (
        presentacion.etiqueta_visual(respuesta_dataset) if respuesta_dataset else None
    )
    for boton in botones:
        boton.activo = False
        boton.marcar_correcta = False
        boton.marcar_incorrecta = False
        if correcta_vis and boton.letra == correcta_vis:
            boton.marcar_correcta = True
        elif respuesta_vis and boton.letra == respuesta_vis and not acierto:
            boton.marcar_incorrecta = True


def texto_solucion(
    p: Pregunta,
    presentacion: PresentacionOpcionesPregunta | None = None,
) -> str:
    if p.correcta in LETRAS_OPCION:
        texto = p.opciones.get(p.correcta, "")
        etiqueta = p.correcta
        if presentacion is not None:
            vis = presentacion.etiqueta_visual(p.correcta)
            if vis:
                etiqueta = vis
        return f"Correcta: {etiqueta}) {texto}"
    return "Correcta: (dato no disponible en esta pregunta)"


def linea_estado(
    estado: EstadoPartida,
    progreso: str,
    *,
    segundos_pregunta_restantes: int | None = None,
    vidas_max: int | None = None,
    progreso_puerta: str | None = None,
    progreso_sala: str | None = None,
    mostrar_tiempo_activo: bool = True,
    desafio_bloque_texto: str | None = None,
) -> str:
    from Comun.linea_estado_ui import linea_estado_con_iconos

    return linea_estado_con_iconos(
        estado,
        progreso,
        segundos_pregunta_restantes=segundos_pregunta_restantes,
        vidas_max=vidas_max,
        progreso_puerta=progreso_puerta,
        progreso_sala=progreso_sala,
        mostrar_tiempo_activo=mostrar_tiempo_activo,
        desafio_bloque_texto=desafio_bloque_texto,
    )


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
            estado.puntos_arcade, delta = sumar_puntos_arcade(estado.puntos_arcade, delta)
            return FeedbackRespuesta(mensaje=f"Correcto (+{delta} puntos)")
        return FeedbackRespuesta(mensaje="Correcto")

    if reglas.tiene_vidas():
        estado.vidas_restantes = (estado.vidas_restantes or 0) - 1
    estado.fallos_por_materia[p.materia] = estado.fallos_por_materia.get(p.materia, 0) + 1
    if reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE:
        delta = calcular_puntos_arcade(p.dificultad, False)
        estado.puntos_arcade, delta = sumar_puntos_arcade(estado.puntos_arcade, delta)
        mensaje = f"Incorrecto ({delta} puntos)"
    else:
        mensaje = "Incorrecto"
    solucion = texto_solucion(p) if reglas.mostrar_solucion_tras_fallo else None
    return FeedbackRespuesta(
        mensaje=mensaje,
        solucion=solucion,
        sin_vidas=reglas.tiene_vidas() and (estado.vidas_restantes or 0) <= 0,
    )

# --- navegacion_fin_partida ---


from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Grafico.pantallas import Pantalla


@dataclass
class NavegacionFinPartida:
    """Pantallas a las que puede ir el jugador desde el resumen final."""

    repetir: Callable[[], Pantalla] | None = None
    configurar: Callable[[], Pantalla] | None = None
