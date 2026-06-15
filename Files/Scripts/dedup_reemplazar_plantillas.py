#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dedup de plantillas.json, elimina variantes sintéticas duplicadas y reinyecta
preguntas del catálogo internet/repuesto por materia.

  python Files/Scripts/dedup_reemplazar_plantillas.py --dry-run
  python Files/Scripts/dedup_reemplazar_plantillas.py --inplace
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import argparse
import json

from catalogo_internet_plantillas import fusionar_con_repuesto  # noqa: E402
from equilibrar_pool_extra_juego import PATH_PLANTILLAS, claves_dataset_csv  # noqa: E402
from utils_plantillas_core import clave_contenido  # noqa: E402
from utils_dataset_csv import borrar_pycache_en_proyecto  # noqa: E402
from utils_deduplicacion import deduplicar_plantillas_dict  # noqa: E402
from utils_orden_temas import cargar_orden_temas  # noqa: E402

_USO_PURGA = frozenset(
    {"ampliado_perm", "ampliado_num", "ampliado_var", "pool_extra"}
)


def purgar_sinteticas(plantillas: dict) -> tuple[dict, int]:
    nueva: dict = {}
    eliminadas = 0
    for tema, items in plantillas.items():
        kept = []
        for t in items:
            if str(t.get("uso", "")).lower() in _USO_PURGA:
                eliminadas += 1
            else:
                kept.append(t)
        nueva[tema] = kept
    return nueva, eliminadas


def inyectar_catalogo(
    plantillas: dict, claves_ds: set[tuple], temas: list[str]
) -> tuple[dict, int]:
    anadidas = 0
    for tema in temas:
        items = plantillas.setdefault(tema, [])
        vistos: set[tuple] = set(claves_ds)
        for t in items:
            k = clave_contenido(
                tema,
                t.get("pregunta", ""),
                {L: t.get(L, "") for L in "ABCD"},
                t.get("correcta", ""),
            )
            vistos.add(k)
        for entrada in fusionar_con_repuesto(tema):
            uso = str(entrada.get("uso", "internet")).lower()
            if uso == "internet":
                tpl = dict(entrada)
            else:
                tpl = {**entrada, "uso": "repuesto"}
            k = clave_contenido(
                tema,
                tpl["pregunta"],
                {L: tpl[L] for L in "ABCD"},
                tpl["correcta"],
            )
            if k in vistos:
                continue
            items.append(tpl)
            vistos.add(k)
            anadidas += 1
    return plantillas, anadidas


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dedup plantillas + purga sintéticas + catálogo internet"
    )
    parser.add_argument("--inplace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.inplace and not args.dry_run:
        print("Indica --inplace o --dry-run")
        return 2

    temas, _ = cargar_orden_temas()
    claves_ds = claves_dataset_csv()

    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plantillas = json.load(f)

    total0 = sum(len(v) for v in plantillas.values())
    plantillas, n_purga = purgar_sinteticas(plantillas)
    print(f"Purgadas sintéticas (perm/num/var/pool_extra): {n_purga}")

    plantillas, exact_r, similar_r = deduplicar_plantillas_dict(plantillas)
    print(f"Dedup: exactas={exact_r} similares={similar_r}")

    plantillas, n_inj = inyectar_catalogo(plantillas, claves_ds, temas)
    print(f"Inyectadas desde catálogo (nuevas claves): {n_inj}")

    total1 = sum(len(v) for v in plantillas.values())
    print(f"Total entradas: {total0} -> {total1}")

    if args.dry_run:
        print("(dry-run: no se guardó)")
        return 0

    with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
        json.dump(plantillas, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Guardado: {PATH_PLANTILLAS}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        borrar_pycache_en_proyecto()
