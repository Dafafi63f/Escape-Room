#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pool de preguntas del modo libre (filtros y selección aleatoria)."""

from __future__ import annotations

import random
from collections import deque
from collections.abc import MutableSequence
from dataclasses import dataclass, field
from pathlib import Path

from Comun.datos import cargar_banco_todo
from Comun.dificultad import (
    debe_filtrar_por_nivel,
    max_complejidad_pool,
    normalizar_niveles_seleccionados,
    pregunta_permitida_por_nivel,
    techo_complejidad_partida,
)
from Comun.modelos import BancoPreguntas, Pregunta

__all__ = [
    "EstadoSeleccionPool",
    "cargar_pool_por_banco",
    "crear_estado_seleccion",
    "elegir_indice_siguiente",
    "filtrar_pool",
    "filtrar_pool_asistente",
    "max_complejidad_pool",
    "opciones_curso_semestre",
    "opciones_tematica",
    "opciones_tipo",
]


def filtrar_pool(
    preguntas: list[Pregunta],
    *,
    tematicas: set[str] | None = None,
    cursos_semestres: set[str] | None = None,
    tipos: set[str] | None = None,
) -> list[Pregunta]:
    """Filtra por una o varias opciones en cada eje (conjunto vacío = sin filtro)."""
    resultado = preguntas
    if tematicas:
        resultado = [p for p in resultado if p.tematica in tematicas]
    if cursos_semestres:
        resultado = [
            p
            for p in resultado
            if f"{p.curso}-{p.semestre}" in cursos_semestres
        ]
    if tipos:
        resultado = [p for p in resultado if p.tipo in tipos]
    return resultado


def filtrar_pool_asistente(
    preguntas: list[Pregunta],
    *,
    tematica: str | None = None,
    curso: str | None = None,
    semestre: str | None = None,
    tipo: str | None = None,
) -> list[Pregunta]:
    """Filtro de un solo valor por eje (asistente de configuración)."""
    return [
        p
        for p in preguntas
        if (tematica is None or p.tematica == tematica)
        and (curso is None or p.curso == curso)
        and (semestre is None or p.semestre == semestre)
        and (tipo is None or p.tipo == tipo)
    ]


def cargar_pool_por_banco(
    banco: BancoPreguntas,
    *,
    preguntas_dataset: list[Pregunta],
    path_preguntas_csv: Path,
    path_plantillas_json: Path,
    materias_meta: dict[str, dict[str, str]],
) -> list[Pregunta]:
    if banco == BancoPreguntas.DATASET:
        return list(preguntas_dataset)
    if banco == BancoPreguntas.PLANTILLAS_TODO:
        try:
            return cargar_banco_todo(
                path_preguntas_csv,
                path_plantillas_json,
                materias_meta,
            )
        except Exception as e:
            print(f"[Juego] Fallo al cargar banco {banco}: {e}")
            return list(preguntas_dataset)
    print(f"[Juego] Banco no soportado: {banco}")
    return list(preguntas_dataset)


def opciones_tematica(pool: list[Pregunta]) -> list[str]:
    return sorted({p.tematica for p in pool if p.tematica})


def opciones_curso_semestre(pool: list[Pregunta]) -> list[str]:
    return sorted(
        {f"{p.curso}-{p.semestre}" for p in pool if p.curso and p.semestre}
    )


def opciones_tipo(pool: list[Pregunta]) -> list[str]:
    return sorted({p.tipo for p in pool if p.tipo})


@dataclass
class EstadoSeleccionPool:
    usadas: set[int] = field(default_factory=set)
    historial_reciente: MutableSequence[int] = field(default_factory=deque)


def crear_estado_seleccion(tam_pool: int) -> EstadoSeleccionPool:
    ventana = max(1, tam_pool // 4) if tam_pool else 1
    return EstadoSeleccionPool(historial_reciente=deque(maxlen=ventana))


def elegir_indice_siguiente(
    pool: list[Pregunta],
    estado: EstadoSeleccionPool,
    *,
    modo_infinito: bool,
    dificultad_progresiva: bool = False,
    niveles_complejidad: frozenset[int] | set[int] | None = None,
    respondidas: int = 0,
) -> int | None:
    if not pool:
        return None
    niveles = normalizar_niveles_seleccionados(niveles_complejidad, pool)
    techo = techo_complejidad_partida(
        dificultad_progresiva=dificultad_progresiva,
        respondidas=respondidas,
        niveles_seleccion=niveles,
    )
    filtrar = debe_filtrar_por_nivel(pool, niveles, dificultad_progresiva)

    def _permitida(p: Pregunta) -> bool:
        if not filtrar:
            return True
        return pregunta_permitida_por_nivel(
            p,
            niveles_seleccion=niveles,
            techo=techo,
            dificultad_progresiva=dificultad_progresiva,
        )

    bloqueadas = set(estado.historial_reciente)
    candidatas = [
        idx
        for idx, p in enumerate(pool)
        if idx not in estado.usadas
        and idx not in bloqueadas
        and _permitida(p)
    ]
    if not candidatas:
        if modo_infinito:
            estado.usadas.clear()
            candidatas = [
                idx
                for idx, p in enumerate(pool)
                if idx not in bloqueadas
                and _permitida(p)
            ]
            if not candidatas:
                return None
        elif filtrar:
            return None
        else:
            candidatas = [idx for idx in range(len(pool)) if idx not in estado.usadas]
            if not candidatas:
                return None
    idx = random.choice(candidatas)
    estado.usadas.add(idx)
    estado.historial_reciente.append(idx)
    return idx
