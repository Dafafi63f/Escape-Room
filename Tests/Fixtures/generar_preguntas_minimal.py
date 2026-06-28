#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera ``Tests/Fixtures/Preguntas_minimal.csv`` desde ``Data/Banco/Preguntas.csv`` (solo columnas mínimas)."""

from __future__ import annotations

import csv
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
_ORIGEN = _RAIZ / "Data" / "Banco" / "Preguntas.csv"
_DESTINO = Path(__file__).resolve().parent / "Preguntas_minimal.csv"
_COLUMNAS = ("Id", "Pregunta", "A", "B", "C", "D", "Correcta")


def generar_preguntas_minimal(
    origen: Path = _ORIGEN,
    destino: Path = _DESTINO,
) -> int:
    if not origen.is_file():
        raise FileNotFoundError(f"No se encontró el banco: {origen}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    filas = 0
    with origen.open("r", encoding="utf-8", newline="") as f_in, destino.open(
        "w", encoding="utf-8", newline=""
    ) as f_out:
        reader = csv.DictReader(f_in, delimiter=";")
        writer = csv.DictWriter(
            f_out,
            fieldnames=list(_COLUMNAS),
            delimiter=";",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in reader:
            writer.writerow({col: row[col] for col in _COLUMNAS})
            filas += 1
    return filas


if __name__ == "__main__":
    n = generar_preguntas_minimal()
    print(f"Escrito {_DESTINO.name}: {n} preguntas")
