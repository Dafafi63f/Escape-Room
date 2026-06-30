#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memoria acumulada de la cadena «Otro examen dirigido»."""

from __future__ import annotations

import random
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from Comun.informe_examen import RegistroRespuesta

# Probabilidad de elegir pregunta del mismo tipo/dificultad que un fallo previo.
PROB_PREGUNTA_PERFIL_FALLO = 0.72

# Solo se excluyen preguntas de las últimas N sesiones; las más antiguas pueden repetirse.
VENTANA_EXCLUSION_SESIONES_DIRIGIDO = 3

# Mezcla refuerzo (fallos) / exploración (materias poco vistas en la cadena).
FRACCION_EXPLORACION_MATERIAS_DIRIGIDO = 0.32

# Probabilidad de elegir un perfil distinto al de los fallos al sacar pregunta.
PROB_EXPLORACION_PERFIL_PREGUNTA = 0.22

_STOPWORDS_ES = frozenset({
    "que", "cual", "cuál", "como", "cómo", "para", "por", "con", "sin", "del",
    "las", "los", "una", "uno", "son", "sus", "este", "esta", "está", "ese",
    "esa", "the", "and", "hay", "más", "mas", "menos", "todo", "toda", "cada",
    "donde", "dónde", "cuando", "cuándo", "sobre", "entre", "desde", "hasta",
    "ante", "bajo", "tras", "pero", "porque", "puede", "pueden", "debe", "deben",
    "ser", "está", "esta", "están", "fue", "era", "han", "has", "hemos",
})

_RE_PALABRA = re.compile(r"[a-záéíóúüñ]+", re.IGNORECASE)
_RE_NUMERO = re.compile(r"\d+")


def tokens_enunciado(pregunta: object) -> frozenset[str]:
    """Huella léxica del enunciado inferida del dataset (sin columna Materia)."""
    texto = (getattr(pregunta, "texto", "") or "").lower()
    palabras = {
        w.lower()
        for w in _RE_PALABRA.findall(texto)
        if len(w) >= 3 and w.lower() not in _STOPWORDS_ES
    }
    numeros = {f"#{n}" for n in _RE_NUMERO.findall(texto)}
    return frozenset(palabras | numeros)


def similitud_contenido(pregunta_a: object, pregunta_b: object) -> float:
    """Similitud de Jaccard entre los tokens de dos enunciados."""
    ta = tokens_enunciado(pregunta_a)
    tb = tokens_enunciado(pregunta_b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def etiqueta_concepto(token: str) -> str:
    """Etiqueta legible de un token para estadísticas y paneles."""
    if token.startswith("#"):
        return f"número {token[1:]}"
    return token


def conceptos_registro(registro: RegistroRespuesta) -> frozenset[str]:
    """Palabras clave del enunciado atribuibles a una respuesta."""
    return tokens_enunciado(registro.pregunta)


def calcular_pesos_preguntas_planas(
    pool: list,
    registros: list[RegistroRespuesta],
) -> list[float]:
    """Pesos por pregunta según fallos y similitud de contenido acumulada en la cadena."""
    preguntas_falladas = [r.pregunta for r in registros if not r.acierto]
    tokens_cadena: set[str] = set()
    for registro in registros:
        tokens_cadena |= tokens_enunciado(registro.pregunta)

    fraccion = FRACCION_EXPLORACION_MATERIAS_DIRIGIDO
    pesos: list[float] = []
    for pregunta in pool:
        perfil = tokens_enunciado(pregunta)
        if not perfil:
            pesos.append(0.15)
            continue

        if preguntas_falladas:
            sim_max = max(
                similitud_contenido(pregunta, fallo) for fallo in preguntas_falladas
            )
            refuerzo = max(0.05, 0.18 + 0.82 * sim_max)
        else:
            refuerzo = 0.15

        nuevos = perfil - tokens_cadena
        if nuevos:
            exploracion = min(1.0, 0.45 + len(nuevos) / len(perfil))
        else:
            exploracion = 0.2

        pesos.append(max(0.05, (1.0 - fraccion) * refuerzo + fraccion * exploracion))
    return pesos


def _muestra_ponderada_sin_reemplazo(
    pool: list,
    pesos: list[float],
    n: int,
    rng: random.Random,
) -> list:
    seleccion: list = []
    restantes = list(pool)
    pesos_rest = list(pesos)
    while len(seleccion) < n and restantes:
        idx = rng.choices(range(len(restantes)), weights=pesos_rest, k=1)[0]
        seleccion.append(restantes.pop(idx))
        pesos_rest.pop(idx)
    return seleccion


def construir_seleccion_plana_dirigida(
    preguntas: list,
    n: int,
    rng: random.Random,
    pregunta_key: Callable,
    registros_dirigido: list[RegistroRespuesta],
    preguntas_excluir: list | None,
) -> list:
    """Examen plano (CSV mínimo) priorizando contenido fallado en la cadena."""
    if n <= 0:
        raise ValueError("n_preguntas debe ser positivo.")
    unicas: dict[object, object] = {}
    for pregunta in preguntas:
        clave = pregunta_key(pregunta)
        if clave not in unicas:
            unicas[clave] = pregunta
    excluidas = {pregunta_key(p) for p in (preguntas_excluir or [])}
    pool = [p for clave, p in unicas.items() if clave not in excluidas]
    if len(pool) < n:
        raise ValueError(
            "No quedan suficientes preguntas nuevas en la ventana reciente de exámenes "
            f"dirigidos ({len(excluidas)} bloqueadas, {len(pool)}/{n} disponibles). "
            "Prueba «Repetir partida» o vuelve al menú."
        )
    pesos = calcular_pesos_preguntas_planas(pool, registros_dirigido)
    return _muestra_ponderada_sin_reemplazo(pool, pesos, n, rng)

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
