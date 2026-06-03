#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEGACY — deshabilitado (banco cerrado 2026-06-03). No ejecutar.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from balance_lib import ejecutar_reordenar, ejecutar_validar
from utils_dataset_csv import guardar_filas_csv

PATH = Path(__file__).resolve().parent.parent.parent / "Data" / "Preguntas.csv"

from utils_banco_cerrado import rechazar_mutacion_dataset

rechazar_mutacion_dataset("limpiar_duplicados_csv.py (legacy)")

with PATH.open(encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter=";")
    fields = list(reader.fieldnames or [])
    rows = list(reader)

rows = [r for r in rows if "(variante" not in (r.get("Pregunta") or "").lower()]

out: list[dict] = []
seen: set[tuple[str, str]] = set()
for r in rows:
    key = (r.get("Materia") or "", (r.get("Pregunta") or "").strip())
    if key in seen:
        continue
    seen.add(key)
    out.append(r)

if len(out) != 480:
    print(
        f"AVISO: tras deduplicar quedan {len(out)} filas (esperadas 480). "
        "Ejecuta fix_final_materias.py antes de reordenar.",
        file=sys.stderr,
    )
    raise SystemExit(1)

for i, r in enumerate(out, start=1):
    r["Id"] = str(i)

guardar_filas_csv(fields, out, PATH)
ejecutar_reordenar(solo_metadatos=True, sin_permutar_respuestas=True)
raise SystemExit(ejecutar_validar(detalle=False, estricto=False))
