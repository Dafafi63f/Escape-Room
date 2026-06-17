#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amplía Data/Preguntas.csv de 400 a 480 filas (40 × 12).

Estructura por materia: 2FT 2MT 2DT 2FC 2MC 2DC (orden canónico + ladder).
Rellena huecos desde plantillas.json (uso != dataset_480).

Uso:
  python Files/ampliar_dataset_480.py
  python Files/ampliar_dataset_480.py --sin-abcd   # no permutar ciclo A-D
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

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from balance_lib import LETRAS_ORDEN, permutar_abcd_objetivo
from objetivos_balanceo import PREGUNTAS_POR_MATERIA, SLOTS_CANONICOS_12, TARGET_TOTAL_PREGUNTAS
from utils_dataset_csv import COLUMNAS_PREGUNTAS, PATH_PREGUNTAS, fila_pregunta, guardar_filas_csv
from utils_orden_temas import cargar_orden_temas

BASE = Path(__file__).resolve().parent.parent.parent
PATH_PLANTILLAS = BASE / "Data" / "JSON" / "plantillas.json"


def clave_fila(r: dict) -> tuple:
    return (
        (r.get("Pregunta") or "").strip().lower(),
        (r.get("A") or "").strip().lower(),
        (r.get("B") or "").strip().lower(),
        (r.get("C") or "").strip().lower(),
        (r.get("D") or "").strip().lower(),
    )


def expandir_plantilla(template: dict) -> list[dict]:
    out: list[dict] = []
    variaciones = template.get("variaciones")
    if variaciones:
        for var in variaciones:
            p = template["pregunta"]
            a, b, c, d = template["A"], template["B"], template["C"], template["D"]
            for key, val in var.items():
                ph = "{" + str(key) + "}"
                p = p.replace(ph, str(val))
                a = a.replace(ph, str(val))
                b = b.replace(ph, str(val))
                c = c.replace(ph, str(val))
                d = d.replace(ph, str(val))
            out.append(
                {
                    "Pregunta": p,
                    "A": a,
                    "B": b,
                    "C": c,
                    "D": d,
                    "Correcta": template.get("correcta", "A"),
                    "Dificultad": template.get("dificultad", "Media"),
                    "Tipo": template.get("tipo", "Teoria"),
                }
            )
    else:
        out.append(
            {
                "Pregunta": template["pregunta"],
                "A": template["A"],
                "B": template["B"],
                "C": template["C"],
                "D": template["D"],
                "Correcta": template.get("correcta", "A"),
                "Dificultad": template.get("dificultad", "Media"),
                "Tipo": template.get("tipo", "Teoria"),
            }
        )
    return out


def cargar_plantillas_por_tema() -> dict[str, list[dict]]:
    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        raw = json.load(f)
    out: dict[str, list[dict]] = {}
    for tema, items in raw.items():
        pool: list[dict] = []
        for t in items:
            pool.extend(expandir_plantilla(t))
        if pool:
            out[tema] = pool
    return out


def fila_desde_origen(origen: dict, materia: str, tipo: str, dificultad: str) -> dict:
    return fila_pregunta(
        id_=0,
        materia=materia,
        dificultad=dificultad,
        tipo=tipo,
        pregunta=origen["Pregunta"],
        a=origen["A"],
        b=origen["B"],
        c=origen["C"],
        d=origen["D"],
        correcta=str(origen.get("Correcta", "A")).strip().upper(),
    )


def elegir_plantilla(
    pool: list[dict],
    tipo: str,
    dificultad: str,
    vistos: set[tuple],
    rng: random.Random,
) -> dict | None:
    candidatos = [
        p
        for p in pool
        if str(p.get("Tipo", "")).strip() == tipo and str(p.get("Dificultad", "")).strip() == dificultad
    ]
    rng.shuffle(candidatos)
    for p in candidatos:
        k = clave_fila(p)
        if k in vistos:
            continue
        vistos.add(k)
        return p
    candidatos_relaj = [p for p in pool if str(p.get("Tipo", "")).strip() == tipo]
    rng.shuffle(candidatos_relaj)
    for p in candidatos_relaj:
        k = clave_fila(p)
        if k in vistos:
            continue
        vistos.add(k)
        return p
    rng.shuffle(pool)
    for p in pool:
        k = clave_fila(p)
        if k in vistos:
            continue
        vistos.add(k)
        return p
    return None


def construir_bloque_12(
    materia: str,
    existentes: list[dict],
    plantillas_tema: list[dict],
    vistos: set[tuple],
    rng: random.Random,
) -> list[dict]:
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in existentes:
        buckets[(str(r["Tipo"]).strip(), str(r["Dificultad"]).strip())].append(dict(r))

    bloque: list[dict] = []
    for tipo, dificultad in SLOTS_CANONICOS_12:
        origen: dict | None = None
        key = (tipo, dificultad)
        if buckets[key]:
            origen = buckets[key].pop(0)
        else:
            origen = elegir_plantilla(plantillas_tema, tipo, dificultad, vistos, rng)
            if origen is None:
                raise RuntimeError(
                    f"{materia!r}: sin plantilla para {tipo}/{dificultad}"
                )
        vistos.add(clave_fila(origen))
        bloque.append(fila_desde_origen(origen, materia, tipo, dificultad))
    return bloque


def main() -> int:
    parser = argparse.ArgumentParser(description="Amplía el dataset a 480 preguntas (12 por materia).")
    parser.add_argument(
        "--sin-abcd",
        action="store_true",
        help="No aplicar permutación cíclica A-D según Id",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    temas, _ = cargar_orden_temas()
    plantillas = cargar_plantillas_por_tema()

    with PATH_PREGUNTAS.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    por_materia: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        por_materia[str(r["Materia"]).strip()].append(r)

    vistos: set[tuple] = {clave_fila(r) for r in rows}
    claves_csv = set(vistos)
    nuevas_filas: list[dict] = []
    desde_plantilla = 0

    for tema in temas:
        existentes = por_materia.get(tema, [])
        if len(existentes) > PREGUNTAS_POR_MATERIA:
            existentes = existentes[:PREGUNTAS_POR_MATERIA]
        pool_tpl = plantillas.get(tema, [])
        if not pool_tpl:
            raise SystemExit(f"Sin plantillas para {tema!r}")
        bloque = construir_bloque_12(tema, existentes, pool_tpl, vistos, rng)
        for fila in bloque:
            if clave_fila(fila) not in claves_csv:
                desde_plantilla += 1
        nuevas_filas.extend(bloque)

    if len(nuevas_filas) != TARGET_TOTAL_PREGUNTAS:
        raise SystemExit(f"Se generaron {len(nuevas_filas)} filas, objetivo {TARGET_TOTAL_PREGUNTAS}")

    for i, r in enumerate(nuevas_filas, start=1):
        r["Id"] = str(i)
        if not args.sin_abcd:
            nuevas_filas[i - 1] = permutar_abcd_objetivo(r, LETRAS_ORDEN[(i - 1) % 4])

    guardar_filas_csv(list(COLUMNAS_PREGUNTAS), nuevas_filas, PATH_PREGUNTAS)

    from balance_lib import ejecutar_ordenar_ladder

    ejecutar_ordenar_ladder()

    print(
        f"OK: {TARGET_TOTAL_PREGUNTAS} preguntas, "
        f"{PREGUNTAS_POR_MATERIA} por materia (2FT 2MT 2DT 2FC 2MC 2DC)"
    )
    print(f"  Desde plantillas (nuevas): {desde_plantilla}")
    print(f"  Reutilizadas del CSV anterior: {TARGET_TOTAL_PREGUNTAS - desde_plantilla}")
    return 0


if __name__ == "__main__":
    from utils_banco_cerrado import rechazar_script_deprecado

    rechazar_script_deprecado("ampliar_dataset_480.py")
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
