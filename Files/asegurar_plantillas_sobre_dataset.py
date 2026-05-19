# -*- coding: utf-8 -*-
"""
Garantiza que `Data/plantillas.json` tenga más preguntas que `Data/Preguntas.csv`.

Pasos:
1. Inyecta las 400 filas del CSV en plantillas (uso `dataset_400`, sin borrar el resto).
2. Comprueba que cada materia tenga al menos `plantillas_minimas_por_materia()` entradas
   (por defecto 2× las 10 preguntas del dataset → mínimo 20 por materia).

Uso:
  python asegurar_plantillas_sobre_dataset.py
  python asegurar_plantillas_sobre_dataset.py --solo-comprobar
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from objetivos_balanceo import (
    MIN_PLANTILLAS_POR_MATERIA_FACTOR,
    TARGET_TOTAL_PREGUNTAS,
    plantillas_minimas_por_materia,
    preguntas_por_materia,
)

PREGUNTAS_DATASET_POR_TEMA = preguntas_por_materia()
from utils_orden_temas import cargar_orden_temas

PATH_CSV = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"


def contar_por_materia() -> tuple[dict[str, int], Counter]:
    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plant = json.load(f)
    rows = list(csv.DictReader(PATH_CSV.open(encoding="utf-8", newline=""), delimiter=";"))
    por_plant = {m: len(plant.get(m, [])) for m in plant}
    return por_plant, Counter(r["Materia"] for r in rows)


def comprobar() -> tuple[bool, list[str]]:
    temas, _ = cargar_orden_temas()
    minimo = plantillas_minimas_por_materia()
    por_plant, por_ds = contar_por_materia()
    msgs: list[str] = []

    total_plant = sum(por_plant.values())
    if total_plant <= TARGET_TOTAL_PREGUNTAS:
        msgs.append(
            f"Total plantillas ({total_plant}) no supera el dataset ({TARGET_TOTAL_PREGUNTAS})"
        )

    for tema in temas:
        n_plant = por_plant.get(tema, 0)
        n_ds = por_ds.get(tema, preguntas_por_materia())
        if n_plant <= n_ds:
            msgs.append(f"{tema!r}: {n_plant} plantillas <= {n_ds} en dataset")
        elif n_plant < minimo:
            msgs.append(
                f"{tema!r}: {n_plant} plantillas < mínimo {minimo} "
                f"({MIN_PLANTILLAS_POR_MATERIA_FACTOR}× dataset)"
            )

    return len(msgs) == 0, msgs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--solo-comprobar",
        action="store_true",
        help="No inyecta; solo valida conteos",
    )
    args = parser.parse_args()

    if not args.solo_comprobar:
        print("Inyectando preguntas del dataset en plantillas…")
        r = subprocess.run(
            [sys.executable, str(BASE / "Files" / "inyectar_dataset_en_plantillas.py")],
            cwd=BASE,
        )
        if r.returncode != 0:
            raise SystemExit("Falló inyectar_dataset_en_plantillas.py")

    por_plant, por_ds = contar_por_materia()
    minimo = plantillas_minimas_por_materia()
    ok, msgs = comprobar()

    print()
    print(f"Dataset: {TARGET_TOTAL_PREGUNTAS} preguntas ({preguntas_por_materia()}/materia)")
    print(f"Plantillas: {sum(por_plant.values())} entradas (mínimo objetivo {minimo}/materia)")
    print(f"Ratio global plantillas/dataset: {sum(por_plant.values()) / TARGET_TOTAL_PREGUNTAS:.2f}×")
    temas, _ = cargar_orden_temas()
    ratios = [por_plant.get(m, 0) / PREGUNTAS_DATASET_POR_TEMA for m in temas]
    if ratios:
        print(f"Ratio por materia: min {min(ratios):.1f}×, max {max(ratios):.1f}×")

    if ok:
        print("\nOK: hay más plantillas que preguntas en el dataset en todas las materias.")
        return

    print("\nDesviaciones:")
    for m in msgs:
        print(f"  - {m}")
    sys.exit(1)


if __name__ == "__main__":
    main()
