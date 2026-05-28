#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reasigna la columna Materia de Data/Preguntas.csv usando solo criterios
de Data/criterios_clasificacion_materia.csv.

Regla:
- Se puntua cada pregunta (enunciado + opciones A/B/C/D) por keywords.
- Si hay una unica materia con maxima puntuacion, esa es la "materia correcta".
- Si no hay match o hay empate en la maxima puntuacion, se marca como ambigua
  y NO se modifica para evitar romper el dataset.

Uso:
  python Files/reasignar_materia_por_criterios.py --dry-run
  python Files/reasignar_materia_por_criterios.py --inplace
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils_dataset_csv import guardar_filas_csv, materia_de_fila
from utils_puntuacion_materia import MATERIAS, puntuar_texto_completo

PATH_CSV = BASE / "Data" / "Preguntas.csv"


def _materia_unica_por_criterios(row: dict) -> tuple[str | None, str | None]:
    """
    Devuelve (materia_inferida, motivo_ambiguedad).
    - materia_inferida = None si no se puede decidir de forma unica.
    - motivo_ambiguedad en {"sin_match", "empate"} cuando aplica.
    """
    scores = puntuar_texto_completo(
        row.get("Pregunta", ""),
        row.get("A", ""),
        row.get("B", ""),
        row.get("C", ""),
        row.get("D", ""),
    )
    if not scores:
        return None, "sin_match"

    max_score = max(scores.values())
    candidatas = [mid for mid, s in scores.items() if s == max_score]
    if len(candidatas) != 1:
        return None, "empate"

    materia = MATERIAS.get(candidatas[0])
    if not materia:
        return None, "sin_match"
    return materia, None


def ejecutar(inplace: bool, dry_run: bool, max_detalle: int) -> int:
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)

    cambios: list[tuple[str, str, str, str]] = []
    ambiguas: list[tuple[str, str, str]] = []

    for row in filas:
        rid = str(row.get("Id", ""))
        materia_actual = materia_de_fila(row)
        materia_inferida, motivo = _materia_unica_por_criterios(row)

        if materia_inferida is None:
            ambiguas.append((rid, motivo or "sin_match", row.get("Pregunta", "")[:90]))
            continue

        if materia_inferida != materia_actual:
            cambios.append((rid, materia_actual, materia_inferida, row.get("Pregunta", "")[:90]))
            row["Materia"] = materia_inferida

    print(f"Filas totales: {len(filas)}")
    print(f"Cambios de Materia: {len(cambios)}")
    print(f"Ambiguas (sin tocar): {len(ambiguas)}")

    if cambios:
        print("\nPrimeros cambios:")
        for rid, ant, nue, pre in cambios[:max_detalle]:
            print(f"  Id {rid}: {ant!r} -> {nue!r} | {pre}")
        if len(cambios) > max_detalle:
            print(f"  ... y {len(cambios) - max_detalle} mas")

    if ambiguas:
        print("\nPrimeras ambiguas:")
        for rid, motivo, pre in ambiguas[:max_detalle]:
            print(f"  Id {rid}: {motivo} | {pre}")
        if len(ambiguas) > max_detalle:
            print(f"  ... y {len(ambiguas) - max_detalle} mas")

    if dry_run or not inplace:
        print("\nDry-run: no se ha modificado el CSV.")
        if ambiguas:
            print("Aviso: existen filas ambiguas; revisar criterios antes de forzar cambios.")
        return 0

    guardar_filas_csv(fieldnames, filas, PATH_CSV)
    print(f"\nGuardado: {PATH_CSV}")
    if ambiguas:
        print("Aviso: quedaron filas ambiguas sin modificar.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inplace", action="store_true", help="Escribe cambios en Data/Preguntas.csv")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra lo que cambiaria")
    parser.add_argument("--max-detalle", type=int, default=25, help="Maximo de lineas de detalle")
    args = parser.parse_args()

    if not args.inplace and not args.dry_run:
        args.dry_run = True

    return ejecutar(inplace=args.inplace, dry_run=args.dry_run, max_detalle=args.max_detalle)


if __name__ == "__main__":
    raise SystemExit(main())
