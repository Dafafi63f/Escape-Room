#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulación del sistema de pity (escape room y modelo simplificado).

Contrasta probabilidad base constante frente a pity suave + hard pity,
reproduciendo la lógica de ``eventos_partida.py`` y partidas simuladas
con ``generar_puertas_sala``.

  python Files/simulacion_pity.py
  python Files/simulacion_pity.py --iteraciones 20000 --salas 30
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_JUEGO = _SCRIPTS.parent / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.datos import cargar_materias, cargar_preguntas  # noqa: E402
from Comun.semillas import RngPartida, semilla_estable_texto  # noqa: E402
from Comun.escape_partida import construir_pool_escape, materias_del_pool  # noqa: E402
from Comun.escape_room import (  # noqa: E402
    SALAS_DEFECTO,
    config_escape_room,
    generar_puertas_sala,
)
from Comun.eventos_partida import (  # noqa: E402
    PityPuertasEspecialesEscape,
    RASGOS_BOTIN_ESCAPE,
    SALAS_HARD_PITY_BOTIN_ESCAPE,
    SALAS_HARD_PITY_DESCANSO_ESCAPE,
    SALAS_HARD_PITY_TIENDA_ESCAPE,
    _PROB_BASE_DESCANSO_PUERTA,
    _PROB_BASE_TIENDA_PUERTA,
    _PROB_PUERTA_ESPECIAL_MAX,
    _PITY_INCREMENT_DESCANSO_POR_SALA,
    _PITY_INCREMENT_TIENDA_POR_SALA,
    prob_puerta_especial_con_pity,
)
from Comun.rutas import resolver_dataset, resolver_listado_materias  # noqa: E402

PARAMS_DESCANSO = {
    "nombre": "descanso",
    "prob_base": _PROB_BASE_DESCANSO_PUERTA,
    "incremento": _PITY_INCREMENT_DESCANSO_POR_SALA,
    "prob_max": _PROB_PUERTA_ESPECIAL_MAX,
    "hard_sala": SALAS_HARD_PITY_DESCANSO_ESCAPE,
    "hard_umbral_sin": SALAS_HARD_PITY_DESCANSO_ESCAPE - 1,
}
PARAMS_TIENDA = {
    "nombre": "tienda",
    "prob_base": _PROB_BASE_TIENDA_PUERTA,
    "incremento": _PITY_INCREMENT_TIENDA_POR_SALA,
    "prob_max": _PROB_PUERTA_ESPECIAL_MAX,
    "hard_sala": SALAS_HARD_PITY_TIENDA_ESCAPE,
    "hard_umbral_sin": SALAS_HARD_PITY_TIENDA_ESCAPE - 1,
}


@dataclass
class ResultadoModeloSimplificado:
    primera_sala: int | None
    max_racha_sin: int


def _media(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def prob_soft(salas_sin_ver: int, *, prob_base: float, incremento: float, prob_max: float) -> float:
    return prob_puerta_especial_con_pity(
        prob_base=prob_base,
        salas_sin_ver=salas_sin_ver,
        incremento_por_sala=incremento,
        prob_max=prob_max,
    )


def simular_modelo_simplificado(
    rng: RngPartida,
    *,
    n_salas: int,
    prob_base: float,
    incremento: float,
    prob_max: float,
    hard_umbral_sin: int | None,
    hard_sala: int | None,
) -> ResultadoModeloSimplificado:
    """Un intento Bernoulli por sala; hard pity fuerza éxito al superar el umbral."""
    sin_ver = 0
    max_racha = 0
    primera: int | None = None
    for sala in range(1, n_salas + 1):
        max_racha = max(max_racha, sin_ver)
        forzar = (
            hard_umbral_sin is not None
            and hard_sala is not None
            and sala >= hard_sala
            and sin_ver >= hard_umbral_sin
        )
        p = prob_soft(sin_ver, prob_base=prob_base, incremento=incremento, prob_max=prob_max)
        if forzar or rng.random() < p:
            if primera is None:
                primera = sala
            sin_ver = 0
        else:
            sin_ver += 1
    return ResultadoModeloSimplificado(primera_sala=primera, max_racha_sin=max_racha)


def _puerta_tiene(puertas: tuple, eid: str) -> bool:
    return any(eid in p.modificadores.eventos_ids for p in puertas)


def _sala_tiene_botin(puertas: tuple) -> bool:
    return any(
        any(eid in RASGOS_BOTIN_ESCAPE for eid in p.modificadores.eventos_ids) for p in puertas
    )


@dataclass
class ResultadoPartidaEscape:
    primera_descanso: int | None
    primera_tienda: int | None
    primera_botin: int | None
    max_sin_descanso: int
    max_sin_tienda: int
    max_sin_botin: int
    descansos: int
    tiendas: int
    botines: int


def simular_partida_escape(
    *,
    config,
    materias_pool: tuple[str, ...],
    pool_preguntas: list,
    semilla: int,
) -> ResultadoPartidaEscape:
    rng = RngPartida.desde_semilla(semilla)
    pity = PityPuertasEspecialesEscape()
    primera_d = primera_t = primera_b = None
    max_sd = max_st = max_sb = 0
    n_d = n_t = n_b = 0
    for idx, sala in enumerate(config.salas):
        puertas, pity = generar_puertas_sala(
            sala,
            idx,
            materias_pool=materias_pool,
            pool_preguntas=pool_preguntas,
            rng=rng,
            n_salas=config.n_salas,
            pity=pity,
        )
        max_sd = max(max_sd, pity.salas_sin_descanso)
        max_st = max(max_st, pity.salas_sin_tienda)
        max_sb = max(max_sb, pity.salas_sin_botin)
        if _puerta_tiene(puertas, "descanso"):
            n_d += 1
            if primera_d is None:
                primera_d = idx + 1
        if _puerta_tiene(puertas, "tienda"):
            n_t += 1
            if primera_t is None:
                primera_t = idx + 1
        if _sala_tiene_botin(puertas):
            n_b += 1
            if primera_b is None:
                primera_b = idx + 1
    return ResultadoPartidaEscape(
        primera_descanso=primera_d,
        primera_tienda=primera_t,
        primera_botin=primera_b,
        max_sin_descanso=max_sd,
        max_sin_tienda=max_st,
        max_sin_botin=max_sb,
        descansos=n_d,
        tiendas=n_t,
        botines=n_b,
    )


def _resumir_modelo(
    resultados: list[ResultadoModeloSimplificado],
    *,
    hard_umbral_sin: int | None,
) -> dict[str, float | int]:
    sin_evento = sum(1 for r in resultados if r.primera_sala is None)
    primeras = [r.primera_sala for r in resultados if r.primera_sala is not None]
    max_rachas = [r.max_racha_sin for r in resultados]
    frac_antes_hard = 0.0
    if hard_umbral_sin is not None and primeras:
        frac_antes_hard = sum(1 for s in primeras if s <= hard_umbral_sin) / len(resultados)
    return {
        "frac_sin_evento": sin_evento / len(resultados) if resultados else 0.0,
        "sala_media_primer_evento": round(_media([float(s) for s in primeras]), 2) if primeras else 0.0,
        "max_racha_media": round(_media([float(x) for x in max_rachas]), 2),
        "max_racha_p95": sorted(max_rachas)[int(0.95 * (len(max_rachas) - 1))] if max_rachas else 0,
        "frac_primer_evento_antes_hard": round(frac_antes_hard, 4),
    }


def _resumir_escape(resultados: list[ResultadoPartidaEscape]) -> dict[str, float | int]:
    if not resultados:
        return {}
    def _primera(campo: str) -> list[int]:
        return [getattr(r, campo) for r in resultados if getattr(r, campo) is not None]

    pd = _primera("primera_descanso")
    pt = _primera("primera_tienda")
    pb = _primera("primera_botin")
    return {
        "descansos_media": round(_media([float(r.descansos) for r in resultados]), 2),
        "tiendas_media": round(_media([float(r.tiendas) for r in resultados]), 2),
        "botines_media": round(_media([float(r.botines) for r in resultados]), 2),
        "primera_descanso_media": round(_media([float(x) for x in pd]), 2) if pd else 0.0,
        "primera_tienda_media": round(_media([float(x) for x in pt]), 2) if pt else 0.0,
        "primera_botin_media": round(_media([float(x) for x in pb]), 2) if pb else 0.0,
        "max_sin_descanso_p95": sorted(r.max_sin_descanso for r in resultados)[
            int(0.95 * (len(resultados) - 1))
        ],
        "max_sin_tienda_p95": sorted(r.max_sin_tienda for r in resultados)[
            int(0.95 * (len(resultados) - 1))
        ],
        "frac_sin_descanso_30": sum(1 for r in resultados if r.descansos == 0) / len(resultados),
    }


def ejecutar_simulacion(
    *,
    iteraciones: int,
    iteraciones_escape: int | None,
    n_salas: int,
    semilla: int,
) -> dict[str, object]:
    rng_base = RngPartida.desde_semilla(semilla_estable_texto(f"pity-base-{semilla}"))
    rng_pity = RngPartida.desde_semilla(semilla_estable_texto(f"pity-model-{semilla}"))
    n_escape = iteraciones_escape if iteraciones_escape is not None else min(iteraciones, 200)
    if n_escape < 0:
        n_escape = 0

    base_descanso = [
        simular_modelo_simplificado(
            rng_base,
            n_salas=n_salas,
            prob_base=PARAMS_DESCANSO["prob_base"],
            incremento=0.0,
            prob_max=PARAMS_DESCANSO["prob_base"],
            hard_umbral_sin=None,
            hard_sala=None,
        )
        for _ in range(iteraciones)
    ]
    pity_descanso = [
        simular_modelo_simplificado(
            rng_pity,
            n_salas=n_salas,
            prob_base=PARAMS_DESCANSO["prob_base"],
            incremento=PARAMS_DESCANSO["incremento"],
            prob_max=PARAMS_DESCANSO["prob_max"],
            hard_umbral_sin=PARAMS_DESCANSO["hard_umbral_sin"],
            hard_sala=PARAMS_DESCANSO["hard_sala"],
        )
        for _ in range(iteraciones)
    ]

    materias_meta = cargar_materias(resolver_listado_materias())
    pool = construir_pool_escape(cargar_preguntas(resolver_dataset(), materias_meta))
    materias_pool = materias_del_pool(pool)
    config = config_escape_room(n_salas=n_salas)

    escape_runs = [
        simular_partida_escape(
            config=config,
            materias_pool=materias_pool,
            pool_preguntas=pool,
            semilla=semilla_estable_texto(f"escape-run-{semilla}-{i}"),
        )
        for i in range(n_escape)
    ]

    return {
        "iteraciones": iteraciones,
        "iteraciones_escape": n_escape,
        "n_salas": n_salas,
        "params_descanso": PARAMS_DESCANSO,
        "params_tienda": PARAMS_TIENDA,
        "hard_pity_botin_salas": SALAS_HARD_PITY_BOTIN_ESCAPE,
        "modelo_base_descanso": _resumir_modelo(base_descanso, hard_umbral_sin=None),
        "modelo_pity_descanso": _resumir_modelo(
            pity_descanso, hard_umbral_sin=PARAMS_DESCANSO["hard_umbral_sin"]
        ),
        "escape": _resumir_escape(escape_runs),
        "primera_descanso_histograma": [r.primera_descanso for r in escape_runs],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulación del sistema de pity.")
    parser.add_argument("--iteraciones", type=int, default=10_000)
    parser.add_argument(
        "--iteraciones-escape",
        type=int,
        default=None,
        help="Réplicas del generador real (por defecto min(iteraciones, 600))",
    )
    parser.add_argument("--salas", type=int, default=SALAS_DEFECTO)
    parser.add_argument("--semilla", type=int, default=42)
    args = parser.parse_args(argv)

    stats = ejecutar_simulacion(
        iteraciones=args.iteraciones,
        iteraciones_escape=args.iteraciones_escape,
        n_salas=args.salas,
        semilla=args.semilla,
    )
    base = stats["modelo_base_descanso"]
    pity = stats["modelo_pity_descanso"]
    esc = stats["escape"]

    print("=== SIMULACIÓN SISTEMA DE PITY ===")
    print(
        f"Réplicas modelo: {stats['iteraciones']} | escape: {stats['iteraciones_escape']} | "
        f"Salas: {stats['n_salas']}"
    )
    print()
    print("--- Modelo simplificado (puerta descanso, Bernoulli/sala) ---")
    print(f"  Sin pity (p={PARAMS_DESCANSO['prob_base']:.0%} fijo):")
    print(f"    Fracción sin descanso en {stats['n_salas']} salas: {base['frac_sin_evento']:.1%}")
    print(f"    Racha media sin descanso: {base['max_racha_media']}")
    print(f"    Racha p95 sin descanso: {base['max_racha_p95']}")
    print(f"  Con pity suave + hard (sala {PARAMS_DESCANSO['hard_sala']}):")
    print(f"    Fracción sin descanso: {pity['frac_sin_evento']:.1%}")
    print(f"    Sala media del primer descanso: {pity['sala_media_primer_evento']}")
    print(f"    Racha p95 sin descanso: {pity['max_racha_p95']}")
    print(f"    Primer descanso antes del hard pity: {pity['frac_primer_evento_antes_hard']:.1%}")
    print()
    if esc:
        print("--- Escape room completo (generar_puertas_sala) ---")
        print(f"  Descansos por partida (media): {esc['descansos_media']}")
        print(f"  Tiendas por partida (media): {esc['tiendas_media']}")
        print(f"  Botines por partida (media): {esc['botines_media']}")
        print(f"  Primera sala con descanso (media): {esc['primera_descanso_media']}")
        print(f"  Primera sala con tienda (media): {esc['primera_tienda_media']}")
        print(f"  Racha p95 sin descanso: {esc['max_sin_descanso_p95']}")
        print(f"  Partidas sin ningún descanso: {esc['frac_sin_descanso_30']:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
