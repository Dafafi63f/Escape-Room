#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de generación de exámenes (modo historia).

Pondera materias según la práctica local del jugador (estadísticas pasadas)
y el perfil pedagógico, sobre el banco de preguntas. La dificultad no se fija
en la configuración: emerge del pool al elegir preguntas por tipo (teoría/cálculo).

Importado por modo_historia.py. Para probar sin jugar: Files/cli_examen_historia.py
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from Comun.reglas import validar_total_preguntas
from Comun.semillas import RngPartida

from enum import Enum


class PerfilPedagogico(str, Enum):
    """Perfiles v1 (ponderación por práctica / índice de dificultad local)."""

    BALANCEADO = "balanceado"
    REFUERZO = "refuerzo"
    DESAFIO = "desafio"
    POR_CURSO = "por_curso"
    SIMULACRO = "simulacro"


def describir_perfil(perfil: PerfilPedagogico) -> str:
    textos = {
        PerfilPedagogico.BALANCEADO: (
            "Preferencia suave al repartir preguntas según el índice de dificultad "
            "de tu práctica."
        ),
        PerfilPedagogico.REFUERZO: (
            "Más preguntas en materias o conceptos con peor acierto en tu práctica."
        ),
        PerfilPedagogico.DESAFIO: (
            "Más preguntas en materias o conceptos con mejor acierto en tu práctica."
        ),
        PerfilPedagogico.POR_CURSO: (
            "Cobertura del ámbito curricular; más preguntas en las más exigentes "
            "según tu práctica."
        ),
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
) -> int:
    if perfil == PerfilPedagogico.SIMULACRO:
        return 1
    return PREGUNTAS_POR_MATERIA_DEFECTO


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
    semilla_partida: int = 0
    semilla_contenido: int = 0
    rng: RngPartida | None = None


def indices_dificultad_ambito(
    candidatas: list[str],
    stats: dict[str, EstadisticaMateria],
) -> dict[str, float]:
    """Índice 0..1 de dificultad relativo al ámbito filtrado (curso/semestre/grupo).

    Las estadísticas (práctica local) se reescalan dentro de las materias candidatas
    para que refuerzo/desafío y el orden tengan sentido en el ámbito elegido.
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
            # Preferencia suave: la práctica inclina sin bloquear otras materias.
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
    *,
    perfiles_fallo: dict[str, tuple[tuple[str, str], ...]] | None = None,
    prob_perfil_fallo: float = 0.72,
) -> object | None:
    candidatas: list = []
    for (tipo, _dificultad), lista in pool.get(materia, {}).items():
        if tipo not in tipos_permitidos:
            continue
        candidatas.extend(p for p in lista if pregunta_key(p) not in usadas_ids)
    if not candidatas:
        return None
    if perfiles_fallo:
        perfiles = perfiles_fallo.get(materia)
        if perfiles:
            similares = [
                p
                for p in candidatas
                if (
                    (getattr(p, "tipo", "") or "").strip(),
                    (getattr(p, "dificultad", "") or "").strip(),
                )
                in perfiles
            ]
            otros = [p for p in candidatas if p not in similares]
            if otros and similares:
                from Comun.cadena_examen_dirigido import PROB_EXPLORACION_PERFIL_PREGUNTA

                if rng.random() < PROB_EXPLORACION_PERFIL_PREGUNTA:
                    return rng.choice(otros)
            if similares and rng.random() < prob_perfil_fallo:
                return rng.choice(similares)
    return rng.choice(candidatas)


def _clave_orden_dificultad_pregunta(pregunta: object) -> tuple[int, int, str]:
    dificultad = getattr(pregunta, "dificultad", "")
    tipo = getattr(pregunta, "tipo", "")
    materia = getattr(pregunta, "materia", "")
    return (
        _ORDEN_DIFICULTAD.get(dificultad, 99),
        _ORDEN_TIPO.get(tipo, 99),
        materia,
    )


def ordenar_preguntas_por_dificultad(preguntas: list) -> list:
    """Orden estable: Fácil → Media → Difícil; Teoría antes que Cálculo."""
    return sorted(preguntas, key=_clave_orden_dificultad_pregunta)


_ordenar_preguntas_por_dificultad = ordenar_preguntas_por_dificultad


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


def _cupo_preguntas_materia(
    pool_idx: dict[str, dict[tuple[str, str], list]],
    materia: str,
    tipos_permitidos: frozenset[str],
    usadas: set,
    pregunta_key: Callable,
) -> int:
    """Preguntas aún no usadas de una materia (respetando tipos permitidos)."""
    total = 0
    for (tipo, _), lista in pool_idx.get(materia, {}).items():
        if tipo not in tipos_permitidos:
            continue
        total += sum(1 for p in lista if pregunta_key(p) not in usadas)
    return total


def _materias_con_cupo_disponible(
    candidatas: list[str],
    pool_idx: dict[str, dict[tuple[str, str], list]],
    tipos_permitidos: frozenset[str],
    usadas: set,
    pregunta_key: Callable,
    *,
    min_cupo: int,
) -> list[str]:
    return [
        m
        for m in candidatas
        if _cupo_preguntas_materia(
            pool_idx, m, tipos_permitidos, usadas, pregunta_key
        )
        >= min_cupo
    ]


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
    perfiles_fallo: dict[str, tuple[tuple[str, str], ...]] | None = None,
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
                perfiles_fallo=perfiles_fallo,
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
    *,
    perfiles_fallo: dict[str, tuple[tuple[str, str], ...]] | None = None,
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
                perfiles_fallo=perfiles_fallo,
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
            perfiles_fallo=perfiles_fallo,
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
    from Comun.utils_plantillas_core import clave_contenido, expandir_plantilla_instancias

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


def _construir_seleccion_plana(
    preguntas: list,
    n: int,
    rng: random.Random,
    pregunta_key: Callable,
) -> list:
    """Muestra aleatoria sin balance por materia, tipo ni dificultad (CSV mínimo)."""
    if n <= 0:
        raise ValueError("n_preguntas debe ser positivo.")
    unicas: dict[object, object] = {}
    for p in preguntas:
        clave = pregunta_key(p)
        if clave not in unicas:
            unicas[clave] = p
    pool = list(unicas.values())
    if len(pool) < n:
        raise ValueError(
            f"No hay suficientes preguntas en el banco ({len(pool)}/{n})."
        )
    return rng.sample(pool, n)


def peso_pregunta_para_seleccion(
    pregunta: object,
    stats: dict[str, EstadisticaMateria],
    perfil: PerfilPedagogico,
) -> float:
    return _pesos_preguntas_desde_stats(
        [pregunta], stats, perfil, usar_ponderacion=True
    )[0]


def _pesos_preguntas_desde_stats(
    pool: list,
    stats: dict[str, EstadisticaMateria],
    perfil: PerfilPedagogico,
    *,
    usar_ponderacion: bool,
) -> list[float]:
    if not stats or not usar_ponderacion:
        return [1.0] * len(pool)
    from Comun.cadena_examen_dirigido import tokens_enunciado

    pesos_clave = calcular_pesos_materia(
        list(stats.keys()),
        stats,
        perfil,
        usar_analisis_historico=True,
    )
    pesos: list[float] = []
    for pregunta in pool:
        tokens = tokens_enunciado(pregunta)
        candidatos = set(tokens)
        materia = (getattr(pregunta, "materia", "") or "").strip()
        if materia:
            candidatos.add(materia)
        ws = [pesos_clave[k] for k in candidatos if k in pesos_clave]
        pesos.append(max(ws) if ws else 0.15)
    return pesos


def _construir_seleccion_plana_ponderada(
    preguntas: list,
    n: int,
    rng: random.Random,
    pregunta_key: Callable,
    stats: dict[str, EstadisticaMateria],
    perfil: PerfilPedagogico,
    *,
    usar_ponderacion: bool,
) -> list:
    if n <= 0:
        raise ValueError("n_preguntas debe ser positivo.")
    unicas: dict[object, object] = {}
    for p in preguntas:
        clave = pregunta_key(p)
        if clave not in unicas:
            unicas[clave] = p
    pool = list(unicas.values())
    if len(pool) < n:
        raise ValueError(
            f"No hay suficientes preguntas en el banco ({len(pool)}/{n})."
        )
    if not stats or not usar_ponderacion:
        return rng.sample(pool, n)
    from Comun.cadena_examen_dirigido import _muestra_ponderada_sin_reemplazo

    pesos = _pesos_preguntas_desde_stats(
        pool, stats, perfil, usar_ponderacion=usar_ponderacion
    )
    return _muestra_ponderada_sin_reemplazo(pool, pesos, n, rng)


def resolver_stats_para_generador(
    *,
    preset,
    cfg,
    perfil,
    materias_meta: dict | None = None,
) -> dict[str, EstadisticaMateria]:
    """Carga estadísticas locales si la configuración pide ponderar por práctica."""
    from Comun.config_historia import usar_analisis_local_desde_config
    from Comun.estadisticas_jugador import cargar_estadisticas_locales

    if not usar_analisis_local_desde_config(preset, cfg, perfil=perfil):
        return {}
    if perfil is None:
        return {}
    return cargar_estadisticas_locales(perfil, materias_meta)


def _ordenar_seleccion_examen(
    seleccion: list,
    orden_preguntas: str,
    rng_partida: RngPartida,
    *,
    pool_materias: list[str] | None = None,
) -> list:
    if len(seleccion) <= 1:
        return seleccion
    if orden_preguntas == "plantilla":
        return _ordenar_preguntas_por_plantilla(seleccion)
    if orden_preguntas == "materia":
        return _ordenar_preguntas_por_materia(seleccion, pool_materias or [])
    if orden_preguntas == "variar":
        rng_partida.shuffle(seleccion)
        return seleccion
    if orden_preguntas == "dificultad":
        return _ordenar_preguntas_por_dificultad(seleccion)
    if orden_preguntas == "aleatorio":
        rng_partida.shuffle(seleccion)
        return seleccion
    raise ValueError(f"orden_preguntas desconocido: {orden_preguntas!r}")


def calcular_pesos_desde_registros(registros: list) -> dict[str, float]:
    """Pesos de selección por materia según fallos de una sesión (más fallos ⇒ más peso)."""
    fallos: dict[str, int] = defaultdict(int)
    intentos: dict[str, int] = defaultdict(int)
    for registro in registros:
        materia = (getattr(registro.pregunta, "materia", "") or "").strip()
        if not materia:
            continue
        intentos[materia] += 1
        if not registro.acierto:
            fallos[materia] += 1
    pesos: dict[str, float] = {}
    for materia, total in intentos.items():
        n_fallos = fallos.get(materia, 0)
        tasa_fallo = n_fallos / total
        pesos[materia] = max(0.05, 0.20 + tasa_fallo + 0.80 * n_fallos)
    return pesos


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
    seleccion_plana: bool = False,
    semilla: int | None = None,
    semilla_contenido: int | None = None,
    pregunta_key: Callable | None = None,
    pesos_materia_sesion: dict[str, float] | None = None,
    preguntas_excluir: list | None = None,
    perfiles_fallo: dict[str, tuple[tuple[str, str], ...]] | None = None,
    registros_dirigido: list | None = None,
) -> PlanExamen:
    """
    Construye un examen eligiendo N preguntas por materia del pool disponible.

    La dificultad no se impone: sale del banco al sortear. Con ponderación activa
    (práctica local), el reparto entre materias sigue los pesos del perfil (salvo
    ``exigir_balance_completo``). Con semilla fija, la selección es reproducible.
    """
    if pregunta_key is None:
        pregunta_key = lambda p: (p.materia, p.texto)

    if stats is None:
        stats = {}

    from Comun.semillas import RngPartida, semilla_partida_aleatoria

    semilla_partida = semilla if semilla is not None else semilla_partida_aleatoria()
    semilla_seleccion = (
        semilla_contenido if semilla_contenido is not None else semilla_partida
    )
    rng_partida = RngPartida.desde_semilla(semilla_partida)
    rng_seleccion = (
        rng_partida
        if semilla_seleccion == semilla_partida
        else RngPartida.desde_semilla(semilla_seleccion)
    )

    if seleccion_plana:
        if n_preguntas is None:
            raise ValueError("seleccion_plana requiere n_preguntas.")
        if registros_dirigido is not None:
            from Comun.cadena_examen_dirigido import construir_seleccion_plana_dirigida

            seleccion = construir_seleccion_plana_dirigida(
                preguntas,
                n_preguntas,
                rng_seleccion,
                pregunta_key,
                registros_dirigido,
                preguntas_excluir,
            )
        else:
            seleccion = _construir_seleccion_plana_ponderada(
                preguntas,
                n_preguntas,
                rng_seleccion,
                pregunta_key,
                stats,
                perfil,
                usar_ponderacion=usar_analisis_historico,
            )
        seleccion = _ordenar_seleccion_examen(
            seleccion,
            orden_preguntas,
            rng_partida,
        )
        validar_total_preguntas(len(seleccion))
        tipos = tipos_permitidos if tipos_permitidos is not None else TIPOS_PREGUNTA_MIXTO
        return PlanExamen(
            perfil=perfil,
            materias=[],
            preguntas_por_materia=n_preguntas,
            tipos_permitidos=tipos,
            preguntas=seleccion,
            semilla_partida=semilla_partida,
            semilla_contenido=semilla_seleccion,
            rng=rng_partida,
        )

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
            rng_seleccion,
            pregunta_key,
            n_preguntas=n_preguntas,
        )
        if not seleccion:
            raise ValueError(
                f"No se pudo construir el examen de {materia_fija!r} "
                f"con las plantillas y el banco disponibles."
            )
        if (
            n_preguntas is not None
            and len(seleccion) > n_preguntas
            and usar_analisis_historico
            and stats
        ):
            seleccion = _construir_seleccion_plana_ponderada(
                seleccion,
                n_preguntas,
                rng_seleccion,
                pregunta_key,
                stats,
                perfil,
                usar_ponderacion=True,
            )
        elif n_preguntas is not None and len(seleccion) > n_preguntas:
            seleccion = rng_seleccion.sample(seleccion, n_preguntas)
        if orden_preguntas == "plantilla":
            seleccion = _ordenar_preguntas_por_plantilla(seleccion)
        elif orden_preguntas == "dificultad":
            seleccion = _ordenar_preguntas_por_dificultad(seleccion)
        elif orden_preguntas in ("aleatorio", "variar"):
            rng_partida.shuffle(seleccion)
        elif orden_preguntas != "materia":
            raise ValueError(f"orden_preguntas desconocido: {orden_preguntas!r}")
        validar_total_preguntas(len(seleccion))
        return PlanExamen(
            perfil=perfil,
            materias=[materia_fija],
            preguntas_por_materia=len(seleccion),
            tipos_permitidos=tipos_permitidos,
            preguntas=seleccion,
            semilla_partida=semilla_partida,
            semilla_contenido=semilla_seleccion,
            rng=rng_partida,
        )

    todas_en_ambito = usar_todas_materias_ambito or perfil == PerfilPedagogico.SIMULACRO
    n_efectivo = len(candidatas) if todas_en_ambito else n_materias

    if tipos_permitidos is None:
        tipos_permitidos = TIPOS_PREGUNTA_MIXTO
    if preguntas_por_materia is None:
        preguntas_por_materia = preguntas_por_materia_defecto(
            perfil=perfil,
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
    pesos_seleccion_materias = pesos
    if pesos_materia_sesion is not None and registros_dirigido is not None:
        raise ValueError("Use registros_dirigido o pesos_materia_sesion, no ambos.")
    if registros_dirigido is not None:
        from Comun.cadena_examen_dirigido import calcular_pesos_materia_dirigido

        pesos_materia_sesion = calcular_pesos_materia_dirigido(registros_dirigido, candidatas)
    if pesos_materia_sesion is not None:
        pesos_seleccion_materias = {
            m: max(0.05, pesos_materia_sesion.get(m, 0.15)) for m in candidatas
        }

    candidatas_pool = candidatas
    if registros_dirigido is not None or pesos_materia_sesion is not None:
        usadas_exclusion: set = set()
        if preguntas_excluir:
            for pregunta in preguntas_excluir:
                usadas_exclusion.add(pregunta_key(pregunta))
        pool_idx_previo = _indice_pool(preguntas)
        min_cupo_materia = preguntas_por_materia if exigir_balance_completo else 1
        candidatas_pool = _materias_con_cupo_disponible(
            candidatas,
            pool_idx_previo,
            tipos_permitidos,
            usadas_exclusion,
            pregunta_key,
            min_cupo=min_cupo_materia,
        )
        if len(candidatas_pool) < n_efectivo:
            candidatas_pool = _materias_con_cupo_disponible(
                candidatas,
                pool_idx_previo,
                tipos_permitidos,
                usadas_exclusion,
                pregunta_key,
                min_cupo=1,
            )
        if len(candidatas_pool) < n_efectivo:
            raise ValueError(
                "No quedan suficientes asignaturas con preguntas nuevas en la ventana "
                f"reciente de exámenes dirigidos ({len(usadas_exclusion)} preguntas bloqueadas). "
                "Prueba «Repetir partida» o vuelve al menú."
            )
        pesos_seleccion_materias = {
            m: pesos_seleccion_materias.get(m, 0.15) for m in candidatas_pool
        }

    if todas_en_ambito:
        pool_materias = list(candidatas_pool)
    elif seleccion_determinista:
        pool_materias = candidatas_pool[:n_efectivo]
    elif registros_dirigido is not None:
        from Comun.cadena_examen_dirigido import elegir_materias_para_examen_dirigido

        pool_materias = elegir_materias_para_examen_dirigido(
            candidatas_pool,
            pesos_seleccion_materias,
            n_efectivo,
            registros_dirigido,
            rng_seleccion,
        )
        pool_materias.sort(
            key=lambda m: materias_orden.index(m) if m in materias_orden else 999
        )
    else:
        pool_materias = elegir_materias_ponderadas(
            candidatas_pool, pesos_seleccion_materias, n_efectivo, rng_seleccion
        )
        pool_materias.sort(
            key=lambda m: materias_orden.index(m) if m in materias_orden else 999
        )

    if not pool_materias:
        raise ValueError("No hay materias en el pool del examen.")

    reparto_equitativo = exigir_balance_completo or not usar_analisis_historico

    pool_idx = _indice_pool(preguntas)
    usadas_examen: set = set()
    if preguntas_excluir:
        for pregunta in preguntas_excluir:
            usadas_examen.add(pregunta_key(pregunta))

    if pesos_materia_sesion is not None and not exigir_balance_completo:
        pesos = {
            m: max(0.05, pesos_materia_sesion.get(m, 0.15)) for m in pool_materias
        }
        reparto_equitativo = False

    if reparto_equitativo:
        seleccion = _construir_seleccion_equitativa(
            pool_materias,
            preguntas_por_materia,
            tipos_permitidos,
            pool_idx,
            usadas_examen,
            rng_seleccion,
            pregunta_key,
            exigir_balance_completo=exigir_balance_completo,
            perfiles_fallo=perfiles_fallo,
        )
    else:
        seleccion = _construir_seleccion_ponderada(
            pool_materias,
            preguntas_por_materia,
            tipos_permitidos,
            pesos,
            pool_idx,
            usadas_examen,
            rng_seleccion,
            pregunta_key,
            perfiles_fallo=perfiles_fallo,
        )

    if exigir_balance_completo and pool_materias:
        esperadas = len(pool_materias) * preguntas_por_materia
        if len(seleccion) != esperadas:
            raise ValueError(
                f"Examen incompleto: {len(seleccion)}/{esperadas} preguntas "
                f"({len(pool_materias)} materias × {preguntas_por_materia} preg/materia)."
            )

    seleccion = _ordenar_seleccion_examen(
        seleccion,
        orden_preguntas,
        rng_partida,
        pool_materias=pool_materias,
    )

    if not seleccion:
        if pesos_materia_sesion is not None and preguntas_excluir:
            raise ValueError(
                "No se pudo completar el examen dirigido: las asignaturas elegidas "
                "no tienen bastantes preguntas nuevas tras excluir las ya hechas en la cadena. "
                "Prueba «Repetir partida» o reduce la cadena volviendo al menú."
            )
        raise ValueError("No se pudo construir el examen con el banco y filtros dados.")

    validar_total_preguntas(len(seleccion))
    materias_plan = _materias_unicas_en_orden(seleccion)

    return PlanExamen(
        perfil=perfil,
        materias=materias_plan,
        preguntas_por_materia=preguntas_por_materia,
        tipos_permitidos=tipos_permitidos,
        preguntas=seleccion,
        semilla_partida=semilla_partida,
        semilla_contenido=semilla_seleccion,
        rng=rng_partida,
    )


def resumen_estadisticas(
    stats: dict[str, EstadisticaMateria],
    materias: list[str],
    top_n: int = 8,
) -> str:
    """Texto breve para CLI: materias más exigentes según el índice de dificultad."""
    ordenadas = sorted(
        (stats[m] for m in materias if m in stats),
        key=lambda s: s.indice_dificultad,
        reverse=True,
    )
    lineas = ["Materias con mayor índice de dificultad (práctica / stats):"]
    for st in ordenadas[:top_n]:
        lineas.append(
            f"  · {st.materia}: media {st.media}, suspens {st.tasa_suspens:.0%}, "
            f"n={st.n_registros}"
        )
    return "\n".join(lineas)
