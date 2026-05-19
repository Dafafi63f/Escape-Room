#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI: clasifica una pregunta (o filas del dataset) por Materia, Tipo y Dificultad.

  python Files/clasificar_pregunta.py --id 42
  python Files/clasificar_pregunta.py -q "¿Qué es un kernel?" -a "..." -b "..." -c "..." -d "..." -c A
  python Files/clasificar_pregunta.py --dataset
  python Files/clasificar_pregunta.py --dataset --solo-incoherentes
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils_clasificacion_pregunta import (
    clasificar_pregunta,
    comparar_con_asignacion,
)
from utils_dataset_csv import materia_de_fila

PATH_CSV = BASE / "Data" / "Preguntas.csv"


def _imprimir_clasificacion(cl, titulo: str = "") -> None:
    if titulo:
        print(titulo)
    print(f"  {cl.resumen()}")
    print(f"  Top materias: {cl.top_materias(4)}")
    print(f"  Tipo (scores): {cl.scores_tipo}")
    print(f"  Dificultad (scores): {cl.scores_dificultad}")


def _imprimir_comparacion(cmp, id_: str | None = None) -> None:
    pref = f"Id {id_}: " if id_ else ""
    pre = cmp.inferido.pregunta[:90].encode("utf-8", errors="replace").decode("utf-8")
    print(f"{pref}{pre}")
    print(
        f"  Asignado:  Materia={cmp.asignado['Materia']!r} | "
        f"Tipo={cmp.asignado['Tipo']} | Dificultad={cmp.asignado['Dificultad']}"
    )
    print(f"  Inferido: {cmp.inferido.resumen()}")
    print(f"  Dificultad (scores): {cmp.inferido.scores_dificultad}")
    if cmp.campos_incoherentes:
        print(f"  Incoherente en: {', '.join(cmp.campos_incoherentes)}")
    else:
        dif_nota = ""
        if cmp.asignado["Dificultad"] != cmp.inferido.dificultad:
            dif_nota = " (dificultad: asignada por escalera del bloque, inferida por contenido)"
        print(f"  Coherente en Materia/Tipo{dif_nota}")


def cmd_texto(args: argparse.Namespace) -> int:
    cl = clasificar_pregunta(args.pregunta, args.a, args.b, args.c, args.d, args.correcta)
    _imprimir_clasificacion(cl, "Clasificación inferida:")
    return 0


def cmd_id(args: argparse.Namespace) -> int:
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        rows = {r["Id"]: r for r in csv.DictReader(f, delimiter=";")}
    row = rows.get(str(args.id))
    if not row:
        print(f"No existe Id {args.id}")
        return 1
    cmp = comparar_con_asignacion(row)
    _imprimir_comparacion(cmp, args.id)
    return 0


def cmd_dataset(args: argparse.Namespace) -> int:
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    incoherentes = 0
    for row in rows:
        cmp = comparar_con_asignacion(row)
        if args.solo_incoherentes and not cmp.debe_sustituir:
            continue
        _imprimir_comparacion(cmp, row["Id"])
        print()
        if cmp.debe_sustituir:
            incoherentes += 1

    print(f"=== Resumen: {len(rows)} filas, {incoherentes} con metadatos incoherentes ===")
    if incoherentes:
        print("Sustituir (no reetiquetar): python Files/revisar_materia_contenido.py --inplace")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Clasificar pregunta por contenido")
    sub = parser.add_subparsers(dest="modo")

    p_q = sub.add_parser("texto", help="Clasificar texto libre")
    p_q.add_argument("-q", "--pregunta", required=True)
    p_q.add_argument("-a", default="")
    p_q.add_argument("-b", default="")
    p_q.add_argument("-c", default="")
    p_q.add_argument("-d", default="")
    p_q.add_argument("--correcta", default="A")

    p_id = sub.add_parser("id", help="Clasificar fila por Id del CSV")
    p_id.add_argument("id", type=int)

    p_ds = sub.add_parser("dataset", help="Revisar todo el dataset")
    p_ds.add_argument("--solo-incoherentes", action="store_true")

    parser.add_argument("--id", type=int, help="Atajo: clasificar fila por Id")
    parser.add_argument("-q", "--pregunta", help="Atajo: enunciado")
    parser.add_argument("-a", default="")
    parser.add_argument("-b", default="")
    parser.add_argument("-c", default="")
    parser.add_argument("-d", default="")
    parser.add_argument("--correcta", default="A")
    parser.add_argument("--dataset", action="store_true")
    parser.add_argument("--solo-incoherentes", action="store_true")

    args = parser.parse_args()

    if args.dataset:
        return cmd_dataset(args)
    if args.id is not None:
        return cmd_id(argparse.Namespace(id=args.id))
    if args.pregunta:
        return cmd_texto(args)
    if args.modo == "texto":
        return cmd_texto(args)
    if args.modo == "id":
        return cmd_id(args)
    if args.modo == "dataset":
        return cmd_dataset(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
