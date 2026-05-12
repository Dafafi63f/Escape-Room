#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inyecta las preguntas actuales del dataset en plantillas.json, manteniendo
las plantillas existentes y evitando duplicados exactos.
"""

import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
from borrar_pycache import borrar_pycache_en_proyecto


BASE = Path(__file__).resolve().parent.parent
PATH_PREGUNTAS = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"
BACKUPS_DIR = BASE / "Backups"


def norm(text: str) -> str:
    return (text or "").strip().lower()


def key_from_template(tema: str, t: dict) -> tuple:
    return (
        norm(tema),
        norm(t.get("pregunta", "")),
        norm(t.get("A", "")),
        norm(t.get("B", "")),
        norm(t.get("C", "")),
        norm(t.get("D", "")),
        norm(t.get("correcta", "")),
    )


def key_from_row(r: dict) -> tuple:
    return (
        norm(r.get("Materia") or r.get("Tema", "")),
        norm(r.get("Pregunta", "")),
        norm(r.get("A", "")),
        norm(r.get("B", "")),
        norm(r.get("C", "")),
        norm(r.get("D", "")),
        norm(r.get("Correcta", "")),
    )


def main() -> None:
    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        plantillas = json.load(f)

    with PATH_PREGUNTAS.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    # Índice de duplicados exactos de plantillas ya existentes
    existing_keys = set()
    for tema, items in plantillas.items():
        for t in items:
            existing_keys.add(key_from_template(tema, t))

    added = 0
    already_present = 0
    missing_topic = 0

    for r in rows:
        tema = (r.get("Materia") or r.get("Tema") or "").strip()
        if not tema:
            continue
        if tema not in plantillas:
            plantillas[tema] = []
            missing_topic += 1

        k = key_from_row(r)
        if k in existing_keys:
            already_present += 1
            continue

        new_t = {
            "pregunta": r["Pregunta"],
            "A": r["A"],
            "B": r["B"],
            "C": r["C"],
            "D": r["D"],
            "correcta": r["Correcta"],
            "dificultad": r["Dificultad"],
            "tipo": r["Tipo"],
            "uso": "dataset_400",
        }
        plantillas[tema].append(new_t)
        existing_keys.add(k)
        added += 1

    # Validación: todas las preguntas del dataset deben existir en plantillas
    final_keys = set()
    for tema, items in plantillas.items():
        for t in items:
            final_keys.add(key_from_template(tema, t))

    missing_from_dataset = 0
    for r in rows:
        if key_from_row(r) not in final_keys:
            missing_from_dataset += 1

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUPS_DIR / f"plantillas_backup_{ts}.json"
    shutil.copy2(PATH_PLANTILLAS, backup_path)

    with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
        json.dump(plantillas, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Filas dataset: {len(rows)}")
    print(f"Añadidas a plantillas: {added}")
    print(f"Ya presentes: {already_present}")
    print(f"Temas creados en plantillas: {missing_topic}")
    print(f"Faltantes tras inyección: {missing_from_dataset}")
    safe_backup_path = str(backup_path).encode("ascii", "replace").decode("ascii")
    print(f"Backup plantillas: {safe_backup_path}")


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
