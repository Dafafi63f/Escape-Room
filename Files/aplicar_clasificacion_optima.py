#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revisa todas las preguntas y ajusta Materia + Tipo + Dificultad a la combinación óptima
inferida del enunciado (clasificar_pregunta).

Estrategia:
- Materia o Tipo incoherentes con el texto → sustituir fila (regenerar desde plantillas
  del hueco de materia, con tipo/dificultad inferidos).
- Dificultad: solo si el contraste es fuerte (Facil↔Dificil); la escalera F/M/D del bloque
  la corrige `balance.py reordenar`.
- No se reetiqueta el mismo enunciado.

Uso:
  python Files/aplicar_clasificacion_optima.py --dry-run
  python Files/aplicar_clasificacion_optima.py --inplace

Ver Memoria_TFG.md §14.4 (tras duplicados.py, antes de balance.py conservador).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from balance_lib import ejecutar_reordenar, ejecutar_validar
from dataset_pipeline import (
    ejecutar_balancear_materias,
    ejecutar_balancear_tipo_dificultad,
    sustituir_filas_incoherentes,
)
from objetivos_balanceo import TARGET_TOTAL_PREGUNTAS
from utils_clasificacion_pregunta import comparar_con_asignacion, metadatos_optimos
from utils_dataset_csv import guardar_filas_csv, materia_de_fila

PATH_CSV = BASE / "Data" / "Preguntas.csv"


def _requiere_sustitucion(cmp) -> bool:
    if "Materia" in cmp.campos_incoherentes or "Tipo" in cmp.campos_incoherentes:
        return True
    return "Dificultad" in cmp.campos_incoherentes


def aplicar(inplace: bool, dry_run: bool, sin_reordenar: bool) -> int:
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)

    sustituir: list[dict] = []
    for row in filas:
        cmp = comparar_con_asignacion(row, estricto=False)
        if not _requiere_sustitucion(cmp):
            continue
        opt = metadatos_optimos(row)
        sustituir.append(
            {
                "id": row["Id"],
                "materia": materia_de_fila(row),
                "campos": cmp.campos_incoherentes,
                "asignado": cmp.asignado,
                "optimo": opt,
                "inferido": cmp.inferido,
                "pregunta": cmp.inferido.pregunta[:90],
            }
        )

    print(f"=== Revisión ({len(filas)} filas) ===")
    print(f"  Sustituir (contenido vs metadatos): {len(sustituir)}")
    for c in sustituir[:45]:
        a, o = c["asignado"], c["optimo"]
        pre = c["pregunta"].encode("utf-8", errors="replace").decode("utf-8")
        print(
            f"  Id {c['id']}: [{', '.join(c['campos'])}] "
            f"M={a['Materia']!r} T={a['Tipo']} D={a['Dificultad']} -> "
            f"M={o['Materia']!r} T={o['Tipo']} D={o['Dificultad']} | {pre}"
        )
    if len(sustituir) > 45:
        print(f"  ... y {len(sustituir) - 45} más")

    if dry_run or not inplace:
        if not inplace:
            print("\n(dry-run: use --inplace para aplicar)")
        return 0

    filas, n_gen, _ = sustituir_filas_incoherentes(filas, sustituir)
    print(f"\nRegeneradas: {n_gen} / {len(sustituir)} solicitadas")

    if len(filas) != TARGET_TOTAL_PREGUNTAS:
        print(f"  Total {len(filas)} != {TARGET_TOTAL_PREGUNTAS}; rellenando materias…")
        ejecutar_balancear_materias()
        with PATH_CSV.open(encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f, delimiter=";"))

    guardar_filas_csv(fieldnames, filas, PATH_CSV)
    print("Guardado:", PATH_CSV, f"({len(filas)} filas)")

    print("\n>>> Ajustar tipo/dificultad por materia (5+5)")
    ejecutar_balancear_tipo_dificultad()

    if not sin_reordenar:
        print("\n>>> Reordenar (escalera canónica tipo/dificultad)")
        if ejecutar_reordenar(solo_metadatos=True, sin_permutar_respuestas=True) != 0:
            return 1

    print("\n>>> Validar")
    return ejecutar_validar(detalle=False, estricto=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inplace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sin-reordenar", action="store_true")
    args = parser.parse_args()
    if not args.inplace and not args.dry_run:
        args.dry_run = True
    return aplicar(args.inplace, args.dry_run, args.sin_reordenar)


if __name__ == "__main__":
    raise SystemExit(main())
