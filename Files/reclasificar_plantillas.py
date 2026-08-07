#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audita y corrige la materia de plantillas en plantillas.json según el contenido.

  python Files/reclasificar_plantillas.py
  python Files/reclasificar_plantillas.py --solo-internet
  python Files/reclasificar_plantillas.py --aplicar
  python Files/reclasificar_plantillas.py --aplicar --solo-internet

Usa los mismos criterios que clasificar_pregunta.py (keywords en criterios_clasificacion_materia.csv).
No modifica entradas con uso dataset_480.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_FILES = Path(__file__).resolve().parent
if str(_FILES) not in sys.path:
    sys.path.insert(0, str(_FILES))

from utils_clasificacion_pregunta import comparar_con_asignacion, entrada_coherente_con_materia
from utils_dataset_csv import borrar_pycache_en_proyecto
from utils_orden_temas import cargar_orden_temas
from utils_plantillas_core import clave_contenido_sin_materia
from utils_plantillas_pool import es_uso_copia_dataset
from rutas_data import PATH_PLANTILLAS, ruta_escritura_proyecto


def _fila_desde_plantilla(materia: str, tpl: dict) -> dict:
    return {
        "Materia": materia,
        "Pregunta": tpl.get("pregunta", ""),
        "A": tpl.get("A", ""),
        "B": tpl.get("B", ""),
        "C": tpl.get("C", ""),
        "D": tpl.get("D", ""),
        "Correcta": tpl.get("correcta", "A"),
        "Tipo": tpl.get("tipo", ""),
        "Dificultad": tpl.get("dificultad", ""),
    }


def _clave_tpl(tpl: dict) -> tuple:
    return clave_contenido_sin_materia(
        tpl.get("pregunta", ""),
        {L: tpl.get(L, "") for L in "ABCD"},
        tpl.get("correcta", "A"),
    )


def _debe_reclasificar(
    materia: str,
    tpl: dict,
    *,
    min_score_materia: float,
    margen_materia: float,
) -> tuple[bool, str | None]:
    cmp = comparar_con_asignacion(
        _fila_desde_plantilla(materia, tpl),
        min_score_materia=min_score_materia,
        margen_materia=margen_materia,
    )
    if "Materia" not in cmp.campos_incoherentes:
        return False, None
    destino = cmp.inferido.materia
    if not destino or destino == materia:
        return False, None
    return True, destino


# Reexport para scripts que importan desde aquí.
__all__ = ["entrada_coherente_con_materia", "auditar_plantillas", "aplicar_reclasificacion"]


def _filtrar_uso(tpl: dict, solo_internet: bool, usos: frozenset[str] | None) -> bool:
    uso = str(tpl.get("uso", "")).strip().lower()
    if es_uso_copia_dataset(uso):
        return False
    if usos is not None:
        return uso in usos
    if solo_internet:
        return uso == "internet"
    return True


def auditar_plantillas(
    plantillas: dict,
    *,
    solo_internet: bool = False,
    usos: frozenset[str] | None = None,
    min_score_materia: float = 2.0,
    margen_materia: float = 2.0,
) -> list[dict]:
    hallazgos: list[dict] = []
    for materia, items in plantillas.items():
        for tpl in items:
            if not _filtrar_uso(tpl, solo_internet, usos):
                continue
            reclasificar, destino = _debe_reclasificar(
                materia,
                tpl,
                min_score_materia=min_score_materia,
                margen_materia=margen_materia,
            )
            if not reclasificar or destino is None:
                continue
            hallazgos.append(
                {
                    "materia_actual": materia,
                    "materia_destino": destino,
                    "uso": tpl.get("uso", ""),
                    "pregunta": tpl.get("pregunta", ""),
                    "clave": _clave_tpl(tpl),
                }
            )
    return hallazgos


def aplicar_reclasificacion(
    plantillas: dict,
    hallazgos: list[dict],
) -> tuple[dict, dict[str, int]]:
    claves_por_materia: dict[str, set[tuple]] = {}
    for materia, items in plantillas.items():
        claves_por_materia[materia] = {_clave_tpl(t) for t in items}

    a_mover: list[tuple[str, dict, str]] = []
    a_eliminar: list[tuple[str, tuple]] = []
    stats = {"movidas": 0, "eliminadas_dup": 0, "sin_cambio": 0}

    for h in hallazgos:
        origen = h["materia_actual"]
        destino = h["materia_destino"]
        clave = h["clave"]
        tpl = None
        for t in plantillas.get(origen, []):
            if _clave_tpl(t) == clave:
                tpl = t
                break
        if tpl is None:
            stats["sin_cambio"] += 1
            continue
        if clave in claves_por_materia.get(destino, set()):
            a_eliminar.append((origen, clave))
            stats["eliminadas_dup"] += 1
        else:
            a_mover.append((origen, tpl, destino))
            claves_por_materia.setdefault(destino, set()).add(clave)
            stats["movidas"] += 1

    eliminar_set = {(o, c) for o, c in a_eliminar}
    mover_claves_origen = {(o, _clave_tpl(t)) for o, t, _ in a_mover}

    nueva: dict[str, list] = {}
    for materia, items in plantillas.items():
        kept = []
        for t in items:
            clave = _clave_tpl(t)
            if (materia, clave) in eliminar_set:
                continue
            if (materia, clave) in mover_claves_origen:
                continue
            kept.append(t)
        nueva[materia] = kept

    for origen, tpl, destino in a_mover:
        nueva.setdefault(destino, []).append(dict(tpl))

    return nueva, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Reclasificar materia de plantillas por contenido")
    parser.add_argument("--aplicar", action="store_true", help="Escribe plantillas.json")
    parser.add_argument("--solo-internet", action="store_true")
    parser.add_argument("--uso", action="append", help="Filtrar por uso (repuesto, internet, …)")
    parser.add_argument("--min-score", type=float, default=2.0)
    parser.add_argument("--margen", type=float, default=2.0)
    parser.add_argument("--json", type=str, default="", help="Informe JSON de hallazgos")
    args = parser.parse_args()

    usos = frozenset(u.strip().lower() for u in args.uso) if args.uso else None

    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plantillas = json.load(f)

    hallazgos = auditar_plantillas(
        plantillas,
        solo_internet=args.solo_internet,
        usos=usos,
        min_score_materia=args.min_score,
        margen_materia=args.margen,
    )

    por_par: dict[tuple[str, str], int] = {}
    for h in hallazgos:
        par = (h["materia_actual"], h["materia_destino"])
        por_par[par] = por_par.get(par, 0) + 1

    print(f"Hallazgos: {len(hallazgos)} plantillas a reclasificar")
    if por_par:
        print("Por (origen → destino):")
        for (o, d), n in sorted(por_par.items(), key=lambda x: (-x[1], x[0][0])):
            print(f"  {o} → {d}: {n}")

    for h in hallazgos[:20]:
        pre = h["pregunta"][:75].encode("utf-8", errors="replace").decode("utf-8")
        print(f"  [{h['uso']}] {h['materia_actual']} → {h['materia_destino']}: {pre}")
    if len(hallazgos) > 20:
        print(f"  … y {len(hallazgos) - 20} más")

    if args.json:
        destino = ruta_escritura_proyecto(args.json)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps(hallazgos, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Informe: {destino}")

    if not args.aplicar:
        if hallazgos:
            print("\nDry-run. Aplica con: python Files/reclasificar_plantillas.py --aplicar")
        return

    nueva, stats = aplicar_reclasificacion(plantillas, hallazgos)
    orden, _rank = cargar_orden_temas()
    ordenados = {t: nueva.get(t, []) for t in orden if t in nueva}
    for t in nueva:
        if t not in ordenados:
            ordenados[t] = nueva[t]

    from utils_banco_cerrado import guardar_plantillas_json

    guardar_plantillas_json(ordenados)

    print(f"\nGuardado: {PATH_PLANTILLAS}")
    print(f"Movidas: {stats['movidas']} | Duplicados eliminados: {stats['eliminadas_dup']}")
    borrar_pycache_en_proyecto()


if __name__ == "__main__":
    main()
