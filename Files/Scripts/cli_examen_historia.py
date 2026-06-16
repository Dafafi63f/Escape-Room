#!/usr/bin/env python3
# pyright: reportMissingImports=false
# -*- coding: utf-8 -*-
"""
CLI de desarrollo: previsualiza un plan de examen (modo historia v1) en consola.

No es el motor del juego; la lógica está en Juego/Consola/generador_examen_historia.py.

Ejemplo:
  python Files/Scripts/cli_examen_historia.py --perfil refuerzo --materias 6
  python Files/Scripts/cli_examen_historia.py --perfil por_curso --curso 2
  python Files/Scripts/cli_examen_historia.py --perfil simulacro --resumen-historico

Para guardar la salida: redirige a un .txt (p. ej. ... > plan_examen.txt).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_FILES = _SCRIPTS.parent
_JUEGO = _FILES.parent / "Juego"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.datos import cargar_materias, cargar_orden_materias, cargar_preguntas  # noqa: E402
from Consola.generador_examen_historia import (  # noqa: E402
    PerfilPedagogico,
    cargar_estadisticas_historicas,
    describir_perfil,
    generar_examen,
    resumen_estadisticas,
)
from Comun.modelos import BancoPreguntas  # noqa: E402
from Comun.rutas import resolver_dataset, resolver_listado_materias  # noqa: E402


def _consola(texto: str) -> str:
    """Evita fallos de codificación en consolas Windows (cp1252)."""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    return texto.encode(enc, errors="replace").decode(enc)


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(
        description="Previsualizar examen balanceado (usa Juego/Consola/generador_examen_historia.py)",
    )
    p.add_argument(
        "--perfil",
        choices=[x.value for x in PerfilPedagogico],
        default=PerfilPedagogico.BALANCEADO.value,
    )
    p.add_argument(
        "--materias",
        type=int,
        default=6,
        help="Materias en el examen (2-20; ignorado en perfil simulacro)",
    )
    p.add_argument("--curso", type=str, default=None, help="Filtro curso (1-4) para por_curso")
    p.add_argument("--semestre", type=str, default=None, help="Filtro semestre opcional (con --curso)")
    p.add_argument("--semilla", type=int, default=None, help="Semilla aleatoria reproducible")
    p.add_argument(
        "--resumen-historico",
        action="store_true",
        help="Muestra materias más exigentes según el histórico",
    )
    args = p.parse_args(argv)

    perfil = PerfilPedagogico(args.perfil)
    if perfil == PerfilPedagogico.POR_CURSO and not args.curso:
        print("El perfil por_curso requiere --curso (1-4).", file=sys.stderr)
        return 2
    if perfil != PerfilPedagogico.SIMULACRO and not (2 <= args.materias <= 20):
        print("--materias debe estar entre 2 y 20.", file=sys.stderr)
        return 2

    path_materias = resolver_listado_materias()
    path_csv = resolver_dataset()
    materias_meta = cargar_materias(path_materias)
    preguntas = cargar_preguntas(path_csv, materias_meta)
    orden_materias = cargar_orden_materias(path_materias)
    stats = cargar_estadisticas_historicas(materias_validas=set(materias_meta))

    if args.resumen_historico:
        print(_consola(resumen_estadisticas(stats, orden_materias)))
        print()

    try:
        plan = generar_examen(
            preguntas,
            perfil=perfil,
            materias_orden=orden_materias,
            materias_meta=materias_meta,
            stats=stats,
            n_materias=args.materias,
            curso_filtro=args.curso,
            semestre_filtro=args.semestre,
            semilla=args.semilla,
        )
    except ValueError as e:
        print(f"No se pudo generar el examen: {e}", file=sys.stderr)
        return 1

    print(_consola(f"Perfil: {perfil.value} — {describir_perfil(perfil)}"))
    print(f"Banco: {BancoPreguntas.DATASET.value} ({len(preguntas)} preguntas)")
    print(_consola(f"Materias ({len(plan.materias)}): {', '.join(plan.materias)}"))
    print(f"Slots por materia ({len(plan.slots_por_materia)}): {plan.slots_por_materia}")
    print(f"Total preguntas: {len(plan.preguntas)}")
    print("\nOrden del examen:")
    for i, pr in enumerate(plan.preguntas, 1):
        snippet = pr.texto[:70] + ("…" if len(pr.texto) > 70 else "")
        print(
            _consola(
                f"  {i:>2}. [{pr.materia}] {pr.tipo}/{pr.dificultad} — {snippet}"
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
