#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidades compartidas para leer/escribir y ordenar filas del dataset CSV.
"""

from __future__ import annotations

import csv
from pathlib import Path
from utils_orden_temas import cargar_orden_temas, key_orden_tema


BASE = Path(__file__).resolve().parent.parent
PATH_PREGUNTAS = BASE / "Data" / "Preguntas.csv"

# Cabecera canónica de Data/Preguntas.csv (orden fijo al guardar).
COLUMNAS_PREGUNTAS: tuple[str, ...] = (
    "Id",
    "Pregunta",
    "Materia",
    "Dificultad",
    "Tipo",
    "A",
    "B",
    "C",
    "D",
    "Correcta",
)


def materia_de_fila(fila: dict) -> str:
    """Nombre de materia: columna oficial `Materia`, con compatibilidad `Tema` antigua."""
    m = fila.get("Materia")
    if m is not None and str(m).strip():
        return str(m).strip()
    t = fila.get("Tema")
    return (str(t).strip() if t is not None else "")


def cargar_filas_csv(path_csv: Path | None = None) -> tuple[list[str], list[dict]]:
    """Carga un CSV ';' y devuelve (fieldnames, filas)."""
    path = path_csv or PATH_PREGUNTAS
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)
    for row in filas:
        if not (row.get("Materia") or "").strip() and (row.get("Tema") or "").strip():
            row["Materia"] = str(row["Tema"]).strip()
    return fieldnames, filas


def guardar_filas_csv(
    fieldnames: list[str] | None, filas: list[dict], path_csv: Path | None = None
) -> None:
    """
    Guarda filas en CSV ';' con UTF-8.
    Fuerza columnas base en COLUMNAS_PREGUNTAS y el orden de cabecera;
    añade al final columnas extra presentes en las filas (p. ej. Tematica).
    El primer argumento se conserva por compatibilidad con scripts antiguos y no determina el orden.
    """
    _ = fieldnames
    path = path_csv or PATH_PREGUNTAS
    extras_keys: set[str] = set()
    for f in filas:
        for k in f:
            if k not in COLUMNAS_PREGUNTAS and k != "Tema":
                extras_keys.add(k)
    extras = sorted(extras_keys)
    out_fn = list(COLUMNAS_PREGUNTAS) + extras
    out_rows: list[dict] = []
    for f in filas:
        row: dict[str, str] = {}
        for c in COLUMNAS_PREGUNTAS:
            if c == "Materia":
                row[c] = materia_de_fila(f)
            else:
                v = f.get(c, "")
                row[c] = "" if v is None else str(v)
        for e in extras:
            v = f.get(e, "")
            row[e] = "" if v is None else str(v)
        out_rows.append(row)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=out_fn, delimiter=";")
        writer.writeheader()
        writer.writerows(out_rows)


def ordenar_filas_por_tema_y_id(filas: list[dict]) -> list[dict]:
    """Ordena filas por materia (listado_materias) y luego por Id."""
    _, tema_rank = cargar_orden_temas()
    return sorted(
        filas,
        key=lambda r: (key_orden_tema(tema_rank, materia_de_fila(r)), int(r["Id"])),
    )


def renumerar_ids(filas: list[dict], start: int = 1) -> None:
    """Renumera la columna Id en el orden actual de la lista."""
    for i, fila in enumerate(filas, start=start):
        fila["Id"] = str(i)
