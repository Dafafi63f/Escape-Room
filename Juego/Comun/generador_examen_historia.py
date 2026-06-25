#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de generación de exámenes (modo historia).

Usa el histórico de calificaciones (MatCAD) para ponderar materias según el
perfil pedagógico y el banco de preguntas. La dificultad no se fija en la
configuración: emerge del pool al elegir preguntas por tipo (teoría/cálculo).

Importado por modo_historia.py. Para probar sin jugar: Files/cli_examen_historia.py
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from Comun.reglas_partida import validar_total_preguntas
from Comun.rutas import resolver_historico_qualificacions

# --- Perfiles pedagógicos ---

from enum import Enum


class PerfilPedagogico(str, Enum):
    """Perfiles v1 (datos agregados del histórico)."""

    BALANCEADO = "balanceado"
    REFUERZO = "refuerzo"
    DESAFIO = "desafio"
    POR_CURSO = "por_curso"
    SIMULACRO = "simulacro"


def describir_perfil(perfil: PerfilPedagogico) -> str:
    textos = {
        PerfilPedagogico.BALANCEADO: "Preferencia histórica suave al repartir preguntas entre materias.",
        PerfilPedagogico.REFUERZO: "Más preguntas en materias con más suspensos del ámbito.",
        PerfilPedagogico.DESAFIO: "Más preguntas en materias con mejores medias del ámbito.",
        PerfilPedagogico.POR_CURSO: "Cobertura del ámbito curricular; más preguntas en las más exigentes.",
        PerfilPedagogico.SIMULACRO: "Una pregunta por materia del ámbito (repaso global).",
    }
    return textos.get(perfil, perfil.value)


# --- Generador ---

_ORDEN_DIFICULTAD = {"Facil": 0, "Media": 1, "Dificil": 2}
_ORDEN_TIPO = {"Teoria": 0, "Calculo": 1}

TIPOS_PREGUNTA_MIXTO = frozenset({"Teoria", "Calculo"})
PREGUNTAS_POR_MATERIA_DEFECTO = 4


def preguntas_por_materia_defecto(
    *,
    perfil: PerfilPedagogico,
    materia_fija: str | None,
) -> int:
    if perfil == PerfilPedagogico.SIMULACRO:
        return 1
    return PREGUNTAS_POR_MATERIA_DEFECTO


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
    preguntas_por_materia: int
    tipos_permitidos: frozenset[str]
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


def indices_dificultad_ambito(
    candidatas: list[str],
    stats: dict[str, EstadisticaMateria],
) -> dict[str, float]:
    """Índice 0..1 de dificultad relativo al ámbito filtrado (curso/semestre/grupo).

    El histórico global sigue siendo la fuente, pero se reescala dentro de las
    materias candidatas para que refuerzo/desafío y el orden tengan sentido aunque
    el ámbito elegido no coincida con las asignaturas más difíciles del grado entero.
    """
    if not candidatas:
        return {}
    brutos = {
        m: stats[m].indice_dificultad if m in stats else 0.5 for m in candidatas
    }
    if len(candidatas) == 1:
        return dict(brutos)
    lo = min(brutos.values())
    hi = max(brutos.values())
    if hi <= lo:
        return {m: 0.5 for m in candidatas}
    escala = hi - lo
    return {m: (brutos[m] - lo) / escala for m in candidatas}


def calcular_pesos_materia(
    materias: list[str],
    stats: dict[str, EstadisticaMateria],
    perfil: PerfilPedagogico,
    *,
    usar_analisis_historico: bool = True,
    indices_ambito: dict[str, float] | None = None,
) -> dict[str, float]:
    """Pesos de selección: mayor valor ⇒ más probable, pero siempre > 0 (ninguna materia excluida)."""
    pesos: dict[str, float] = {}
    for m in materias:
        if indices_ambito is not None and m in indices_ambito:
            indice = indices_ambito[m]
        else:
            st = stats.get(m)
            indice = st.indice_dificultad if st else 0.5
        if not usar_analisis_historico:
            w = 1.0
        elif perfil == PerfilPedagogico.BALANCEADO:
            # Preferencia suave: el histórico inclina sin bloquear otras materias.
            w = 0.75 + 0.50 * indice
        elif perfil == PerfilPedagogico.REFUERZO:
            w = 0.35 + indice
        elif perfil == PerfilPedagogico.DESAFIO:
            w = 0.35 + (1.0 - indice)
        elif perfil in (PerfilPedagogico.POR_CURSO, PerfilPedagogico.SIMULACRO):
            w = 0.35 + indice if perfil == PerfilPedagogico.POR_CURSO else 1.0
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


def _elegir_pregunta(
    pool: dict[str, dict[tuple[str, str], list]],
    materia: str,
    tipos_permitidos: frozenset[str],
    usadas_ids: set,
    rng: random.Random,
    pregunta_key: Callable,
) -> object | None:
    candidatas: list = []
    for (tipo, _dificultad), lista in pool.get(materia, {}).items():
        if tipo not in tipos_permitidos:
            continue
        candidatas.extend(p for p in lista if pregunta_key(p) not in usadas_ids)
    if candidatas:
        return rng.choice(candidatas)
    return None


def _clave_orden_dificultad_pregunta(pregunta: object) -> tuple[int, int, str]:
    dificultad = getattr(pregunta, "dificultad", "")
    tipo = getattr(pregunta, "tipo", "")
    materia = getattr(pregunta, "materia", "")
    return (
        _ORDEN_DIFICULTAD.get(dificultad, 99),
        _ORDEN_TIPO.get(tipo, 99),
        materia,
    )


def _ordenar_preguntas_por_dificultad(preguntas: list) -> list:
    """Orden estable: Fácil → Media → Difícil; Teoría antes que Cálculo."""
    return sorted(preguntas, key=_clave_orden_dificultad_pregunta)


def _clave_orden_plantilla(pregunta: object) -> tuple[int, int, str]:
    tipo = getattr(pregunta, "tipo", "")
    dificultad = getattr(pregunta, "dificultad", "")
    materia = getattr(pregunta, "materia", "")
    return (
        _ORDEN_TIPO.get(tipo, 99),
        _ORDEN_DIFICULTAD.get(dificultad, 99),
        materia,
    )


def _ordenar_preguntas_por_plantilla(preguntas: list) -> list:
    """Orden canónico del banco: teoría antes que cálculo; F → M → D dentro de cada tipo."""
    return sorted(preguntas, key=_clave_orden_plantilla)


def _ordenar_preguntas_por_materia(
    preguntas: list,
    orden_materias: list[str],
) -> list:
    """Agrupa por asignatura en el orden del plan (un examen tras otro)."""
    if len(preguntas) <= 1:
        return preguntas
    grupos: dict[str, list] = {}
    for p in preguntas:
        grupos.setdefault(p.materia, []).append(p)
    out: list = []
    vistos: set[str] = set()
    for m in orden_materias:
        if m in grupos:
            out.extend(grupos[m])
            vistos.add(m)
    for m, bloque in grupos.items():
        if m not in vistos:
            out.extend(bloque)
    return out


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


def _materias_unicas_en_orden(seleccion: list) -> list[str]:
    vistas: list[str] = []
    for p in seleccion:
        m = getattr(p, "materia", "")
        if m and m not in vistas:
            vistas.append(m)
    return vistas


def _construir_seleccion_equitativa(
    pool_materias: list[str],
    preguntas_por_materia: int,
    tipos_permitidos: frozenset[str],
    pool_idx: dict[str, dict[tuple[str, str], list]],
    usadas: set,
    rng: random.Random,
    pregunta_key: Callable,
    *,
    exigir_balance_completo: bool,
) -> list:
    seleccion: list = []
    for materia in pool_materias:
        for _ in range(preguntas_por_materia):
            p = _elegir_pregunta(
                pool_idx,
                materia,
                tipos_permitidos,
                usadas,
                rng,
                pregunta_key,
            )
            if p is None:
                if exigir_balance_completo:
                    tipos_txt = "/".join(sorted(tipos_permitidos))
                    raise ValueError(
                        f"No hay pregunta disponible para {materia!r} "
                        f"(tipos {tipos_txt}); no se puede completar el examen."
                    )
                continue
            usadas.add(pregunta_key(p))
            seleccion.append(p)
    return seleccion


def _construir_seleccion_ponderada(
    pool_materias: list[str],
    preguntas_por_materia: int,
    tipos_permitidos: frozenset[str],
    pesos: dict[str, float],
    pool_idx: dict[str, dict[tuple[str, str], list]],
    usadas: set,
    rng: random.Random,
    pregunta_key: Callable,
) -> list:
    """Reparte preguntas eligiendo materia por peso histórico en cada elección."""
    if not pool_materias or preguntas_por_materia <= 0:
        return []

    n_preguntas = len(pool_materias) * preguntas_por_materia
    seleccion: list = []

    if n_preguntas >= len(pool_materias):
        for materia in pool_materias:
            p = _elegir_pregunta(
                pool_idx,
                materia,
                tipos_permitidos,
                usadas,
                rng,
                pregunta_key,
            )
            if p is not None:
                usadas.add(pregunta_key(p))
                seleccion.append(p)

    ws = [pesos.get(m, 1.0) for m in pool_materias]
    intentos_fallidos = 0
    max_intentos = max(n_preguntas * len(pool_materias) * 4, 32)
    while len(seleccion) < n_preguntas:
        if intentos_fallidos > max_intentos:
            break
        materia = rng.choices(pool_materias, weights=ws, k=1)[0]
        p = _elegir_pregunta(
            pool_idx,
            materia,
            tipos_permitidos,
            usadas,
            rng,
            pregunta_key,
        )
        if p is None:
            intentos_fallidos += 1
            continue
        intentos_fallidos = 0
        usadas.add(pregunta_key(p))
        seleccion.append(p)

    return seleccion


def _construir_seleccion_plantillas_materia(
    materia: str,
    plantillas: list[dict],
    preguntas: list,
    tipos_permitidos: frozenset[str],
    usadas: set,
    rng: random.Random,
    pregunta_key: Callable,
    n_preguntas: int | None = None,
) -> list:
    """Una pregunta aleatoria por plantilla del banco (contenido distinto en cada partida)."""
    from Comun.rutas import registrar_scripts_en_path

    registrar_scripts_en_path()
    from utils_plantillas_core import clave_contenido, expandir_plantilla_instancias

    pool_materia = [p for p in preguntas if getattr(p, "materia", "") == materia]
    por_clave: dict[tuple, object] = {}
    for p in pool_materia:
        k = clave_contenido(p.materia, p.texto, p.opciones, p.correcta)
        por_clave[k] = p

    pool_idx = _indice_pool(preguntas)
    seleccion: list = []

    elegibles: list[dict] = []
    for plantilla in plantillas:
        tipo = (plantilla.get("tipo") or "Teoria").strip()
        if tipo not in tipos_permitidos:
            continue
        elegibles.append(plantilla)

    if n_preguntas is not None and n_preguntas < len(elegibles):
        orden = list(elegibles)
        rng.shuffle(orden)
        elegibles = orden[:n_preguntas]

    for plantilla in elegibles:
        candidatas: list = []
        for inst in expandir_plantilla_instancias(materia, plantilla):
            if inst["tipo"] not in tipos_permitidos:
                continue
            k = clave_contenido(
                inst["materia"],
                inst["pregunta"],
                inst["opciones"],
                inst["correcta"],
            )
            p = por_clave.get(k)
            if p is not None and pregunta_key(p) not in usadas:
                candidatas.append(p)
        if candidatas:
            p = rng.choice(candidatas)
        else:
            p = _elegir_pregunta(
                pool_idx,
                materia,
                tipos_permitidos,
                usadas,
                rng,
                pregunta_key,
            )
            if p is None:
                continue
        usadas.add(pregunta_key(p))
        seleccion.append(p)

    return seleccion


def generar_examen(
    preguntas: list,
    *,
    perfil: PerfilPedagogico,
    materias_orden: list[str],
    materias_meta: dict[str, dict[str, str]],
    stats: dict[str, EstadisticaMateria] | None = None,
    n_materias: int = 5,
    preguntas_por_materia: int | None = None,
    tipos_permitidos: frozenset[str] | None = None,
    curso_filtro: str | None = None,
    semestre_filtro: str | None = None,
    grupo_filtro: str | None = None,
    materia_fija: str | None = None,
    usar_todas_materias_ambito: bool = False,
    seleccion_determinista: bool = False,
    orden_preguntas: str = "aleatorio",
    exigir_balance_completo: bool = False,
    usar_analisis_historico: bool = True,
    usar_plantillas_materia: bool = False,
    plantillas_materia: list[dict] | None = None,
    n_preguntas: int | None = None,
    semilla: int | None = None,
    semilla_orden: int | None = None,
    pregunta_key: Callable | None = None,
) -> PlanExamen:
    """
    Construye un examen eligiendo N preguntas por materia del pool disponible.

    La dificultad no se impone: sale del banco al sortear. Con histórico activo,
    el reparto entre materias sigue los pesos del perfil (salvo
    ``exigir_balance_completo``). Con semilla fija, la selección es reproducible.
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

    if tipos_permitidos is None:
        tipos_permitidos = TIPOS_PREGUNTA_MIXTO

    if usar_plantillas_materia and materia_fija:
        if not plantillas_materia:
            raise ValueError(
                f"No hay plantillas definidas para la asignatura {materia_fija!r}."
            )
        usadas: set = set()
        seleccion = _construir_seleccion_plantillas_materia(
            materia_fija,
            plantillas_materia,
            preguntas,
            tipos_permitidos,
            usadas,
            rng,
            pregunta_key,
            n_preguntas=n_preguntas,
        )
        if not seleccion:
            raise ValueError(
                f"No se pudo construir el examen de {materia_fija!r} "
                f"con las plantillas y el banco disponibles."
            )
        if orden_preguntas == "plantilla":
            seleccion = _ordenar_preguntas_por_plantilla(seleccion)
        elif orden_preguntas == "dificultad":
            seleccion = _ordenar_preguntas_por_dificultad(seleccion)
        elif orden_preguntas in ("aleatorio", "variar"):
            if orden_preguntas == "variar" and semilla_orden is not None:
                random.Random(semilla_orden).shuffle(seleccion)
            else:
                rng.shuffle(seleccion)
        elif orden_preguntas != "materia":
            raise ValueError(f"orden_preguntas desconocido: {orden_preguntas!r}")
        validar_total_preguntas(len(seleccion))
        return PlanExamen(
            perfil=perfil,
            materias=[materia_fija],
            preguntas_por_materia=len(seleccion),
            tipos_permitidos=tipos_permitidos,
            preguntas=seleccion,
        )

    todas_en_ambito = usar_todas_materias_ambito or perfil == PerfilPedagogico.SIMULACRO
    n_efectivo = len(candidatas) if todas_en_ambito else n_materias

    if tipos_permitidos is None:
        tipos_permitidos = TIPOS_PREGUNTA_MIXTO
    if preguntas_por_materia is None:
        preguntas_por_materia = preguntas_por_materia_defecto(
            perfil=perfil,
            materia_fija=materia_fija,
        )
    if preguntas_por_materia <= 0:
        raise ValueError("preguntas_por_materia debe ser positivo.")

    indices_ambito: dict[str, float] = {}
    if usar_analisis_historico:
        indices_ambito = indices_dificultad_ambito(candidatas, stats)

    pesos = calcular_pesos_materia(
        candidatas,
        stats,
        perfil,
        usar_analisis_historico=usar_analisis_historico,
        indices_ambito=indices_ambito or None,
    )
    if todas_en_ambito:
        pool_materias = list(candidatas)
    elif seleccion_determinista:
        pool_materias = candidatas[:n_efectivo]
    else:
        pool_materias = elegir_materias_ponderadas(candidatas, pesos, n_efectivo, rng)
        pool_materias.sort(
            key=lambda m: materias_orden.index(m) if m in materias_orden else 999
        )

    if not pool_materias:
        raise ValueError("No hay materias en el pool del examen.")

    n_preguntas = len(pool_materias) * preguntas_por_materia
    reparto_equitativo = exigir_balance_completo or not usar_analisis_historico

    pool_idx = _indice_pool(preguntas)
    usadas: set = set()

    if reparto_equitativo:
        seleccion = _construir_seleccion_equitativa(
            pool_materias,
            preguntas_por_materia,
            tipos_permitidos,
            pool_idx,
            usadas,
            rng,
            pregunta_key,
            exigir_balance_completo=exigir_balance_completo,
        )
    else:
        seleccion = _construir_seleccion_ponderada(
            pool_materias,
            preguntas_por_materia,
            tipos_permitidos,
            pesos,
            pool_idx,
            usadas,
            rng,
            pregunta_key,
        )

    if exigir_balance_completo and pool_materias:
        esperadas = len(pool_materias) * preguntas_por_materia
        if len(seleccion) != esperadas:
            raise ValueError(
                f"Examen incompleto: {len(seleccion)}/{esperadas} preguntas "
                f"({len(pool_materias)} materias × {preguntas_por_materia} preg/materia)."
            )

    if len(seleccion) <= 1:
        pass
    elif orden_preguntas == "plantilla":
        seleccion = _ordenar_preguntas_por_plantilla(seleccion)
    elif orden_preguntas == "materia":
        seleccion = _ordenar_preguntas_por_materia(seleccion, pool_materias)
    elif orden_preguntas == "variar" and semilla_orden is not None:
        random.Random(semilla_orden).shuffle(seleccion)
    elif orden_preguntas == "variar":
        rng.shuffle(seleccion)
    elif orden_preguntas == "dificultad":
        seleccion = _ordenar_preguntas_por_dificultad(seleccion)
    elif orden_preguntas == "aleatorio":
        rng.shuffle(seleccion)
    else:
        raise ValueError(f"orden_preguntas desconocido: {orden_preguntas!r}")

    if not seleccion:
        raise ValueError("No se pudo construir el examen con el banco y filtros dados.")

    validar_total_preguntas(len(seleccion))
    materias_plan = _materias_unicas_en_orden(seleccion)

    return PlanExamen(
        perfil=perfil,
        materias=materias_plan,
        preguntas_por_materia=preguntas_por_materia,
        tipos_permitidos=tipos_permitidos,
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
