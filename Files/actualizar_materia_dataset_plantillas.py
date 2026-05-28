#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actualiza la Materia de TODO el dataset y plantillas usando
Data/criterios_clasificacion_materia.csv.

Regla de decision:
- Se puntua texto completo (pregunta + opciones) por materia.
- Se elige la materia con mayor puntuacion.
- En empate, gana la de menor Id (orden del listado oficial).
- Si no hay match (score vacio), se conserva la materia actual.

Uso:
  python Files/actualizar_materia_dataset_plantillas.py --dry-run
  python Files/actualizar_materia_dataset_plantillas.py --inplace
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils_dataset_csv import guardar_filas_csv, materia_de_fila
from utils_puntuacion_materia import MATERIAS, mejor_materia_por_texto

PATH_CSV = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"


def _inferir_materia(pregunta: str, a: str, b: str, c: str, d: str) -> str | None:
    mid, _ = mejor_materia_por_texto(pregunta, a, b, c, d)
    if not mid:
        return None
    return MATERIAS.get(mid)


def actualizar_dataset(inplace: bool) -> tuple[int, int]:
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)

    cambios = 0
    sin_match = 0
    for row in filas:
        actual = materia_de_fila(row)
        inferida = _inferir_materia(
            row.get("Pregunta", ""),
            row.get("A", ""),
            row.get("B", ""),
            row.get("C", ""),
            row.get("D", ""),
        )
        if not inferida:
            sin_match += 1
            continue
        if inferida != actual:
            row["Materia"] = inferida
            cambios += 1

    if inplace:
        guardar_filas_csv(fieldnames, filas, PATH_CSV)
    return cambios, sin_match


def actualizar_plantillas(inplace: bool) -> tuple[int, int]:
    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plantillas = json.load(f)

    nuevas: dict[str, list] = {m: [] for m in plantillas.keys()}
    movidas = 0
    sin_match = 0

    for materia_actual, items in plantillas.items():
        for it in items:
            inferida = _inferir_materia(
                it.get("pregunta", ""),
                it.get("A", ""),
                it.get("B", ""),
                it.get("C", ""),
                it.get("D", ""),
            )
            if not inferida:
                sin_match += 1
                inferida = materia_actual
            if inferida != materia_actual:
                movidas += 1
            if inferida not in nuevas:
                nuevas[inferida] = []
            nuevas[inferida].append(it)

    if inplace:
        with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
            json.dump(nuevas, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return movidas, sin_match


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inplace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.inplace and not args.dry_run:
        args.dry_run = True

    inplace = args.inplace and not args.dry_run

    cambios_ds, sin_ds = actualizar_dataset(inplace=inplace)
    mov_pl, sin_pl = actualizar_plantillas(inplace=inplace)

    print("=== Actualizacion por criterios ===")
    print(f"Dataset: cambios de materia = {cambios_ds}, sin_match = {sin_ds}")
    print(f"Plantillas: movidas de bucket = {mov_pl}, sin_match = {sin_pl}")
    if not inplace:
        print("Dry-run: no se han escrito cambios.")
    else:
        print(f"Guardado: {PATH_CSV}")
        print(f"Guardado: {PATH_PLANTILLAS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
