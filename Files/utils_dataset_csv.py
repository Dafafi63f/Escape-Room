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


def cargar_filas_csv(path_csv: Path | None = None) -> tuple[list[str], list[dict]]:
    """Carga un CSV ';' y devuelve (fieldnames, filas)."""
    path = path_csv or PATH_PREGUNTAS
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)
    return fieldnames, filas


def guardar_filas_csv(
    fieldnames: list[str], filas: list[dict], path_csv: Path | None = None
) -> None:
    """Guarda filas en CSV ';' con UTF-8."""
    path = path_csv or PATH_PREGUNTAS
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(filas)


def ordenar_filas_por_tema_y_id(filas: list[dict]) -> list[dict]:
    """Ordena filas por tema (listado_materias) y luego por Id."""
    _, tema_rank = cargar_orden_temas()
    return sorted(
        filas, key=lambda r: (key_orden_tema(tema_rank, r["Tema"]), int(r["Id"]))
    )


def renumerar_ids(filas: list[dict], start: int = 1) -> None:
    """Renumera la columna Id en el orden actual de la lista."""
    for i, fila in enumerate(filas, start=start):
        fila["Id"] = str(i)
