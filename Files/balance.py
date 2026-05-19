#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto único de entrada para balance de Data/Preguntas.csv.

Uso:
  python Files/balance.py validar [--detalle] [--estricto]
  python Files/balance.py ajustar [--dry-run] [--sin-dificultad] [--intercambios]
  python Files/balance.py reordenar [--solo-metadatos] [--explicar]
  python Files/balance.py corregir              # parches + git HEAD (destructivo)
  python Files/balance.py conservador           # regenerar + reordenar (flujo habitual)
  python Files/balance.py conservador --corregir  # incluye corregir antes
  python Files/balance.py agresivo              # duplicados + regenerar + reordenar completo

Flujo habitual: duplicados.py revisar → todo --inplace → aplicar_clasificacion_optima.py --inplace
  → balance.py conservador.
Clasificación por contenido: clasificar_pregunta.py (Materia+Tipo+Dificultad).
Por defecto se borran filas mal encajadas y se crean nuevas desde plantillas.
Ver Memoria_TFG.md §14.4.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FILES = Path(__file__).resolve().parent
sys.path.insert(0, str(FILES))

from borrar_pycache import borrar_pycache_en_proyecto
from objetivos_balanceo import (
    TARGET_TOTAL_PREGUNTAS,
    objetivos_correcta_por_letra,
    objetivos_dificultad_por_totales,
    preguntas_por_materia,
    preguntas_por_tipo_global,
)
from utils_dataset_csv import materia_de_fila

PATH_CSV = BASE / "Data" / "Preguntas.csv"
MAX_ITER_AGRESIVO = 15

# Pasos de regeneración (dataset_pipeline.py), tras duplicados exacto
PASOS_AGRESIVO: list[tuple[str, str]] = [
    ("TEMAS", "materias"),
    ("TIPO+DIFICULTAD", "tipo+dificultad por materia"),
    ("TIPOS", "tipos globales"),
    ("DIFICULTAD", "dificultad global"),
    ("CORRECTAS", "correctas ABCD"),
]


def _run_script(nombre: str, *extra: str) -> bool:
    cmd = [sys.executable, str(FILES / nombre), *extra]
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=BASE).returncode == 0


def cmd_validar(args: argparse.Namespace) -> int:
    from balance_lib import ejecutar_validar

    return ejecutar_validar(detalle=args.detalle, estricto=args.estricto)


def cmd_ajustar(args: argparse.Namespace) -> int:
    from balance_lib import ejecutar_ajuste

    return ejecutar_ajuste(
        dry_run=args.dry_run,
        sin_dificultad=args.sin_dificultad,
        intercambios=args.intercambios,
    )


def cmd_reordenar(args: argparse.Namespace) -> int:
    from balance_lib import ejecutar_reordenar

    try:
        return ejecutar_reordenar(
            solo_metadatos=args.solo_metadatos,
            explicar=args.explicar,
            sin_permutar_respuestas=args.sin_permutar_respuestas,
        )
    except SystemExit as e:
        code = e.code
        return int(code) if isinstance(code, int) else 1


def cmd_corregir(_args: argparse.Namespace) -> int:
    from balance_lib import ejecutar_corregir

    return ejecutar_corregir()


def cmd_conservador(args: argparse.Namespace) -> int:
    if args.corregir:
        rc = cmd_corregir(args)
        if rc != 0:
            return rc

    rc = cmd_validar(argparse.Namespace(detalle=False, estricto=False))
    if rc != 0 and not args.force:
        print("(Hay desviaciones; continúa con ajustar…)", flush=True)

    rc = cmd_ajustar(
        argparse.Namespace(
            dry_run=False,
            sin_dificultad=args.sin_dificultad,
            intercambios=False,
        )
    )
    if rc != 0:
        return rc

    cmd_validar(argparse.Namespace(detalle=False, estricto=False))

    rc = cmd_reordenar(
        argparse.Namespace(
            solo_metadatos=True,
            explicar=False,
            sin_permutar_respuestas=True,
        )
    )
    if rc != 0:
        return rc

    print("\nPipeline conservador terminado.", flush=True)
    return cmd_validar(argparse.Namespace(detalle=args.detalle, estricto=False))


def _esta_balanceado() -> tuple[bool, str]:
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    n = len(rows)
    if n != TARGET_TOTAL_PREGUNTAS:
        return False, f"Total {n} != {TARGET_TOTAL_PREGUNTAS}"

    tgt_m = preguntas_por_materia()
    por_tema = Counter(materia_de_fila(r) for r in rows)
    if por_tema and (min(por_tema.values()) != tgt_m or max(por_tema.values()) != tgt_m):
        return False, f"Temas: min={min(por_tema.values())}, max={max(por_tema.values())} (obj. {tgt_m})"

    tgt_diff = objetivos_dificultad_por_totales(n)
    por_dificultad = Counter(r["Dificultad"] for r in rows)
    for d in ["Facil", "Media", "Dificil"]:
        if por_dificultad.get(d, 0) != tgt_diff[d]:
            return False, f"Dificultad {d}: {por_dificultad.get(d, 0)} (obj. {tgt_diff[d]})"

    tgt_tipo = preguntas_por_tipo_global()
    por_tipo = Counter(r["Tipo"] for r in rows)
    if por_tipo.get("Teoria", 0) != tgt_tipo or por_tipo.get("Calculo", 0) != tgt_tipo:
        return False, f"Tipos: Teoria={por_tipo.get('Teoria', 0)}, Calculo={por_tipo.get('Calculo', 0)}"

    tgt_corr = objetivos_correcta_por_letra(n)
    por_correcta = Counter(r["Correcta"] for r in rows)
    for letra in ["A", "B", "C", "D"]:
        if por_correcta.get(letra, 0) != tgt_corr[letra]:
            return False, f"Correcta {letra}: {por_correcta.get(letra, 0)} (obj. {tgt_corr[letra]})"

    return True, "OK"


def cmd_agresivo(_args: argparse.Namespace) -> int:
    from dataset_pipeline import PASOS_PIPELINE, ejecutar_pipeline_regenerar

    print("=" * 60, flush=True)
    print(f"BALANCEO AGRESIVO (objetivo: {TARGET_TOTAL_PREGUNTAS} preguntas)", flush=True)
    print("=" * 60, flush=True)

    if not _run_script("duplicados.py", "exacto"):
        return 1

    pasos_por_nombre = {nombre: fn for nombre, fn in PASOS_PIPELINE}

    for iteracion in range(1, MAX_ITER_AGRESIVO + 1):
        print(f"\n--- Iteración {iteracion}/{MAX_ITER_AGRESIVO} ---", flush=True)
        for etiqueta, clave in PASOS_AGRESIVO:
            print(f"\n>>> {etiqueta}", flush=True)
            pasos_por_nombre[clave]()

        ok, msg = _esta_balanceado()
        if ok:
            if cmd_reordenar(
                argparse.Namespace(
                    solo_metadatos=False,
                    explicar=False,
                    sin_permutar_respuestas=False,
                )
            ) != 0:
                return 1
            print("\n" + "=" * 60, flush=True)
            print(f"BALANCEO AGRESIVO FINALIZADO (iteración {iteracion})", flush=True)
            print("=" * 60, flush=True)
            return 0

        print(f"\n[Iteración {iteracion}] Aún desbalanceado: {msg}", flush=True)

    print("\n[AVISO] Máximo de iteraciones sin equilibrio completo.", flush=True)
    _, msg = _esta_balanceado()
    print(f"Estado final: {msg}", flush=True)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Balance del dataset Preguntas.csv (400 filas, 40 materias)."
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_val = sub.add_parser("validar", help="Comprueba balance sin modificar el CSV")
    p_val.add_argument("--detalle", action="store_true")
    p_val.add_argument("--estricto", action="store_true")

    p_aj = sub.add_parser(
        "ajustar",
        help="Borra filas mal encajadas y regenera desde plantillas (por defecto)",
    )
    p_aj.add_argument("--dry-run", action="store_true")
    p_aj.add_argument("--sin-dificultad", action="store_true")
    p_aj.add_argument(
        "--intercambios",
        action="store_true",
        help="Obsoleto: solo intercambia etiquetas sin cambiar el enunciado",
    )

    p_re = sub.add_parser("reordenar", help="Orden canónico (listado, ladder, Id, ABCD)")
    p_re.add_argument("--solo-metadatos", action="store_true")
    p_re.add_argument("--explicar", action="store_true")
    p_re.add_argument("--sin-permutar-respuestas", action="store_true")

    sub.add_parser("corregir", help="Restaura desde git HEAD y aplica parches (destructivo)")

    p_co = sub.add_parser(
        "conservador",
        help="Regenerar balance (plantillas) + reordenar --solo-metadatos",
    )
    p_co.add_argument(
        "--corregir",
        action="store_true",
        help="Ejecuta corregir (git HEAD) antes del resto",
    )
    p_co.add_argument("--sin-dificultad", action="store_true")
    p_co.add_argument("--detalle", action="store_true", help="Validación final con detalle")
    p_co.add_argument("--force", action="store_true", help="No parar si validar inicial falla")

    sub.add_parser(
        "agresivo",
        help="Elimina/regenera preguntas hasta equilibrio (pipeline antiguo)",
    )

    args = parser.parse_args(argv)
    handlers = {
        "validar": cmd_validar,
        "ajustar": cmd_ajustar,
        "reordenar": cmd_reordenar,
        "corregir": cmd_corregir,
        "conservador": cmd_conservador,
        "agresivo": cmd_agresivo,
    }
    try:
        return handlers[args.comando](args)
    finally:
        borrar_pycache_en_proyecto()


if __name__ == "__main__":
    raise SystemExit(main())
