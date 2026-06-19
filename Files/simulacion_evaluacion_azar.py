#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulación Monte Carlo: respuestas aleatorias A–D frente al banco cerrado.

Contrasta que el azar produce bajo rendimiento (≈25 % aciertos, nota ≈2,5/10)
y que el sistema de vidas expulsa al jugador antes de completar bloques largos.

  python Files/simulacion_evaluacion_azar.py
  python Files/simulacion_evaluacion_azar.py --iteraciones 50000 --preguntas 20
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
from Comun.modelos import Pregunta  # noqa: E402
from Comun.reglas_partida import calcular_puntos_arcade, nota_sobre_diez  # noqa: E402
from Comun.rutas import resolver_dataset, resolver_listado_materias  # noqa: E402

_LETRAS = ("A", "B", "C", "D")
_PROB_ACIERTO_TEORICA = 0.25


@dataclass
class ResultadoSimulacion:
    aciertos: int
    respondidas: int
    nota: float
    puntos_arcade: int
    vidas_restantes: int
    agotado_vidas: bool


def _respuesta_azar(rng: random.Random) -> str:
    return rng.choice(_LETRAS)


def simular_examen(
    preguntas: list[Pregunta],
    n_objetivo: int,
    rng: random.Random,
) -> ResultadoSimulacion:
    """Modo examen (sin vidas): nota sobre 10."""
    muestra = rng.sample(preguntas, min(n_objetivo, len(preguntas)))
    aciertos = sum(1 for p in muestra if _respuesta_azar(rng) == p.correcta)
    total = len(muestra)
    return ResultadoSimulacion(
        aciertos=aciertos,
        respondidas=total,
        nota=nota_sobre_diez(aciertos, total),
        puntos_arcade=0,
        vidas_restantes=0,
        agotado_vidas=False,
    )


def simular_arcade_vidas(
    preguntas: list[Pregunta],
    n_objetivo: int,
    vidas_iniciales: int,
    rng: random.Random,
) -> ResultadoSimulacion:
    """Preset arcade: 3 vidas, puntuación +/- según dificultad."""
    muestra = rng.sample(preguntas, min(n_objetivo, len(preguntas)))
    aciertos = 0
    respondidas = 0
    puntos = 0
    vidas = vidas_iniciales
    for p in muestra:
        respondidas += 1
        ok = _respuesta_azar(rng) == p.correcta
        if ok:
            aciertos += 1
            puntos += calcular_puntos_arcade(p.dificultad, True)
        else:
            puntos += calcular_puntos_arcade(p.dificultad, False)
            vidas -= 1
            if vidas <= 0:
                break
    return ResultadoSimulacion(
        aciertos=aciertos,
        respondidas=respondidas,
        nota=nota_sobre_diez(aciertos, respondidas),
        puntos_arcade=puntos,
        vidas_restantes=max(0, vidas),
        agotado_vidas=vidas <= 0,
    )


def _media(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def ejecutar_simulacion(
    preguntas: list[Pregunta],
    *,
    iteraciones: int,
    n_preguntas: int,
    semilla: int,
) -> dict[str, object]:
    rng = random.Random(semilla)
    examenes = [simular_examen(preguntas, n_preguntas, rng) for _ in range(iteraciones)]
    arcades = [
        simular_arcade_vidas(preguntas, n_preguntas, 3, rng) for _ in range(iteraciones)
    ]

    notas_examen = [r.nota for r in examenes]
    aciertos_examen = [r.aciertos / r.respondidas for r in examenes]
    notas_arcade = [r.nota for r in arcades]
    puntos_arcade = [r.puntos_arcade for r in arcades]
    frac_agotado = sum(1 for r in arcades if r.agotado_vidas) / iteraciones
    respondidas_arcade = [r.respondidas for r in arcades]

    return {
        "iteraciones": iteraciones,
        "n_preguntas": n_preguntas,
        "n_banco": len(preguntas),
        "prob_acierto_teorica": _PROB_ACIERTO_TEORICA,
        "examen_nota_media": round(_media(notas_examen), 2),
        "examen_aciertos_frac_media": round(_media(aciertos_examen), 4),
        "examen_nota_min": round(min(notas_examen), 1),
        "examen_nota_max": round(max(notas_examen), 1),
        "arcade_nota_media": round(_media(notas_arcade), 2),
        "arcade_puntos_media": round(_media(puntos_arcade), 1),
        "arcade_frac_agotado_vidas": round(frac_agotado, 4),
        "arcade_respondidas_media": round(_media(respondidas_arcade), 2),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simulación Monte Carlo de evaluación al azar.")
    parser.add_argument("--iteraciones", type=int, default=10_000)
    parser.add_argument("--preguntas", type=int, default=20)
    parser.add_argument("--semilla", type=int, default=42)
    args = parser.parse_args(argv)

    path_csv = resolver_dataset()
    path_materias = resolver_listado_materias()
    materias_meta = cargar_materias(path_materias)
    preguntas = cargar_preguntas(path_csv, materias_meta)
    if not preguntas:
        print("Error: banco vacío.", file=sys.stderr)
        return 1

    stats = ejecutar_simulacion(
        preguntas,
        iteraciones=args.iteraciones,
        n_preguntas=args.preguntas,
        semilla=args.semilla,
    )

    print("=== SIMULACIÓN EVALUACIÓN AL AZAR ===")
    print(f"Banco: {stats['n_banco']} preguntas | Iteraciones: {stats['iteraciones']}")
    print(f"Preguntas por partida simulada: {stats['n_preguntas']}")
    print(f"Probabilidad teórica de acierto por ítem: {stats['prob_acierto_teorica']:.0%}")
    print()
    print("--- Modo examen (nota /10, sin vidas) ---")
    print(f"  Fracción media de aciertos: {stats['examen_aciertos_frac_media']:.2%}")
    print(f"  Nota media: {stats['examen_nota_media']}/10")
    print(f"  Rango notas: {stats['examen_nota_min']} – {stats['examen_nota_max']}")
    print()
    print("--- Modo arcade (3 vidas, puntuación +/-) ---")
    print(f"  Nota media (sobre preguntas respondidas): {stats['arcade_nota_media']}/10")
    print(f"  Puntos arcade medios: {stats['arcade_puntos_media']}")
    print(f"  Partidas que agotan vidas antes de terminar: {stats['arcade_frac_agotado_vidas']:.1%}")
    print(f"  Preguntas respondidas de media: {stats['arcade_respondidas_media']}/{stats['n_preguntas']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
