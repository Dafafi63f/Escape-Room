#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo resistencia del modo historia: escalada de dificultad y selección de preguntas."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from Comun.dificultad import complejidad_pregunta, max_complejidad_pool
from Comun.modelos import Pregunta
from Comun.pool_libre import EstadoSeleccionPool, crear_estado_seleccion
from Comun.preguntas_resistencia import (
    construir_pool_resistencia,
    pool_resistencia_desde_dataset,
)
from Comun.reglas_partida import ReglasPartida

__all__ = [
    "EscaladaResistencia",
    "EventoAleatorioResistencia",
    "PREGUNTA_MIN_EVENTOS_ALEATORIOS",
    "aplicar_escalada_a_reglas",
    "construir_pool_resistencia",
    "elegir_indice_resistencia",
    "escalada_para_pregunta",
    "escalada_para_racha",
    "es_preset_resistencia",
    "etiqueta_tier_exclusiva",
    "eventos_aleatorios_para_pregunta",
    "eventos_aleatorios_para_racha",
    "parametros_eventos_aleatorios",
    "pool_resistencia_desde_dataset",
    "probabilidad_pregunta_exclusiva",
    "texto_efectos_escalada",
]

_DIFICULTADES = ("Facil", "Media", "Dificil")

# Eventos aleatorios desde esta pregunta; la frecuencia/potencia/cantidad escalan después.
PREGUNTA_MIN_EVENTOS_ALEATORIOS = 5
RACHA_MIN_EVENTOS_ALEATORIOS = PREGUNTA_MIN_EVENTOS_ALEATORIOS

_EVENTOS_ALEATORIOS_POOL = (
    "relampago",
    "opciones_ocultas",
    "enunciado_oculto",
    "doble",
)

# Hasta aquí el techo de complejidad suele dejar solo fácil/medio; la sorpresa mete una difícil.
_PREGUNTA_MAX_SORPRESA_DIFICIL = 49


@dataclass(frozen=True)
class EventoAleatorioResistencia:
    """Efecto puntual que puede apilarse con otros en la misma pregunta."""

    etiqueta: str
    tiempo_pregunta: int | None = None
    multiplicador_puntos: int | None = None
    dificultades_permitidas: frozenset[str] | None = None
    max_complejidad: int | None = None
    opciones_ocultas: int | None = None
    fraccion_enunciado: float | None = None
    min_max_complejidad: int | None = None
    unir_dificultades: frozenset[str] | None = None


@dataclass(frozen=True)
class EscaladaResistencia:
    """Parámetros de juego según el número de pregunta en la partida."""

    nivel: int
    tiempo_pregunta_seg: int | None
    max_complejidad: int
    dificultades_permitidas: frozenset[str]
    mostrar_solucion_tras_fallo: bool
    multiplicador_puntos: int
    opciones_ocultas: int = 0
    fraccion_enunciado: float = 1.0
    efectos: tuple[str, ...] = ()


def es_preset_resistencia(preset) -> bool:
    return getattr(preset, "contexto_reglas", "") == "historia_resistencia"


def etiqueta_tier_exclusiva(pregunta: Pregunta) -> str | None:
    if not pregunta.exclusiva_resistencia:
        return None
    from Comun.preguntas_resistencia import ETIQUETAS_TIER_RESISTENCIA

    return ETIQUETAS_TIER_RESISTENCIA.get(pregunta.tier_resistencia, "Exclusiva")


def probabilidad_pregunta_exclusiva(numero_pregunta: int) -> float:
    """Cuota de exclusivas entre candidatas ya desbloqueadas."""
    if numero_pregunta < 100:
        return 0.0
    if numero_pregunta < 250:
        return 0.18
    if numero_pregunta < 500:
        return 0.28
    if numero_pregunta < 750:
        return 0.38
    return 0.48


def parametros_eventos_aleatorios(numero_pregunta: int) -> tuple[float, int, float]:
    """Probabilidad por pregunta, tope de eventos simultáneos e intensidad (0..1)."""
    if numero_pregunta < PREGUNTA_MIN_EVENTOS_ALEATORIOS:
        return 0.0, 0, 0.0
    progreso = numero_pregunta - PREGUNTA_MIN_EVENTOS_ALEATORIOS
    probabilidad = min(0.78, 0.10 + progreso * 0.0045)
    max_eventos = 1 + min(3, progreso // 30)
    intensidad = min(1.0, 0.25 + progreso / 180.0)
    return probabilidad, max_eventos, intensidad


def _construir_evento(kind: str, intensidad: float) -> EventoAleatorioResistencia:
    if kind == "relampago":
        seg = max(3, int(11 - 7 * intensidad))
        return EventoAleatorioResistencia(
            etiqueta=f"Relámpago: {seg} s por pregunta",
            tiempo_pregunta=seg,
        )
    if kind == "opciones_ocultas":
        n = 1 if intensidad < 0.6 else 2
        return EventoAleatorioResistencia(
            etiqueta=f"Niebla: {n} respuesta(s) oculta(s)",
            opciones_ocultas=n,
        )
    if kind == "enunciado_oculto":
        fraccion = 0.55 if intensidad < 0.7 else 0.4
        return EventoAleatorioResistencia(
            etiqueta="Niebla: enunciado parcialmente oculto",
            fraccion_enunciado=fraccion,
        )
    if kind == "doble":
        mult = 2 if intensidad < 0.75 else 3
        texto = "Doble puntos" if mult == 2 else "Triple puntos"
        return EventoAleatorioResistencia(
            etiqueta=texto,
            multiplicador_puntos=mult,
        )
    if kind == "sorpresa_dificil":
        extra = intensidad >= 0.7
        cx = 4 if extra else 3
        return EventoAleatorioResistencia(
            etiqueta="Pregunta extra difícil" if extra else "Pregunta difícil",
            min_max_complejidad=cx,
            unir_dificultades=frozenset({"Dificil"}),
        )
    raise ValueError(f"Evento desconocido: {kind!r}")


def _kinds_eventos_para_pregunta(numero_pregunta: int) -> list[str]:
    kinds = list(_EVENTOS_ALEATORIOS_POOL)
    if numero_pregunta <= _PREGUNTA_MAX_SORPRESA_DIFICIL:
        kinds.append("sorpresa_dificil")
    return kinds


def eventos_aleatorios_para_pregunta(numero_pregunta: int) -> tuple[EventoAleatorioResistencia, ...]:
    """Efectos extra con probabilidad creciente; pueden apilarse varios en una pregunta."""
    probabilidad, max_eventos, intensidad = parametros_eventos_aleatorios(numero_pregunta)
    if max_eventos <= 0 or probabilidad <= 0.0:
        return ()
    rng = random.Random(numero_pregunta * 7919 + 17)
    if rng.random() > probabilidad:
        return ()
    n = 1
    if max_eventos > 1:
        chance_extra = min(0.55, 0.08 + intensidad * 0.45)
        if rng.random() < chance_extra:
            n = rng.randint(2, max_eventos)
    kinds = _kinds_eventos_para_pregunta(numero_pregunta)
    rng.shuffle(kinds)
    return tuple(_construir_evento(kinds[i % len(kinds)], intensidad) for i in range(n))


def _fusionar_evento_en_escalada(
    evento: EventoAleatorioResistencia,
    *,
    tiempo: int | None,
    max_cx: int,
    permitidas: frozenset[str],
    mult: int,
    opciones_ocultas: int,
    fraccion_enunciado: float,
    efectos: list[str],
) -> tuple[int | None, int, frozenset[str], int, int, float]:
    efectos.append(evento.etiqueta)
    if evento.tiempo_pregunta is not None:
        if tiempo is None:
            tiempo = evento.tiempo_pregunta
        else:
            tiempo = min(tiempo, evento.tiempo_pregunta)
    if evento.multiplicador_puntos is not None:
        mult = max(mult, evento.multiplicador_puntos)
    if evento.dificultades_permitidas is not None:
        permitidas = frozenset(permitidas & evento.dificultades_permitidas)
        if not permitidas:
            permitidas = evento.dificultades_permitidas
    if evento.unir_dificultades is not None:
        permitidas = frozenset(permitidas | evento.unir_dificultades)
    if evento.max_complejidad is not None:
        max_cx = max(max_cx, evento.max_complejidad)
    if evento.min_max_complejidad is not None:
        max_cx = max(max_cx, evento.min_max_complejidad)
    if evento.opciones_ocultas is not None:
        opciones_ocultas = max(opciones_ocultas, evento.opciones_ocultas)
    if evento.fraccion_enunciado is not None:
        fraccion_enunciado = min(fraccion_enunciado, evento.fraccion_enunciado)
    return tiempo, max_cx, permitidas, mult, opciones_ocultas, fraccion_enunciado


def escalada_para_pregunta(numero_pregunta: int) -> EscaladaResistencia:
    """Calcula reglas vigentes según el número de pregunta (1 = inicio fácil, sin tiempo)."""
    progreso = max(0, numero_pregunta - 1)
    tiempo: int | None = None
    max_cx = 2
    permitidas = frozenset(_DIFICULTADES)
    mostrar_sol = True
    mult = 1
    nivel = 0
    opciones_ocultas = 0
    fraccion_enunciado = 1.0
    efectos: list[str] = []

    if progreso >= 700:
        nivel = 7
        tiempo = 10
        max_cx = 99
        permitidas = frozenset({"Dificil"})
        mostrar_sol = False
        efectos.append("Nivel extremo: solo difíciles, 10 s, sin pistas")
    elif progreso >= 400:
        nivel = 6
        tiempo = 12
        max_cx = 99
        permitidas = frozenset({"Dificil"})
        efectos.append("Solo preguntas difíciles")
    elif progreso >= 200:
        nivel = 5
        tiempo = 15
        max_cx = 5
        permitidas = frozenset({"Media", "Dificil"})
        efectos.append("Sin preguntas fáciles · 15 s")
    elif progreso >= 100:
        nivel = 4
        tiempo = 20
        max_cx = 4
        permitidas = frozenset({"Media", "Dificil"})
        efectos.append("Tiempo: 20 s por pregunta")
    elif progreso >= 50:
        nivel = 3
        tiempo = 30
        max_cx = 4
        permitidas = frozenset({"Media", "Dificil"})
        efectos.append("Sin preguntas fáciles · 30 s")
    elif progreso >= 25:
        nivel = 2
        tiempo = 45
        max_cx = 3
        permitidas = frozenset({"Facil", "Media", "Dificil"})
        efectos.append("Tiempo: 45 s por pregunta")
    elif progreso >= 10:
        nivel = 1
        permitidas = frozenset({"Media", "Dificil"})
        efectos.append("Sin preguntas fáciles")

    for evento in eventos_aleatorios_para_pregunta(numero_pregunta):
        (
            tiempo,
            max_cx,
            permitidas,
            mult,
            opciones_ocultas,
            fraccion_enunciado,
        ) = _fusionar_evento_en_escalada(
            evento,
            tiempo=tiempo,
            max_cx=max_cx,
            permitidas=permitidas,
            mult=mult,
            opciones_ocultas=opciones_ocultas,
            fraccion_enunciado=fraccion_enunciado,
            efectos=efectos,
        )

    return EscaladaResistencia(
        nivel=nivel,
        tiempo_pregunta_seg=tiempo,
        max_complejidad=max_cx,
        dificultades_permitidas=permitidas,
        mostrar_solucion_tras_fallo=mostrar_sol,
        multiplicador_puntos=mult,
        opciones_ocultas=opciones_ocultas,
        fraccion_enunciado=fraccion_enunciado,
        efectos=tuple(efectos),
    )


def escalada_para_racha(racha: int) -> EscaladaResistencia:
    """Alias histórico: la escalada depende del número de pregunta, no de la racha."""
    return escalada_para_pregunta(racha + 1)


eventos_aleatorios_para_racha = eventos_aleatorios_para_pregunta


def aplicar_escalada_a_reglas(base: ReglasPartida, escalada: EscaladaResistencia) -> ReglasPartida:
    return ReglasPartida(
        vidas=base.vidas,
        tiempo_por_pregunta_seg=escalada.tiempo_pregunta_seg,
        tiempo_total_seg=None,
        sistema_puntuacion=base.sistema_puntuacion,
        mostrar_solucion_tras_fallo=escalada.mostrar_solucion_tras_fallo,
        mostrar_aciertos_en_curso=base.mostrar_aciertos_en_curso,
        correccion_al_final=False,
        dificultad_progresiva=True,
    )


def texto_efectos_escalada(escalada: EscaladaResistencia) -> str:
    if not escalada.efectos:
        if escalada.nivel == 0:
            return "Inicio: fácil, sin límite de tiempo"
        return f"Nivel {escalada.nivel}"
    return " · ".join(escalada.efectos)


def _indices_candidatos(
    pool: list[Pregunta],
    estado: EstadoSeleccionPool,
    escalada: EscaladaResistencia,
    numero_pregunta: int,
    *,
    solo_no_usadas: bool,
) -> list[int]:
    bloqueadas = set(estado.historial_reciente)
    candidatas: list[int] = []
    progreso = max(0, numero_pregunta - 1)
    for idx, p in enumerate(pool):
        if idx in bloqueadas:
            continue
        if p.racha_minima_resistencia > progreso:
            continue
        if p.dificultad not in escalada.dificultades_permitidas:
            continue
        if complejidad_pregunta(p) > escalada.max_complejidad:
            continue
        if solo_no_usadas and idx in estado.usadas:
            continue
        candidatas.append(idx)
    return candidatas


def _elegir_entre_candidatas(
    pool: list[Pregunta],
    candidatas: list[int],
    numero_pregunta: int,
) -> int:
    exclusivas = [i for i in candidatas if pool[i].exclusiva_resistencia]
    normales = [i for i in candidatas if not pool[i].exclusiva_resistencia]
    if exclusivas and normales:
        prob = probabilidad_pregunta_exclusiva(numero_pregunta)
        grupo = exclusivas if random.random() < prob else normales
        return random.choice(grupo)
    return random.choice(candidatas)


def elegir_indice_resistencia(
    pool: list[Pregunta],
    estado: EstadoSeleccionPool,
    escalada: EscaladaResistencia,
    numero_pregunta: int,
) -> int | None:
    if not pool:
        return None
    candidatas = _indices_candidatos(pool, estado, escalada, numero_pregunta, solo_no_usadas=True)
    if not candidatas:
        estado.usadas.clear()
        candidatas = _indices_candidatos(pool, estado, escalada, numero_pregunta, solo_no_usadas=False)
    if not candidatas:
        progreso = max(0, numero_pregunta - 1)
        candidatas = [
            idx
            for idx, p in enumerate(pool)
            if p.racha_minima_resistencia <= progreso
        ]
    if not candidatas:
        return None
    idx = _elegir_entre_candidatas(pool, candidatas, numero_pregunta)
    estado.usadas.add(idx)
    estado.historial_reciente.append(idx)
    return idx


def crear_seleccion_resistencia(pool: list[Pregunta]) -> EstadoSeleccionPool:
    return crear_estado_seleccion(len(pool))


def max_complejidad_resistencia(pool: list[Pregunta]) -> int:
    return max_complejidad_pool(pool)
