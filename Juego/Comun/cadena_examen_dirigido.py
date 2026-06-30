#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memoria acumulada de la cadena «Otro examen dirigido»."""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass

from Comun.informe_examen import RegistroRespuesta

# Probabilidad de elegir pregunta del mismo tipo/dificultad que un fallo previo.
PROB_PREGUNTA_PERFIL_FALLO = 0.72

# Solo se excluyen preguntas de las últimas N sesiones; las más antiguas pueden repetirse.
VENTANA_EXCLUSION_SESIONES_DIRIGIDO = 3

# Mezcla refuerzo (fallos) / exploración (materias poco vistas en la cadena).
FRACCION_EXPLORACION_MATERIAS_DIRIGIDO = 0.32

# Probabilidad de elegir un perfil distinto al de los fallos al sacar pregunta.
PROB_EXPLORACION_PERFIL_PREGUNTA = 0.22


@dataclass(frozen=True)
class CadenaExamenDirigido:
    """Sesiones acumuladas de una cadena de exámenes dirigidos."""

    sesiones: tuple[tuple[RegistroRespuesta, ...], ...] = ()

    @property
    def registros(self) -> tuple[RegistroRespuesta, ...]:
        return tuple(r for sesion in self.sesiones for r in sesion)

    @property
    def n_sesiones(self) -> int:
        return len(self.sesiones)

    @classmethod
    def desde_primera_sesion(cls, registros: list[RegistroRespuesta]) -> CadenaExamenDirigido:
        return cls(sesiones=(tuple(registros),))

    def extender(self, registros_sesion: list[RegistroRespuesta]) -> CadenaExamenDirigido:
        if not registros_sesion:
            return self
        return CadenaExamenDirigido(sesiones=self.sesiones + (tuple(registros_sesion),))

    def preguntas_vistas(self) -> list:
        return [r.pregunta for r in self.registros]

    def preguntas_en_ventana_exclusion(
        self,
        ventana: int = VENTANA_EXCLUSION_SESIONES_DIRIGIDO,
    ) -> list:
        """Preguntas no reutilizables: solo las de las últimas ``ventana`` sesiones."""
        if not self.sesiones or ventana <= 0:
            return []
        recientes = self.sesiones[-ventana:]
        return [r.pregunta for sesion in recientes for r in sesion]


def extender_cadena(
    cadena: CadenaExamenDirigido | None,
    registros_sesion: list[RegistroRespuesta],
) -> CadenaExamenDirigido:
    """Añade la sesión recién terminada a la cadena (o inicia una nueva)."""
    if not registros_sesion:
        if cadena is not None:
            return cadena
        return CadenaExamenDirigido()
    if cadena is None:
        return CadenaExamenDirigido.desde_primera_sesion(registros_sesion)
    return cadena.extender(registros_sesion)


def perfiles_fallo_desde_registros(
    registros: list[RegistroRespuesta],
) -> dict[str, tuple[tuple[str, str], ...]]:
    """Por materia, perfiles (tipo, dificultad) de preguntas falladas en la cadena."""
    buckets: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for registro in registros:
        if registro.acierto:
            continue
        materia = (getattr(registro.pregunta, "materia", "") or "").strip()
        if not materia:
            continue
        tipo = (getattr(registro.pregunta, "tipo", "") or "").strip()
        dificultad = (getattr(registro.pregunta, "dificultad", "") or "").strip()
        buckets[materia].add((tipo, dificultad))
    return {m: tuple(sorted(perfiles)) for m, perfiles in buckets.items()}


def intentos_por_materia(registros: list[RegistroRespuesta]) -> dict[str, int]:
    """Cuántas preguntas de cada materia lleva la cadena."""
    cuentas: dict[str, int] = defaultdict(int)
    for registro in registros:
        materia = (getattr(registro.pregunta, "materia", "") or "").strip()
        if materia:
            cuentas[materia] += 1
    return dict(cuentas)


def calcular_pesos_materia_dirigido(
    registros: list[RegistroRespuesta],
    candidatas: list[str],
) -> dict[str, float]:
    """Refuerzo por fallos + exploración de materias poco o nunca vistas en la cadena."""
    from Comun.generador_examen_historia import calcular_pesos_desde_registros

    pesos_fallo = calcular_pesos_desde_registros(registros)
    intentos = intentos_por_materia(registros)
    max_intentos = max(intentos.values()) if intentos else 0
    fraccion = FRACCION_EXPLORACION_MATERIAS_DIRIGIDO
    pesos: dict[str, float] = {}
    for materia in candidatas:
        refuerzo = max(0.05, pesos_fallo.get(materia, 0.15))
        n = intentos.get(materia, 0)
        if n == 0:
            exploracion = 1.0
        elif max_intentos > 0:
            exploracion = max(0.12, 1.0 - 0.85 * (n / max_intentos))
        else:
            exploracion = 0.5
        pesos[materia] = max(
            0.05,
            (1.0 - fraccion) * refuerzo + fraccion * exploracion,
        )
    return pesos


def _reserva_materias_sin_exposicion(n_materias: int, n_sin_exposicion: int) -> int:
    """Plazas reservadas para asignaturas aún no vistas en la cadena."""
    if n_sin_exposicion <= 0 or n_materias <= 0:
        return 0
    return min(n_sin_exposicion, max(1, n_materias // 2), n_materias)


def elegir_materias_para_examen_dirigido(
    candidatas: list[str],
    pesos: dict[str, float],
    n: int,
    registros: list[RegistroRespuesta],
    rng: random.Random,
) -> list[str]:
    """Elige materias mezclando refuerzo y asignaturas aún no exploradas en la cadena."""
    if n >= len(candidatas):
        return list(candidatas)

    intentos = intentos_por_materia(registros)
    sin_exposicion = [m for m in candidatas if intentos.get(m, 0) == 0]
    reserva = _reserva_materias_sin_exposicion(n, len(sin_exposicion))

    elegidas: list[str] = []
    restantes = list(candidatas)

    def _elegir_ponderada(pool: list[str]) -> str:
        ws = [pesos.get(m, 0.15) for m in pool]
        idx = rng.choices(range(len(pool)), weights=ws, k=1)[0]
        return pool.pop(idx)

    pool_nuevas = [m for m in sin_exposicion if m in restantes]
    while len(elegidas) < reserva and pool_nuevas:
        idx = rng.randrange(len(pool_nuevas))
        materia = pool_nuevas.pop(idx)
        elegidas.append(materia)
        restantes.remove(materia)

    while len(elegidas) < n and restantes:
        elegidas.append(_elegir_ponderada(restantes))

    return elegidas
