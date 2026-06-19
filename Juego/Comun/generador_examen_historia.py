#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de generación de exámenes balanceados (modo historia).

Usa el histórico de qualificacions (MatCAD) para ponderar materias según el
perfil pedagógico y el banco de preguntas revisado con slots canónicos
(Teoria/Calculo × Facil/Media/Dificil).

Importado por modo_historia.py. Para probar sin jugar: Files/cli_examen_historia.py

Versión 1: perfiles agregados (sin expediente individual). Las versiones
futuras podrán importar notas por alumno.
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from Comun.perfiles_historia import PerfilPedagogico, describir_perfil
from Comun.rutas import resolver_historico_qualificacions

# Réplica mínima de objetivos_balanceo (el .exe no incluye Files/).
SLOTS_CANONICOS_12: tuple[tuple[str, str], ...] = (
    ("Teoria", "Facil"),
    ("Teoria", "Facil"),
    ("Teoria", "Media"),
    ("Teoria", "Media"),
    ("Teoria", "Dificil"),
    ("Teoria", "Dificil"),
    ("Calculo", "Facil"),
    ("Calculo", "Facil"),
    ("Calculo", "Media"),
    ("Calculo", "Media"),
    ("Calculo", "Dificil"),
    ("Calculo", "Dificil"),
)

SLOTS_EXAMEN_4: tuple[tuple[str, str], ...] = (
    ("Teoria", "Facil"),
    ("Teoria", "Media"),
    ("Calculo", "Facil"),
    ("Calculo", "Media"),
)

SLOTS_EXAMEN_6: tuple[tuple[str, str], ...] = (
    ("Teoria", "Facil"),
    ("Teoria", "Media"),
    ("Teoria", "Dificil"),
    ("Calculo", "Facil"),
    ("Calculo", "Media"),
    ("Calculo", "Dificil"),
)

# Nombre de asignatura en el CSV histórico (columna «Unnamed: 9») → Materia del listado.
ALIASES_NOMBRE_HISTORICO: dict[str, str] = {
    "Computació d'Altes Prestacions": "Computació i Simulació d'Altes Prestacions",
    "Simulació d'Altes Prestacions": "Computació i Simulació d'Altes Prestacions",
}

COL_NOMBRE_ASIGNATURA = "Unnamed: 9"
COL_NOTA = "Qualificació"
UMBRAL_SUSPENS = 5.0


@dataclass(frozen=True)
class EstadisticaMateria:
    materia: str
    n_registros: int
    media: float
    tasa_suspens: float
    indice_dificultad: float


@dataclass
class PlanExamen:
    perfil: PerfilPedagogico
    materias: list[str]
    slots_por_materia: tuple[tuple[str, str], ...]
    preguntas: list  # list[Pregunta] en runtime


def normalizar_nombre_historico(nombre: str) -> str:
    nombre = (nombre or "").strip()
    return ALIASES_NOMBRE_HISTORICO.get(nombre, nombre)


def cargar_estadisticas_historicas(
    path_csv: Path | None = None,
    *,
    materias_validas: set[str] | None = None,
) -> dict[str, EstadisticaMateria]:
    path = path_csv or resolver_historico_qualificacions()
    acum: dict[str, list[float]] = defaultdict(list)

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            nombre = normalizar_nombre_historico(row.get(COL_NOMBRE_ASIGNATURA, ""))
            if not nombre:
                continue
            if materias_validas is not None and nombre not in materias_validas:
                continue
            raw = (row.get(COL_NOTA) or "").strip().replace(",", ".")
            try:
                nota = float(raw)
            except ValueError:
                continue
            acum[nombre].append(nota)

    stats: dict[str, EstadisticaMateria] = {}
    for materia, notas in acum.items():
        n = len(notas)
        media = sum(notas) / n
        suspensos = sum(1 for x in notas if x < UMBRAL_SUSPENS)
        tasa = suspensos / n
        # Índice 0..1: más alto ⇒ más difícil según el histórico agregado.
        indice = min(1.0, max(0.0, 0.55 * tasa + 0.45 * ((UMBRAL_SUSPENS - media) / 3.0)))
        stats[materia] = EstadisticaMateria(
            materia=materia,
            n_registros=n,
            media=round(media, 2),
            tasa_suspens=round(tasa, 3),
            indice_dificultad=round(indice, 3),
        )
    return stats


def slots_para_tamano(preguntas_objetivo: int, n_materias: int) -> tuple[tuple[str, str], ...]:
    """Elige plantilla de slots según preguntas por materia."""
    if n_materias <= 0:
        raise ValueError("n_materias debe ser positivo")
    por_materia = preguntas_objetivo // n_materias
    if por_materia >= 12:
        return SLOTS_CANONICOS_12
    if por_materia >= 6:
        return SLOTS_EXAMEN_6
    if por_materia >= 4:
        return SLOTS_EXAMEN_4
    return (("Teoria", "Media"),)


def calcular_pesos_materia(
    materias: list[str],
    stats: dict[str, EstadisticaMateria],
    perfil: PerfilPedagogico,
) -> dict[str, float]:
    pesos: dict[str, float] = {}
    for m in materias:
        st = stats.get(m)
        if perfil == PerfilPedagogico.BALANCEADO:
            w = 1.0
        elif perfil == PerfilPedagogico.REFUERZO:
            w = 0.35 + (st.indice_dificultad if st else 0.5)
        elif perfil == PerfilPedagogico.DESAFIO:
            w = 0.35 + (1.0 - (st.indice_dificultad if st else 0.5))
        elif perfil in (PerfilPedagogico.POR_CURSO, PerfilPedagogico.SIMULACRO):
            w = 1.0
        else:
            w = 1.0
        pesos[m] = max(0.05, w)
    return pesos


def elegir_materias_ponderadas(
    candidatas: list[str],
    pesos: dict[str, float],
    n: int,
    rng: random.Random,
) -> list[str]:
    if n >= len(candidatas):
        return list(candidatas)
    elegidas: list[str] = []
    restantes = list(candidatas)
    while len(elegidas) < n and restantes:
        ws = [pesos.get(m, 1.0) for m in restantes]
        total = sum(ws)
        probs = [w / total for w in ws]
        idx = rng.choices(range(len(restantes)), weights=probs, k=1)[0]
        elegidas.append(restantes.pop(idx))
    return elegidas


def _indice_pool(
    preguntas: list,
) -> dict[str, dict[tuple[str, str], list]]:
    pool: dict[str, dict[tuple[str, str], list]] = defaultdict(lambda: defaultdict(list))
    for p in preguntas:
        pool[p.materia][(p.tipo, p.dificultad)].append(p)
    return pool


def _elegir_pregunta_slot(
    pool: dict[str, dict[tuple[str, str], list]],
    materia: str,
    tipo: str,
    dificultad: str,
    usadas_ids: set[int],
    rng: random.Random,
    pregunta_key: Callable,
) -> object | None:
    candidatas = pool.get(materia, {}).get((tipo, dificultad), [])
    candidatas = [p for p in candidatas if pregunta_key(p) not in usadas_ids]
    if candidatas:
        return rng.choice(candidatas)
    # Relajar: mismo tipo, otra dificultad
    for (_t, _d), lista in pool.get(materia, {}).items():
        if _t != tipo:
            continue
        alt = [p for p in lista if pregunta_key(p) not in usadas_ids]
        if alt:
            return rng.choice(alt)
    # Cualquier pregunta de la materia
    todas: list = []
    for lista in pool.get(materia, {}).values():
        todas.extend(p for p in lista if pregunta_key(p) not in usadas_ids)
    if todas:
        return rng.choice(todas)
    return None


def _filtrar_materias_candidatas(
    materias_orden: list[str],
    materias_meta: dict[str, dict[str, str]],
    *,
    curso_filtro: str | None,
    semestre_filtro: str | None,
    grupo_filtro: str | None,
) -> list[str]:
    candidatas: list[str] = []
    for materia in materias_orden:
        meta = materias_meta.get(materia, {})
        if curso_filtro and (meta.get("curso") or "") != curso_filtro:
            continue
        if semestre_filtro and (meta.get("semestre") or "") != semestre_filtro:
            continue
        if grupo_filtro and (meta.get("grupo") or "") != str(grupo_filtro):
            continue
        candidatas.append(materia)
    return candidatas


def generar_examen(
    preguntas: list,
    *,
    perfil: PerfilPedagogico,
    materias_orden: list[str],
    materias_meta: dict[str, dict[str, str]],
    stats: dict[str, EstadisticaMateria] | None = None,
    n_materias: int = 5,
    slots: tuple[tuple[str, str], ...] | None = None,
    curso_filtro: str | None = None,
    semestre_filtro: str | None = None,
    grupo_filtro: str | None = None,
    materia_fija: str | None = None,
    usar_todas_materias_ambito: bool = False,
    seleccion_determinista: bool = False,
    orden_por_historico: str | None = None,
    semilla: int | None = None,
    pregunta_key: Callable | None = None,
) -> PlanExamen:
    """
    Construye un examen ordenado: por materia (orden del grado) y slots balanceados.
    """
    if pregunta_key is None:
        pregunta_key = lambda p: (p.materia, p.texto)

    if stats is None:
        stats = cargar_estadisticas_historicas(materias_validas=set(materias_orden))

    rng = random.Random(semilla)

    candidatas = _filtrar_materias_candidatas(
        materias_orden,
        materias_meta,
        curso_filtro=curso_filtro,
        semestre_filtro=semestre_filtro,
        grupo_filtro=grupo_filtro,
    )
    if not candidatas:
        raise ValueError("No hay materias para los filtros indicados.")

    if materia_fija:
        candidatas = [m for m in candidatas if m == materia_fija]
        if not candidatas:
            raise ValueError(f"La materia {materia_fija!r} no está en el ámbito del examen.")

    todas_en_ambito = usar_todas_materias_ambito or perfil == PerfilPedagogico.SIMULACRO
    n_efectivo = len(candidatas) if todas_en_ambito else n_materias

    if perfil == PerfilPedagogico.SIMULACRO:
        slots = (("Teoria", "Media"),)
    elif materia_fija and n_efectivo == 1:
        slots = SLOTS_CANONICOS_12
    elif slots is None:
        total_preg = n_efectivo * 4
        slots = slots_para_tamano(total_preg, n_efectivo)

    pesos = calcular_pesos_materia(candidatas, stats, perfil)
    if todas_en_ambito:
        materias_sel = candidatas
    elif seleccion_determinista:
        materias_sel = candidatas[:n_efectivo]
    else:
        materias_sel = elegir_materias_ponderadas(candidatas, pesos, n_efectivo, rng)
        materias_sel.sort(key=lambda m: materias_orden.index(m) if m in materias_orden else 999)

    if orden_por_historico in ("asc", "desc") and len(materias_sel) > 1:
        reverse = orden_por_historico == "desc"

        def _indice(m: str) -> float:
            st = stats.get(m)
            return st.indice_dificultad if st else 0.5

        materias_sel.sort(key=_indice, reverse=reverse)

    pool_idx = _indice_pool(preguntas)
    seleccion: list = []
    usadas: set = set()

    for materia in materias_sel:
        for tipo, dificultad in slots:
            p = _elegir_pregunta_slot(
                pool_idx, materia, tipo, dificultad, usadas, rng, pregunta_key
            )
            if p is None:
                continue
            usadas.add(pregunta_key(p))
            seleccion.append(p)

    if not seleccion:
        raise ValueError("No se pudo construir el examen con el banco y filtros dados.")

    return PlanExamen(
        perfil=perfil,
        materias=materias_sel,
        slots_por_materia=slots,
        preguntas=seleccion,
    )


def resumen_estadisticas(
    stats: dict[str, EstadisticaMateria],
    materias: list[str],
    top_n: int = 8,
) -> str:
    """Texto breve para CLI: materias más exigentes según histórico."""
    ordenadas = sorted(
        (stats[m] for m in materias if m in stats),
        key=lambda s: s.indice_dificultad,
        reverse=True,
    )
    lineas = ["Materias con mayor índice de dificultad (histórico agregado):"]
    for st in ordenadas[:top_n]:
        lineas.append(
            f"  · {st.materia}: media {st.media}, suspens {st.tasa_suspens:.0%}, "
            f"n={st.n_registros}"
        )
    return "\n".join(lineas)
