#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revisa coherencia Materia + Tipo + Dificultad frente al contenido (enunciado + opciones).

Con --inplace: borra filas incoherentes y genera preguntas nuevas desde plantillas
(con metadatos coherentes), sin cambiar solo etiquetas sobre el mismo texto.

Ver también: clasificar_pregunta.py --dataset --solo-incoherentes;
  aplicar_clasificacion_optima.py --inplace (flujo recomendado del banco, Memoria §14.4).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataset_pipeline import sustituir_filas_incoherentes
from utils_clasificacion_pregunta import comparar_con_asignacion, metadatos_optimos
from utils_dataset_csv import guardar_filas_csv, materia_de_fila

PATH_CSV = BASE / "Data" / "Preguntas.csv"
PATH_PL = BASE / "Data" / "plantillas.json"


def corregir_dataset(inplace: bool, dry_run: bool) -> int:
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)

    cambios: list[dict] = []
    for row in filas:
        cmp = comparar_con_asignacion(row)
        if not cmp.debe_sustituir:
            continue
        cambios.append(
            {
                "id": row["Id"],
                "materia": materia_de_fila(row),
                "campos": cmp.campos_incoherentes,
                "asignado": cmp.asignado,
                "optimo": metadatos_optimos(row),
                "inferido": cmp.inferido,
                "pregunta": cmp.inferido.pregunta[:100],
            }
        )

    print(f"=== Dataset ({len(filas)} filas) ===")
    print(f"Filas con metadatos incoherentes (sustituir por regeneración): {len(cambios)}")
    for c in cambios:
        pre = c["pregunta"].encode("utf-8", errors="replace").decode("utf-8")
        inf = c["inferido"]
        print(
            f"  Id {c['id']}: [{', '.join(c['campos'])}] | "
            f"asignado M={c['asignado']['Materia']!r} T={c['asignado']['Tipo']} "
            f"D={c['asignado']['Dificultad']} -> "
            f"inferido M={inf.materia!r} T={inf.tipo} D={inf.dificultad} | {pre}"
        )

    if cambios and inplace and not dry_run:
        nuevas_filas, n_gen, _ = sustituir_filas_incoherentes(filas, cambios)
        print(f"Regeneradas: {n_gen} preguntas nuevas (1 por fila sustituida)")
        guardar_filas_csv(fieldnames, nuevas_filas, PATH_CSV)
        print("Guardado:", PATH_CSV)
        print("Ejecuta después: python Files/balance.py conservador")
    return len(cambios)


def corregir_plantillas(inplace: bool, dry_run: bool) -> int:
    """Plantillas: reubica el bucket si la Materia del tema no encaja (el texto se mueve con la entrada)."""
    with PATH_PL.open(encoding="utf-8") as f:
        plantillas = json.load(f)

    movidos: list[dict] = []
    nuevas: dict[str, list] = {t: [] for t in plantillas}

    for tema_orig, items in plantillas.items():
        for i, t in enumerate(items):
            fila = {
                "Pregunta": t.get("pregunta", ""),
                "A": t.get("A", ""),
                "B": t.get("B", ""),
                "C": t.get("C", ""),
                "D": t.get("D", ""),
                "Materia": tema_orig,
                "Tipo": t.get("tipo", "Teoria"),
                "Dificultad": t.get("dificultad", "Media"),
                "Correcta": t.get("correcta", "A"),
            }
            cmp = comparar_con_asignacion(fila)
            dest = tema_orig
            if "Materia" in cmp.campos_incoherentes and cmp.inferido.materia:
                dest = cmp.inferido.materia
                movidos.append(
                    {
                        "de": tema_orig,
                        "a": dest,
                        "idx": i,
                        "campos": cmp.campos_incoherentes,
                        "pregunta": cmp.inferido.pregunta[:80],
                    }
                )
            if dest not in nuevas:
                nuevas[dest] = []
            entry = dict(t)
            if dest != tema_orig:
                entry["tipo"] = cmp.inferido.tipo
                entry["dificultad"] = cmp.inferido.dificultad
            nuevas[dest].append(entry)

    for tema in plantillas:
        if tema not in nuevas:
            nuevas[tema] = []

    print(f"\n=== Plantillas ===")
    print(f"Reubicadas por contenido (materia): {len(movidos)}")
    for m in movidos[:50]:
        pre = m["pregunta"].encode("utf-8", errors="replace").decode("utf-8")
        print(
            f"  {m['de']!r}#{m['idx']} -> {m['a']!r} "
            f"[{', '.join(m['campos'])}] | {pre}"
        )
    if len(movidos) > 50:
        print(f"  ... y {len(movidos) - 50} más")

    if movidos and inplace and not dry_run:
        with PATH_PL.open("w", encoding="utf-8") as f:
            json.dump(nuevas, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("Guardado:", PATH_PL)

    return len(movidos)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inplace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--solo-dataset", action="store_true")
    parser.add_argument("--solo-plantillas", action="store_true")
    args = parser.parse_args()

    if not args.inplace and not args.dry_run:
        args.dry_run = True

    n = 0
    if not args.solo_plantillas:
        n += corregir_dataset(args.inplace, args.dry_run)
    if not args.solo_dataset:
        n += corregir_plantillas(args.inplace, args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
