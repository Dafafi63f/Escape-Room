#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deduplicación de plantillas y revisión del banco cerrado.

Uso seguro:
  python Files/Scripts/duplicados.py revisar
  python Files/Scripts/duplicados.py plantillas

Bloqueado (modifica Preguntas.csv): todo --inplace, enunciado --inplace, exacto.
Ver Files/Scripts/README.md y Memoria_TFG.md §5.4
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import argparse
import sys
from pathlib import Path

from utils_dataset_csv import borrar_pycache_en_proyecto


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicación de Data/Preguntas.csv y Data/plantillas.json."
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("revisar", help="Informe de duplicados/similitudes (sin modificar archivos)")
    sub.add_parser("plantillas", help="Deduplica solo plantillas.json")
    sub.add_parser("exacto", help="Reemplaza duplicados exactos (mismo enunciado y opciones)")

    p_todo = sub.add_parser(
        "todo",
        help="Deduplica plantillas + dataset (criterios unificados); flujo recomendado",
    )
    p_todo.add_argument("--inplace", action="store_true", help="Escribe los archivos")
    p_todo.add_argument("--dry-run", action="store_true", help="Solo informa cambios")
    p_todo.add_argument("--seed", type=int, default=42)

    p_en = sub.add_parser("enunciado", help="Duplicados solo por texto de Pregunta")
    p_en.add_argument("--inplace", action="store_true", help="Sobrescribe Preguntas.csv")
    p_en.add_argument(
        "--output",
        type=str,
        default="Data/Preguntas_sin_duplicados_enunciado.csv",
        help="Salida si no se usa --inplace",
    )
    p_en.add_argument("--seed", type=int, default=42)

    args = parser.parse_args(argv)

    from duplicados_lib import (
        ejecutar_enunciado,
        ejecutar_exacto,
        ejecutar_plantillas,
        ejecutar_revisar,
        ejecutar_todo,
    )

    try:
        if args.comando == "revisar":
            return ejecutar_revisar()
        if args.comando == "plantillas":
            return ejecutar_plantillas()
        if args.comando == "exacto":
            from utils_banco_cerrado import rechazar_mutacion_dataset

            rechazar_mutacion_dataset("duplicados.py exacto")
        if args.comando == "todo":
            from utils_banco_cerrado import rechazar_mutacion_dataset

            if args.inplace:
                rechazar_mutacion_dataset("duplicados.py todo --inplace")
            if not args.inplace and not args.dry_run:
                print("Indica --inplace o --dry-run")
                return 2
            return ejecutar_todo(
                inplace=args.inplace,
                dry_run=args.dry_run,
                seed=args.seed,
            )
        if args.comando == "enunciado":
            from utils_banco_cerrado import rechazar_mutacion_dataset

            if args.inplace:
                rechazar_mutacion_dataset("duplicados.py enunciado --inplace")
            return ejecutar_enunciado(
                inplace=args.inplace,
                output=args.output,
                seed=args.seed,
            )
        return 2
    finally:
        borrar_pycache_en_proyecto()


if __name__ == "__main__":
    raise SystemExit(main())
