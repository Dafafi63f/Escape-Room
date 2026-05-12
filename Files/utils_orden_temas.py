#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidades compartidas para trabajar con el orden de temas definido en
Data/listado_materias.csv.
"""

from __future__ import annotations

import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
PATH_MATERIAS = BASE / "Data" / "listado_materias.csv"


def cargar_orden_temas(path_materias: Path | None = None) -> tuple[list[str], dict[str, int]]:
    """
    Devuelve:
    - lista ordenada de temas según listado_materias.csv
    - diccionario tema -> rank (0..N-1)
    """
    path = path_materias or PATH_MATERIAS
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        temas = [r["Materia"] for r in reader if r.get("Materia")]
    rank = {t: i for i, t in enumerate(temas)}
    return temas, rank


def key_orden_tema(tema_rank: dict[str, int], tema: str) -> int:
    """Clave segura para ordenar temas (desconocidos al final)."""
    return tema_rank.get(tema, len(tema_rank))
