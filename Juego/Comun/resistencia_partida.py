#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo resistencia: pool, escalada de dificultad y selección de preguntas."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from Comun.dificultad import complejidad_pregunta, max_complejidad_pool
from Comun.modelos import Pregunta
from Comun.pool_libre import EstadoSeleccionPool, crear_estado_seleccion
from Comun.preguntas_resistencia import (
    BancoResistencia,
    construir_banco_resistencia,
    construir_pool_resistencia,
    pool_resistencia_desde_dataset,
)
from Comun.resistencia_motor import PREGUNTA_MIN_EVENTOS_ALEATORIOS
from Comun.reglas_partida import ReglasPartida

__all__ = [
    "BancoResistencia",
    "EscaladaResistencia",
    "EventoAleatorioResistencia",
    "PityEventosResistencia",
    "PREGUNTA_MIN_EVENTOS_ALEATORIOS",
    "aplicar_escalada_a_reglas",
    "avisos_pre_pregunta_resistencia",
    "baseline_escalada_resistencia",
    "construir_banco_resistencia",
    "construir_pool_resistencia",
    "elegir_indice_resistencia",
    "elegir_indice_similar",
    "escalada_para_pregunta",
    "es_preset_resistencia",
    "etiqueta_tier_exclusiva",
    "eventos_aleatorios_para_pregunta",
    "parametros_eventos_aleatorios",
    "actualizar_pity_eventos_resistencia",
    "prob_gate_evento_resistencia_con_pity",
    "pool_resistencia_desde_dataset",
    "probabilidad_pregunta_exclusiva",
    "partes_texto_efectos_escalada",
    "texto_efectos_escalada",
]

_DIFICULTADES = ("Facil", "Media", "Dificil")

RACHA_MIN_EVENTOS_ALEATORIOS = PREGUNTA_MIN_EVENTOS_ALEATORIOS

from Comun.eventos_partida import (
    elegir_malos_resistencia_exclusivos,
    ids_eventos_buenos_resistencia,
    malos_resistencia_vigentes,
    ids_pool_resistencia_aleatorio,
)

_EVENTOS_ALEATORIOS_POOL = ids_pool_resistencia_aleatorio()
_EVENTOS_BUENOS = ids_eventos_buenos_resistencia()

_MALOS_PITY_RESISTENCIA = frozenset({
    "relampago",
    "opciones_ocultas",
})
_KINDS_PITY_RESISTENCIA = _MALOS_PITY_RESISTENCIA | frozenset({"doble"})

_PITY_INC_GATE_MALO = 0.025
_PITY_INC_GATE_BUENO = 0.018
_PROB_GATE_MAX_BOOST_MALO = 0.35
_PROB_GATE_MAX_BOOST_BUENO = 0.30
_PITY_INC_MALO_KIND = 0.22
_PESO_BASE_MALO_KIND = 1.0

# Hasta aquí el techo de complejidad suele dejar solo fácil/medio; eventos solo modifican la pregunta actual.


@dataclass
class PityEventosResistencia:
    """Preguntas seguidas sin ver un popup de escalada; sube prob. y peso al elegir tipo."""

    preguntas_sin_malo: int = 0
    preguntas_sin_bueno: int = 0
    preguntas_sin_por_kind: dict[str, int] = field(
        default_factory=lambda: {k: 0 for k in _KINDS_PITY_RESISTENCIA}
    )
    ultima_pregunta_actualizada: int = 0
    _cache_pregunta: int = 0
    _cache_eventos: tuple[EventoAleatorioResistencia, ...] = ()


def prob_gate_evento_resistencia_con_pity(
    *,
    prob_base: float,
    preguntas_sin_ver: int,
    incremento_por_pregunta: float,
    max_boost: float,
    prob_tope: float = 0.98,
) -> float:
    if preguntas_sin_ver <= 0:
        return prob_base
    boost = min(max_boost, preguntas_sin_ver * incremento_por_pregunta)
    return min(prob_tope, prob_base + boost)


def kind_de_evento_resistencia(evento: EventoAleatorioResistencia) -> str | None:
    if evento.tiempo_pregunta is not None:
        return "relampago"
    if evento.multiplicador_puntos is not None:
        return "doble"
    if (evento.opciones_ocultas or 0) > 0:
        return "opciones_ocultas"
    return None


def kinds_de_eventos_resistencia(
    eventos: tuple[EventoAleatorioResistencia, ...],
) -> frozenset[str]:
    vistos: set[str] = set()
    for evento in eventos:
        kind = kind_de_evento_resistencia(evento)
        if kind is not None:
            vistos.add(kind)
    return frozenset(vistos)


def actualizar_pity_eventos_resistencia(
    pity: PityEventosResistencia,
    eventos: tuple[EventoAleatorioResistencia, ...],
    *,
    numero_pregunta: int,
    kinds_vigentes: tuple[str, ...],
) -> None:
    """Tras una pregunta: resetea el pity del tipo visto o acumula +1 (idempotente)."""
    if numero_pregunta <= pity.ultima_pregunta_actualizada:
        return
    pity.ultima_pregunta_actualizada = numero_pregunta
    vistos = kinds_de_eventos_resistencia(eventos)
    hubo_malo = bool(vistos & _MALOS_PITY_RESISTENCIA)
    pity.preguntas_sin_malo = 0 if hubo_malo else pity.preguntas_sin_malo + 1
    pity.preguntas_sin_bueno = 0 if "doble" in vistos else pity.preguntas_sin_bueno + 1
    for kind in kinds_vigentes:
        if kind in vistos:
            pity.preguntas_sin_por_kind[kind] = 0
        else:
            pity.preguntas_sin_por_kind[kind] = pity.preguntas_sin_por_kind.get(kind, 0) + 1
    if numero_pregunta >= PREGUNTA_MIN_EVENTOS_ALEATORIOS:
        if "doble" in vistos:
            pity.preguntas_sin_por_kind["doble"] = 0
        else:
            pity.preguntas_sin_por_kind["doble"] = pity.preguntas_sin_por_kind.get("doble", 0) + 1


def _pesos_malos_resistencia_con_pity(
    pity: PityEventosResistencia,
    kinds: tuple[str, ...],
) -> dict[str, float]:
    return {
        kind: _PESO_BASE_MALO_KIND
        + pity.preguntas_sin_por_kind.get(kind, 0) * _PITY_INC_MALO_KIND
        for kind in kinds
    }


@dataclass(frozen=True)
class EventoAleatorioResistencia:
    """Efecto puntual que puede apilarse con otros en la misma pregunta."""

    etiqueta: str
    tiempo_pregunta: int | None = None
    multiplicador_puntos: int | None = None
    dificultades_permitidas: frozenset[str] | None = None
    max_complejidad: int | None = None
    opciones_ocultas: int | None = None
    min_max_complejidad: int | None = None
    unir_dificultades: frozenset[str] | None = None


@dataclass(frozen=True)
class BaselineEscaladaResistencia:
    """Reglas fijas de la escalada antes de eventos aleatorios."""

    nivel: int
    tiempo_pregunta_seg: int | None
    max_complejidad: int
    dificultades_permitidas: frozenset[str]
    opciones_ocultas: int
    efectos: tuple[str, ...]


@dataclass(frozen=True)
class EscaladaResistencia:
    """Parámetros de juego según el número de pregunta en la partida."""

    nivel: int  # Índice interno (0 = inicio); en pantalla usar ``nivel_visible``.
    tiempo_pregunta_seg: int | None
    max_complejidad: int
    dificultades_permitidas: frozenset[str]
    multiplicador_puntos: int
    opciones_ocultas: int = 0
    efectos: tuple[str, ...] = ()

    @property
    def nivel_visible(self) -> int:
        """Nivel mostrado al jugador (1 = inicio, sin usar 0)."""
        return self.nivel + 1


def es_preset_resistencia(preset) -> bool:
    return getattr(preset, "contexto_reglas", "") == "resistencia"


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


def parametros_eventos_aleatorios(
    numero_pregunta: int,
) -> tuple[float, float, int, int, float]:
    """Prob. buena/mala, cupos de eventos hostiles/favorables e intensidad.

    Los cupos limitan solo la generación de eventos aleatorios de escalada
    (relámpago, niebla, doble…). No comparten tope con recompensas ni con
    la cantidad de popups mostrados en pantalla.
    """
    from Comun.resistencia_motor import (
        factor_progreso_resistencia,
        probabilidad_buena_resistencia,
        probabilidad_mala_resistencia,
        progreso_probabilidad_resistencia,
    )

    if numero_pregunta < PREGUNTA_MIN_EVENTOS_ALEATORIOS:
        return 0.0, 0.0, 0, 0, 0.0
    progreso = progreso_probabilidad_resistencia(numero_pregunta)
    t = factor_progreso_resistencia(numero_pregunta)
    prob_buena = probabilidad_buena_resistencia(numero_pregunta)
    prob_mala = probabilidad_mala_resistencia(numero_pregunta)
    max_malos = 1 if progreso < 60 else 2
    max_buenos = 1
    intensidad = 0.30 + 0.70 * t
    return prob_buena, prob_mala, max_malos, max_buenos, intensidad


def _construir_evento(
    kind: str,
    intensidad: float,
    *,
    numero_pregunta: int,
) -> EventoAleatorioResistencia:
    from Comun.eventos_partida import evento_resistencia_aleatorio

    return evento_resistencia_aleatorio(kind, intensidad, numero_pregunta=numero_pregunta)


def _añadir_malos_aleatorios(
    eventos: list[EventoAleatorioResistencia],
    *,
    kinds: tuple[str, ...],
    cantidad: int,
    intensidad: float,
    numero_pregunta: int,
    rng: random.Random,
    familias_usadas: set[str],
    pity: PityEventosResistencia | None = None,
) -> None:
    from Comun.eventos_partida import familia_malo_resistencia

    disponibles = tuple(
        k
        for k in kinds
        if (fam := familia_malo_resistencia(k)) is None or fam not in familias_usadas
    )
    pesos = _pesos_malos_resistencia_con_pity(pity, disponibles) if pity is not None else None
    for kind in elegir_malos_resistencia_exclusivos(
        disponibles, cantidad, rng, pesos=pesos
    ):
        eventos.append(
            _construir_evento(kind, intensidad, numero_pregunta=numero_pregunta)
        )
        familia = familia_malo_resistencia(kind)
        if familia is not None:
            familias_usadas.add(familia)


def eventos_aleatorios_para_pregunta(
    numero_pregunta: int,
    *,
    semilla_partida: int | None = None,
    racha: int = 0,
    baseline: BaselineEscaladaResistencia | None = None,
    pity: PityEventosResistencia | None = None,
) -> tuple[EventoAleatorioResistencia, ...]:
    """Efectos de escalada; con racha extrema se apilan hostiles más allá del tope."""
    from Comun.resistencia_motor import exceso_presion_racha, intensidad_presion_racha

    if pity is not None and pity._cache_pregunta == numero_pregunta:
        return pity._cache_eventos

    if baseline is None:
        baseline = baseline_escalada_resistencia(numero_pregunta)
    prob_buena, prob_mala, max_malos, max_buenos, intensidad = parametros_eventos_aleatorios(
        numero_pregunta
    )
    t_presion = intensidad_presion_racha(racha)
    if t_presion > 1.0:
        max_buenos = 0
    if max_malos <= 0 and max_buenos <= 0 and t_presion <= 1.0:
        return ()
    kinds = malos_resistencia_vigentes(
        numero_pregunta,
        tiempo_baseline=baseline.tiempo_pregunta_seg,
        opciones_baseline=baseline.opciones_ocultas,
    )
    base = semilla_partida or 0
    rng = random.Random(numero_pregunta * 7919 + 17 + base * 10007)
    eventos: list[EventoAleatorioResistencia] = []
    familias_usadas: set[str] = set()

    prob_mala_eff = prob_mala
    if pity is not None and prob_mala > 0.0:
        prob_mala_eff = prob_gate_evento_resistencia_con_pity(
            prob_base=prob_mala,
            preguntas_sin_ver=pity.preguntas_sin_malo,
            incremento_por_pregunta=_PITY_INC_GATE_MALO,
            max_boost=_PROB_GATE_MAX_BOOST_MALO,
        )

    if prob_mala_eff > 0.0 and max_malos > 0 and kinds and rng.random() <= prob_mala_eff:
        n_malos = 1
        if max_malos > 1 and rng.random() < min(0.35, intensidad * 0.4):
            n_malos = min(2, max_malos, len(kinds))
        _añadir_malos_aleatorios(
            eventos,
            kinds=kinds,
            cantidad=n_malos,
            intensidad=intensidad,
            numero_pregunta=numero_pregunta,
            rng=rng,
            familias_usadas=familias_usadas,
            pity=pity,
        )

    from Comun.resistencia_motor import probabilidad_evento_bueno_escalada

    prob_evento_bueno = probabilidad_evento_bueno_escalada(numero_pregunta)
    prob_bueno_eff = prob_evento_bueno
    if pity is not None and prob_evento_bueno > 0.0:
        prob_bueno_eff = prob_gate_evento_resistencia_con_pity(
            prob_base=prob_evento_bueno,
            preguntas_sin_ver=pity.preguntas_sin_bueno,
            incremento_por_pregunta=_PITY_INC_GATE_BUENO,
            max_boost=_PROB_GATE_MAX_BOOST_BUENO,
            prob_tope=0.95,
        )
    if prob_bueno_eff > 0.0 and max_buenos > 0 and rng.random() <= prob_bueno_eff:
        eventos.append(
            _construir_evento("doble", intensidad, numero_pregunta=numero_pregunta)
        )

    exceso = exceso_presion_racha(racha)
    if exceso > 0.0 and kinds:
        rng_extra = random.Random(
            numero_pregunta * 8311 + 29 + base * 10007 + racha * 17
        )
        n_extra = min(8, 1 + int(exceso * 5))
        int_extra = min(1.0, intensidad + exceso * 0.2)
        _añadir_malos_aleatorios(
            eventos,
            kinds=kinds,
            cantidad=n_extra,
            intensidad=int_extra,
            numero_pregunta=numero_pregunta,
            rng=rng_extra,
            familias_usadas=familias_usadas,
            pity=pity,
        )

    if pity is not None:
        actualizar_pity_eventos_resistencia(
            pity,
            tuple(eventos),
            numero_pregunta=numero_pregunta,
            kinds_vigentes=kinds,
        )
        pity._cache_pregunta = numero_pregunta
        pity._cache_eventos = tuple(eventos)

    return tuple(eventos)


def _fusionar_evento_en_escalada(
    evento: EventoAleatorioResistencia,
    *,
    tiempo: int | None,
    max_cx: int,
    permitidas: frozenset[str],
    mult: int,
    opciones_ocultas: int,
    efectos: list[str],
) -> tuple[int | None, int, frozenset[str], int, int]:
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
    return tiempo, max_cx, permitidas, mult, opciones_ocultas


def baseline_escalada_resistencia(numero_pregunta: int) -> BaselineEscaladaResistencia:
    """Reglas fijas por progreso: tiempo y niebla pasan a ser permanentes en fases altas."""
    progreso = max(0, numero_pregunta - 1)
    tiempo: int | None = None
    max_cx = 2
    permitidas = frozenset(_DIFICULTADES)
    nivel = 0
    opciones_ocultas = 0
    efectos: list[str] = []

    if progreso >= 700:
        nivel = 7
        tiempo = 10
        max_cx = 99
        permitidas = frozenset({"Dificil"})
        efectos.append("Nivel extremo: solo difíciles, 10 s")
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

    if progreso >= 150:
        opciones_ocultas = max(opciones_ocultas, 1)
        efectos.append("Niebla: 1 respuesta oculta")

    return BaselineEscaladaResistencia(
        nivel=nivel,
        tiempo_pregunta_seg=tiempo,
        max_complejidad=max_cx,
        dificultades_permitidas=permitidas,
        opciones_ocultas=opciones_ocultas,
        efectos=tuple(efectos),
    )


def escalada_para_pregunta(
    numero_pregunta: int,
    *,
    semilla_partida: int | None = None,
    racha: int = 0,
    pity: PityEventosResistencia | None = None,
) -> EscaladaResistencia:
    """Calcula reglas vigentes según el número de pregunta (1 = inicio fácil, sin tiempo)."""
    base = baseline_escalada_resistencia(numero_pregunta)
    tiempo = base.tiempo_pregunta_seg
    max_cx = base.max_complejidad
    permitidas = base.dificultades_permitidas
    mult = 1
    opciones_ocultas = base.opciones_ocultas
    efectos = list(base.efectos)

    for evento in eventos_aleatorios_para_pregunta(
        numero_pregunta,
        semilla_partida=semilla_partida,
        racha=racha,
        baseline=base,
        pity=pity,
    ):
        (
            tiempo,
            max_cx,
            permitidas,
            mult,
            opciones_ocultas,
        ) = _fusionar_evento_en_escalada(
            evento,
            tiempo=tiempo,
            max_cx=max_cx,
            permitidas=permitidas,
            mult=mult,
            opciones_ocultas=opciones_ocultas,
            efectos=efectos,
        )

    return EscaladaResistencia(
        nivel=base.nivel,
        tiempo_pregunta_seg=tiempo,
        max_complejidad=max_cx,
        dificultades_permitidas=permitidas,
        multiplicador_puntos=mult,
        opciones_ocultas=opciones_ocultas,
        efectos=tuple(efectos),
    )


def aplicar_escalada_a_reglas(base: ReglasPartida, escalada: EscaladaResistencia) -> ReglasPartida:
    return ReglasPartida(
        vidas=base.vidas,
        tiempo_por_pregunta_seg=escalada.tiempo_pregunta_seg,
        tiempo_total_seg=None,
        sistema_puntuacion=base.sistema_puntuacion,
        mostrar_solucion_tras_fallo=True,
        mostrar_aciertos_en_curso=base.mostrar_aciertos_en_curso,
        correccion_al_final=False,
        dificultad_progresiva=True,
    )


def partes_texto_efectos_escalada(escalada: EscaladaResistencia) -> list[str]:
    if escalada.efectos:
        return list(escalada.efectos)
    if escalada.nivel == 0:
        return ["Inicio: fácil, sin límite de tiempo"]
    return [f"Nivel {escalada.nivel_visible}"]


def texto_efectos_escalada(escalada: EscaladaResistencia) -> str:
    return " · ".join(partes_texto_efectos_escalada(escalada))


def indices_candidatos_resistencia(
    pool: list[Pregunta],
    estado: EstadoSeleccionPool,
    escalada: EscaladaResistencia,
    numero_pregunta: int,
    *,
    solo_no_usadas: bool,
    er=None,
) -> list[int]:
    return _indices_candidatos(
        pool, estado, escalada, numero_pregunta, solo_no_usadas=solo_no_usadas, er=er
    )


def _indices_candidatos(
    pool: list[Pregunta],
    estado: EstadoSeleccionPool,
    escalada: EscaladaResistencia,
    numero_pregunta: int,
    *,
    solo_no_usadas: bool,
    er=None,
) -> list[int]:
    from Comun.resistencia_motor import pregunta_compatible_bloque

    bloqueadas = set(estado.historial_reciente)
    candidatas: list[int] = []
    progreso = max(0, numero_pregunta - 1)
    banco = getattr(er, "banco_resistencia", None) if er is not None else None
    for idx, p in enumerate(pool):
        if banco is not None and not banco.indice_habilitado(idx, numero_pregunta):
            continue
        if idx in bloqueadas:
            continue
        if p.racha_minima_resistencia > progreso:
            continue
        if p.dificultad not in escalada.dificultades_permitidas:
            continue
        if complejidad_pregunta(p) > escalada.max_complejidad:
            continue
        if er is not None and not pregunta_compatible_bloque(p, er):
            continue
        if solo_no_usadas and idx in estado.usadas:
            continue
        candidatas.append(idx)
    return candidatas


def _elegir_entre_candidatas(
    pool: list[Pregunta],
    candidatas: list[int],
    numero_pregunta: int,
    *,
    er=None,
) -> int:
    from Comun.resistencia_motor import rng_partida

    exclusivas = [i for i in candidatas if pool[i].exclusiva_resistencia]
    normales = [i for i in candidatas if not pool[i].exclusiva_resistencia]
    if exclusivas and normales:
        prob = probabilidad_pregunta_exclusiva(numero_pregunta)
        if er is not None and er.semilla_partida is not None:
            roll = rng_partida(er, numero_pregunta * 11).random()
        else:
            roll = random.random()
        grupo = exclusivas if roll < prob else normales
        candidatas = grupo
    if er is not None and er.semilla_partida is not None:
        return rng_partida(er, numero_pregunta * 13).choice(candidatas)
    return random.choice(candidatas)


def elegir_indice_resistencia(
    pool: list[Pregunta],
    estado: EstadoSeleccionPool,
    escalada: EscaladaResistencia,
    numero_pregunta: int,
    *,
    er=None,
) -> int | None:
    if not pool:
        return None
    candidatas = _indices_candidatos(
        pool, estado, escalada, numero_pregunta, solo_no_usadas=True, er=er
    )
    if not candidatas:
        estado.usadas.clear()
        candidatas = _indices_candidatos(
            pool, estado, escalada, numero_pregunta, solo_no_usadas=False, er=er
        )
    if not candidatas:
        progreso = max(0, numero_pregunta - 1)
        from Comun.resistencia_motor import pregunta_compatible_bloque

        candidatas = [
            idx
            for idx, p in enumerate(pool)
            if p.racha_minima_resistencia <= progreso
            and (er is None or pregunta_compatible_bloque(p, er))
        ]
    if not candidatas:
        return None
    idx = _elegir_entre_candidatas(pool, candidatas, numero_pregunta, er=er)
    estado.usadas.add(idx)
    estado.historial_reciente.append(idx)
    return idx


def crear_seleccion_resistencia(pool: list[Pregunta]) -> EstadoSeleccionPool:
    return crear_estado_seleccion(len(pool))


def max_complejidad_resistencia(pool: list[Pregunta]) -> int:
    return max_complejidad_pool(pool)


def elegir_indice_similar(
    pool: list[Pregunta],
    estado: EstadoSeleccionPool,
    escalada: EscaladaResistencia,
    numero_pregunta: int,
    idx_actual: int,
    *,
    er=None,
) -> int | None:
    """Sustituye por otra pregunta con la misma materia y tipo."""
    from Comun.resistencia_motor import rng_partida

    actual = pool[idx_actual]
    candidatas = indices_candidatos_resistencia(
        pool,
        estado,
        escalada,
        numero_pregunta,
        solo_no_usadas=True,
        er=er,
    )
    similares = [
        i
        for i in candidatas
        if i != idx_actual
        and pool[i].materia == actual.materia
        and pool[i].tipo == actual.tipo
    ]
    if not similares:
        candidatas = indices_candidatos_resistencia(
            pool,
            estado,
            escalada,
            numero_pregunta,
            solo_no_usadas=False,
            er=er,
        )
        similares = [
            i
            for i in candidatas
            if i != idx_actual
            and pool[i].materia == actual.materia
            and pool[i].tipo == actual.tipo
        ]
    if not similares:
        similares = [
            i
            for i in candidatas
            if i != idx_actual and pool[i].materia == actual.materia
        ]
    if not similares:
        return None
    rng = rng_partida(er, numero_pregunta * 19 + idx_actual) if er else random.Random()
    elegido = rng.choice(similares)
    estado.usadas.discard(idx_actual)
    estado.usadas.add(elegido)
    if estado.historial_reciente and estado.historial_reciente[-1] == idx_actual:
        estado.historial_reciente[-1] = elegido
    else:
        estado.historial_reciente.append(elegido)
    return elegido


def avisos_pre_pregunta_resistencia(
    p: Pregunta,
    numero_pregunta: int,
    *,
    avisos_extra: list[str] | None = None,
    er=None,
) -> list[str]:
    """Mensajes para popup antes de mostrar la pregunta."""
    from Comun.resistencia_motor import (
        emoji_aviso_exclusiva,
        formatear_aviso_evento,
        prefijar_emoji,
    )

    avisos: list[str] = []
    if avisos_extra:
        avisos.extend(avisos_extra)
    for evento in eventos_aleatorios_para_pregunta(
        numero_pregunta,
        semilla_partida=er.semilla_partida if er else None,
        racha=er.racha if er is not None else 0,
        baseline=baseline_escalada_resistencia(numero_pregunta),
        pity=er.pity_eventos if er is not None else None,
    ):
        avisos.append(formatear_aviso_evento(evento.etiqueta))
    if p.exclusiva_resistencia:
        tier = etiqueta_tier_exclusiva(p)
        if tier:
            avisos.append(
                prefijar_emoji(
                    f"Pregunta exclusiva — {tier}",
                    emoji_aviso_exclusiva(),
                )
            )
    return avisos
