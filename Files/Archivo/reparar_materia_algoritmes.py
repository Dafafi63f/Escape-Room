#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reubica preguntas según reglas del proyecto (movimientos puntuales por Id).

**Supersedido** para el mantenimiento habitual por ``fix_final_materias.py``.
Solo útil si hace falta repetir un movimiento concreto vía ``recategorizar_y_equilibrar``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_FILES = Path(__file__).resolve().parent.parent
_SCRIPTS = _FILES / "Scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_FILES) not in sys.path:
    sys.path.insert(0, str(_FILES))

import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Scripts"))

from recategorizar_y_equilibrar import recategorizar_y_equilibrar_por_id

PATH = BASE / "Data" / "CSV" / "Preguntas.csv"
DEST_ALG = "Tècniques de Disseny d'Algoritmes"
PROG = "Programari de Sistema"
FON = "Fonaments de Computadors"
INI = "Iniciació a la Programació"
POO = "Programació Orientada als Objectes"

# (materia_origen, fragmento_pregunta, materia_destino)
MOVES = [
    (INI, "valores puede representar 1 bit", FON),
    (INI, "comando crea un archivo vac", PROG),
    (INI, "comando sube un nivel", PROG),
    (INI, "operador de tubería", PROG),
    (INI, "redirección en la terminal", PROG),
    (INI, "estructura usa lifo", DEST_ALG),
    (INI, "qué es un algoritmo", DEST_ALG),
    (POO, "complejidad de fibonacci", DEST_ALG),
    (POO, "lista no ordenada", DEST_ALG),
    (POO, "complejidad de búsqueda binaria", DEST_ALG),
]


def _find_id(materia: str, fragment: str) -> str | None:
    with PATH.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r.get("Materia") != materia:
                continue
            if fragment.lower() in (r.get("Pregunta") or "").lower():
                return r["Id"]
    return None


def _limpiar_variantes() -> None:
    from utils_dataset_csv import guardar_filas_csv

    with PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fields = list(reader.fieldnames or [])
        rows = [r for r in reader if "(variante" not in (r.get("Pregunta") or "").lower()]
    for r in rows:
        if r.get("Materia") == INI and (r.get("Pregunta") or "").startswith("¿Qué es un array"):
            r["Dificultad"] = "Facil"
            r["Tipo"] = "Teoria"
    for i, r in enumerate(rows, start=1):
        r["Id"] = str(i)
    guardar_filas_csv(fields, rows, PATH)


def main() -> int:
    _limpiar_variantes()
    for origen, frag, destino in MOVES:
        rid = _find_id(origen, frag)
        if not rid:
            print(f"OMITIDO (ya movida o no encontrada): {frag!r} [{origen}]")
            continue
        print(f"\n>>> Id {rid}: {origen} -> {destino} ({frag[:50]}...)")
        rc = recategorizar_y_equilibrar_por_id(rid, destino, inplace=True)
        if rc:
            return rc
    print("\nTodas las reubicaciones aplicadas.")
    return 0


if __name__ == "__main__":
    from utils_banco_cerrado import rechazar_script_deprecado

    rechazar_script_deprecado("reparar_materia_algoritmes.py")
    raise SystemExit(main())
