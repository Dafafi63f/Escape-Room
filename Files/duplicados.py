#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto único de entrada para deduplicación de Preguntas.csv y plantillas.json.

Uso:
  python Files/duplicados.py revisar
  python Files/duplicados.py plantillas
  python Files/duplicados.py todo --dry-run
  python Files/duplicados.py todo --inplace
  python Files/duplicados.py exacto          # duplicados exactos A-D (balance agresivo)
  python Files/duplicados.py enunciado [--inplace]

Flujo recomendado: revisar → todo --inplace → balance.py conservador (Memoria_TFG.md §14.4).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

FILES = Path(__file__).resolve().parent
sys.path.insert(0, str(FILES))

from borrar_pycache import borrar_pycache_en_proyecto


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
            return ejecutar_exacto()
        if args.comando == "todo":
            if not args.inplace and not args.dry_run:
                print("Indica --inplace o --dry-run")
                return 2
            return ejecutar_todo(
                inplace=args.inplace,
                dry_run=args.dry_run,
                seed=args.seed,
            )
        if args.comando == "enunciado":
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
