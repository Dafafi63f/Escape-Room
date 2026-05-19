#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mantiene Data/criterios_clasificacion_materia.csv.

  python Files/exportar_criterios_clasificacion_materia.py
      Relee Palabras_clave y actualiza columnas derivadas.

  python Files/exportar_criterios_clasificacion_materia.py --corregir-ids-permutados
      Corrige Palabras_clave en ids 11-20 (exportación previa desalineada con listado).

Tras editar el CSV: ejecutar este script; en código: recargar_criterios().
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from borrar_pycache import borrar_pycache_en_proyecto
from utils_puntuacion_materia import MATERIAS, recargar_criterios, SEP_KEYWORDS

BASE = Path(__file__).resolve().parent.parent
PATH_LISTADO = BASE / "Data" / "listado_materias.csv"
PATH_OUT = BASE / "Data" / "criterios_clasificacion_materia.csv"

CRITERIO_RESUMEN = (
    "Puntuación = nº de Palabras_clave presentes como subcadena en "
    "Pregunta+A+B+C+D (texto normalizado: minúsculas, sin acentos). "
    "No asigna Materia automáticamente; sirve para priorizar eliminaciones e intercambios. "
    "Fuente editable: Data/criterios_clasificacion_materia.csv."
)

# Palabras_clave que estaban bajo otro Id en el dict Python histórico
_CORREGIR_DESDE_ID: dict[int, int] = {
    11: 14,
    12: 17,
    13: 12,
    14: 13,
    15: 11,
    16: 20,
    17: 19,
    19: 15,
    20: 16,
}

# Permutación histórica en ids 26-30 (BDD NoSQL↔Distribuïts, IQ↔ModSim↔Xarxes)
_CORREGIR_CICLO_26_30: dict[int, int] = {
    26: 29,
    29: 26,
    27: 28,
    28: 30,
    30: 27,
}

NOTAS_POR_ID: dict[int, str] = {
    3: "Comparte «entropía» con Teoria de la Informació y «cuello de botella» con HPC.",
    5: "«kernel» también puntúa en Àlgebra y Visió; en SO suele ir con proceso/thread.",
    7: "Comparte «gradiente» con Optimització i Càlcul DV.",
    11: "SQL/ACID; «consistencia» también en BDD No Relacionals.",
    15: "Geometría 3D; puede solapar con Àlgebra (volúmenes) o TDA.",
    16: "Fourier/complejos; «convolución» también en Xarxes/Visió.",
    18: "«clasificación/regresión» también en Aprenentatge i Xarxes Neuronals.",
    19: "Monte Carlo / simulación; solapa amb Modelització i Simulació.",
    24: "Física, química, biología; solapa amb Astrofísica i Bioinformàtica.",
    27: "Comparte convolución/stride/pooling con Visió per Computador.",
    28: "Solapa Monte Carlo amb Mètodes Numèrics Probabilístics.",
    35: "Comparte IC 95, odds ratio, sensibilidad amb Modelització i Inferència.",
    40: "Comparte convolución, kernel, stride amb Xarxes Neuronals.",
}


def _parse_keywords(celda: str) -> list[str]:
    return [p.strip() for p in (celda or "").split("|") if p.strip()]


def _cargar_tematica() -> dict[int, str]:
    out: dict[int, str] = {}
    with PATH_LISTADO.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            out[int(row["Id"])] = row.get("Tematica", "")
    return out


def leer_keywords_csv() -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    with PATH_OUT.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            out[int(row["Id"])] = _parse_keywords(row.get("Palabras_clave", ""))
    return out


def corregir_permutacion(kws: dict[int, list[str]]) -> dict[int, list[str]]:
    actual = dict(kws)
    for dest, src in _CORREGIR_DESDE_ID.items():
        actual[dest] = list(kws[src])
    for dest, src in _CORREGIR_CICLO_26_30.items():
        actual[dest] = list(kws[src])
    return actual


def _indice_palabra(kws_por_id: dict[int, list[str]]) -> dict[str, list[int]]:
    inv: dict[str, list[int]] = defaultdict(list)
    for mid, kws in kws_por_id.items():
        for kw in kws:
            inv[kw.lower().strip()].append(mid)
    return inv


def _solapamientos(mid: int, kws: list[str], inv: dict[str, list[int]]) -> tuple[str, str]:
    compartidas: set[str] = set()
    otras: set[int] = set()
    for kw in kws:
        ids = [i for i in inv.get(kw.lower().strip(), []) if i != mid]
        if ids:
            compartidas.add(kw)
            otras.update(ids)
    return SEP_KEYWORDS.join(sorted(compartidas, key=str.lower)), SEP_KEYWORDS.join(
        MATERIAS[i] for i in sorted(otras)
    )


def escribir_csv(kws_por_id: dict[int, list[str]]) -> None:
    tematica = _cargar_tematica()
    inv = _indice_palabra(kws_por_id)
    fieldnames = [
        "Id",
        "Materia",
        "Tematica",
        "N_palabras_clave",
        "Palabras_clave",
        "Criterio_puntuacion_resumen",
        "Palabras_clave_compartidas",
        "Otras_materias_con_esas_palabras",
        "Notas_desambiguacion",
    ]
    rows_out: list[dict[str, str]] = []
    for mid in sorted(MATERIAS):
        kws = kws_por_id.get(mid, [])
        kw_comp, mats_comp = _solapamientos(mid, kws, inv)
        rows_out.append(
            {
                "Id": str(mid),
                "Materia": MATERIAS[mid],
                "Tematica": tematica.get(mid, ""),
                "N_palabras_clave": str(len(kws)),
                "Palabras_clave": SEP_KEYWORDS.join(kws),
                "Criterio_puntuacion_resumen": CRITERIO_RESUMEN,
                "Palabras_clave_compartidas": kw_comp,
                "Otras_materias_con_esas_palabras": mats_comp,
                "Notas_desambiguacion": NOTAS_POR_ID.get(mid, ""),
            }
        )
    with PATH_OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(rows_out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corregir-ids-permutados",
        action="store_true",
        help="Reasigna Palabras_clave de ids 11-20 según permutación histórica",
    )
    args = parser.parse_args()

    kws = leer_keywords_csv()
    if args.corregir_ids_permutados:
        kws = corregir_permutacion(kws)

    escribir_csv(kws)
    recargar_criterios()
    print(f"Actualizado: criterios_clasificacion_materia.csv ({len(kws)} materias)")


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
