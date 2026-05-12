#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elimina duplicados por enunciado (columna "Pregunta") en Data/Preguntas.csv.

Comportamiento:
- Mantiene la primera aparición de cada enunciado.
- Para cada duplicado restante intenta generar un reemplazo del mismo tema
  usando Data/plantillas.json.
- Si no encuentra reemplazo válido, elimina la fila duplicada.
- Renumera Id al final.

Uso:
  python Files/eliminar_duplicados_enunciado.py
  python Files/eliminar_duplicados_enunciado.py --inplace
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from utils_dataset_csv import guardar_filas_csv, ordenar_filas_por_tema_y_id, renumerar_ids
from utils_texto import normalizar_basico
from borrar_pycache import borrar_pycache_en_proyecto


BASE = Path(__file__).resolve().parent.parent
PATH_PREGUNTAS = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"
BACKUP_DIR = BASE / "Backups"


def normalizar_enunciado(texto: str) -> str:
    return normalizar_basico(texto)


def cargar_plantillas() -> dict[str, list[dict]]:
    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        return json.load(f)


def expandir_plantilla(template: dict) -> list[dict]:
    preguntas = []
    variaciones = template.get("variaciones")

    if variaciones:
        for var in variaciones:
            p = template["pregunta"]
            a = template["A"]
            b = template["B"]
            c = template["C"]
            d = template["D"]
            for key, val in var.items():
                placeholder = "{" + str(key) + "}"
                p = p.replace(placeholder, str(val))
                a = a.replace(placeholder, str(val))
                b = b.replace(placeholder, str(val))
                c = c.replace(placeholder, str(val))
                d = d.replace(placeholder, str(val))
            preguntas.append(
                {
                    "Pregunta": p,
                    "A": a,
                    "B": b,
                    "C": c,
                    "D": d,
                    "Correcta": template["correcta"],
                    "Dificultad": template.get("dificultad", "Media"),
                    "Tipo": template.get("tipo", "Teoria"),
                }
            )
    else:
        preguntas.append(
            {
                "Pregunta": template["pregunta"],
                "A": template["A"],
                "B": template["B"],
                "C": template["C"],
                "D": template["D"],
                "Correcta": template["correcta"],
                "Dificultad": template.get("dificultad", "Media"),
                "Tipo": template.get("tipo", "Teoria"),
            }
        )

    return preguntas


def generar_reemplazo(
    tema: str,
    plantillas: dict[str, list[dict]],
    enunciados_existentes: set[str],
    bloques_existentes: set[tuple[str, str, str, str, str]],
) -> dict | None:
    templates = plantillas.get(tema, [])
    if not templates:
        return None

    orden = list(range(len(templates)))
    random.shuffle(orden)

    for idx in orden:
        for cand in expandir_plantilla(templates[idx]):
            enunciado_norm = normalizar_enunciado(cand["Pregunta"])
            bloque = (
                cand["Pregunta"].strip(),
                cand["A"].strip(),
                cand["B"].strip(),
                cand["C"].strip(),
                cand["D"].strip(),
            )
            if enunciado_norm in enunciados_existentes:
                continue
            if bloque in bloques_existentes:
                continue
            return cand
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inplace",
        action="store_true",
        help="Sobrescribe Data/Preguntas.csv (creando backup en Backups/).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="Data/Preguntas_sin_duplicados_enunciado.csv",
        help="Ruta de salida cuando no se usa --inplace.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria.")
    args = parser.parse_args()

    random.seed(args.seed)

    plantillas = cargar_plantillas()

    with PATH_PREGUNTAS.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)

    if not fieldnames:
        raise ValueError("No se encontraron columnas en Data/Preguntas.csv")

    enunciado_a_indices: dict[str, list[int]] = defaultdict(list)
    for idx, fila in enumerate(filas):
        enunciado_a_indices[normalizar_enunciado(fila.get("Pregunta", ""))].append(idx)

    indices_a_reemplazar = []
    for _, indices in enunciado_a_indices.items():
        if len(indices) > 1:
            indices_a_reemplazar.extend(indices[1:])

    if not indices_a_reemplazar:
        print("No hay duplicados por enunciado.")
        return

    enunciados_existentes = set()
    bloques_existentes = set()
    for idx, fila in enumerate(filas):
        if idx in indices_a_reemplazar:
            continue
        enunciados_existentes.add(normalizar_enunciado(fila.get("Pregunta", "")))
        bloques_existentes.add(
            (
                (fila.get("Pregunta") or "").strip(),
                (fila.get("A") or "").strip(),
                (fila.get("B") or "").strip(),
                (fila.get("C") or "").strip(),
                (fila.get("D") or "").strip(),
            )
        )

    reemplazadas = 0
    eliminadas = 0

    for idx in sorted(indices_a_reemplazar):
        fila = filas[idx]
        materia = (fila.get("Materia") or fila.get("Tema") or "").strip()
        reemplazo = generar_reemplazo(
            materia, plantillas, enunciados_existentes, bloques_existentes
        )
        if reemplazo:
            filas[idx] = {
                "Id": fila.get("Id", ""),
                "Pregunta": reemplazo["Pregunta"],
                "Materia": materia,
                "Dificultad": reemplazo["Dificultad"],
                "Tipo": reemplazo["Tipo"],
                "A": reemplazo["A"],
                "B": reemplazo["B"],
                "C": reemplazo["C"],
                "D": reemplazo["D"],
                "Correcta": reemplazo["Correcta"],
            }
            enunciados_existentes.add(normalizar_enunciado(reemplazo["Pregunta"]))
            bloques_existentes.add(
                (
                    reemplazo["Pregunta"].strip(),
                    reemplazo["A"].strip(),
                    reemplazo["B"].strip(),
                    reemplazo["C"].strip(),
                    reemplazo["D"].strip(),
                )
            )
            reemplazadas += 1
        else:
            filas[idx] = None
            eliminadas += 1

    filas = [f for f in filas if f is not None]
    filas = ordenar_filas_por_tema_y_id(filas)
    renumerar_ids(filas)

    output_path = PATH_PREGUNTAS if args.inplace else (BASE / args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.inplace:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"Preguntas_backup_dedup_enunciado_{stamp}.csv"
        shutil.copy2(PATH_PREGUNTAS, backup_path)
        print(f"Backup creado: {backup_path}")

    guardar_filas_csv(fieldnames, filas, output_path)

    print(f"Duplicados por enunciado detectados: {len(indices_a_reemplazar)}")
    print(f"  Reemplazados: {reemplazadas}")
    if eliminadas:
        print(f"  Eliminados sin reemplazo: {eliminadas}")
    print(f"Total final: {len(filas)}")
    print(f"Escrito en: {output_path}")


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
