#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica correcciones de Materia/contenido revisadas manualmente."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from balance_lib import PATCHES as _PATCHES_ALL

# Solo filas cuyo enunciado sigue siendo claramente incorrecto para la Materia actual
PATCHES_CONTENIDO: dict[int, dict[str, str]] = {
    22: _PATCHES_ALL[22],
}
from borrar_pycache import borrar_pycache_en_proyecto
from utils_dataset_csv import guardar_filas_csv, materia_de_fila
from utils_puntuacion_materia import recargar_criterios

PATH_CSV = BASE / "Data" / "Preguntas.csv"
PATH_PL = BASE / "Data" / "plantillas.json"
PATH_CRIT = BASE / "Data" / "criterios_clasificacion_materia.csv"

# Id -> nueva Materia (tras revisión manual + keywords corregidos)
CAMBIOS_MATERIA: dict[int, str] = {
    13: "Càlcul Numèric",
    15: "Càlcul en Diverses Variables",
    24: "Bases de Dades Relacionals",
    51: "Anàlisi Topològica de Dades",
    69: "Anàlisi Complexa i de Fourier",
    159: "Càlcul en una Variable",
    164: "Aprenentatge Computacional",
    178: "Anàlisi de Dades Complexes",
    185: "Càlcul Numèric",
    189: "Probabilitat",
    207: "Optimització",
    277: "Probabilitat",
    280: "Anàlisi de Dades Financeres",
    282: "Fonaments de Computadors",
    329: "Algorítmia i Combinatòria en Grafs. Mètodes Heurístics",
    333: "Sistemes Distribuïts i el Núvol",
}

# Palabras clave extra en criterios (se añaden si no existen)
KW_EXTRA: dict[int, list[str]] = {
    17: ["pca", "componentes principales", "analisis de componentes principales"],
    26: ["$group", "ventaja nosql", "datos no estructurados"],
    29: ["throughput", "teorema cap"],
    31: ["valor presente", "factor de descuento", "descuento"],
}


def _añadir_keywords_criterios() -> None:
    rows = list(csv.DictReader(PATH_CRIT.open(encoding="utf-8"), delimiter=";"))
    by_id = {int(r["Id"]): r for r in rows}
    for mid, extras in KW_EXTRA.items():
        if mid not in by_id:
            continue
        actuales = [p.strip() for p in by_id[mid]["Palabras_clave"].split("|") if p.strip()]
        vistos = {a.lower() for a in actuales}
        for e in extras:
            if e.lower() not in vistos:
                actuales.append(e)
                vistos.add(e.lower())
        by_id[mid]["Palabras_clave"] = " | ".join(actuales)
        by_id[mid]["N_palabras_clave"] = str(len(actuales))
    fn = list(rows[0].keys())
    with PATH_CRIT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fn, delimiter=";")
        w.writeheader()
        for i in sorted(by_id):
            w.writerow(by_id[i])
    recargar_criterios()
    print("Keywords ampliados en criterios_clasificacion_materia.csv")


def aplicar_dataset() -> int:
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)

    n = 0
    for row in filas:
        rid = int(row["Id"])
        # Solo parches de contenido puntuales (no todo el dict de balance corregir)
        if rid in PATCHES_CONTENIDO:
            for k, v in PATCHES_CONTENIDO[rid].items():
                row[k] = v
            n += 1
            print(f"  Id {rid}: parche de contenido")
        if rid in CAMBIOS_MATERIA:
            ant = materia_de_fila(row)
            row["Materia"] = CAMBIOS_MATERIA[rid]
            if ant != row["Materia"]:
                print(f"  Id {rid}: Materia {ant!r} -> {row['Materia']!r}")
                n += 1

    guardar_filas_csv(fieldnames, filas, PATH_CSV)
    print(f"Guardado {PATH_CSV} ({n} cambios)")
    return n


def aplicar_plantillas() -> bool:
    """Solo en la primera ejecución; evita re-mover si ya se aplicó."""
    return True


def _aplicar_plantillas_mov() -> int:
    """Reubica plantillas claramente fuera de tema (lista curada)."""
    MOVIMIENTOS: list[tuple[str, int, str]] = [
        ("Iniciació a la Programació", 3, "Programació Orientada als Objectes"),
        ("Programari de Sistema", 13, "Fonaments de Computadors"),
        ("Tècniques de Disseny d'Algoritmes", 3, "Programació Orientada als Objectes"),
        ("Física, Abstracció i Computació", 5, "Teoria de Jocs"),
        ("Modelització i Simulació", 2, "Probabilitat"),
        ("Sistemes Distribuïts i el Núvol", 3, "Fonaments de Computadors"),
        ("Sistemes Distribuïts i el Núvol", 4, "Fonaments de Computadors"),
        ("Internet de les Coses", 10, "Visió per Computador"),
    ]

    with PATH_PL.open(encoding="utf-8") as f:
        pl = json.load(f)

    nuevas: dict[str, list] = {t: list(items) for t, items in pl.items()}
    n = 0
    for tema_orig, idx, dest in MOVIMIENTOS:
        items = pl.get(tema_orig, [])
        if idx >= len(items):
            continue
        t = items[idx]
        nuevas[tema_orig] = [x for j, x in enumerate(items) if j != idx]
        if dest not in nuevas:
            nuevas[dest] = []
        nuevas[dest].append(t)
        n += 1
        print(f"  plantilla {tema_orig}#{idx} -> {dest!r}")

    with PATH_PL.open("w", encoding="utf-8") as f:
        json.dump(nuevas, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Guardado {PATH_PL} ({n} plantillas movidas)")
    return n


def main() -> None:
    import argparse
    import subprocess

    parser = argparse.ArgumentParser()
    parser.add_argument("--solo-dataset", action="store_true")
    parser.add_argument("--solo-plantillas", action="store_true")
    args = parser.parse_args()

    if not args.solo_plantillas:
        _añadir_keywords_criterios()
        subprocess.run(
            [sys.executable, "Files/exportar_criterios_clasificacion_materia.py"],
            cwd=BASE,
            check=True,
        )
        print("\n=== Dataset ===")
        aplicar_dataset()
    if not args.solo_dataset:
        print("\n=== Plantillas (subconjunto curado) ===")
        _aplicar_plantillas_mov()


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
