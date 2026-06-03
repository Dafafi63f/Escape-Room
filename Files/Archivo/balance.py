#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validación del banco cerrado Data/Preguntas.csv (480 filas, 40 materias × 12).

Uso:
  python Files/balance.py validar [--detalle] [--estricto]

Los comandos de regeneración (conservador, agresivo, ajustar, reordenar, …)
están deshabilitados desde 2026-06-03. Ver Memoria_TFG.md §14.4.

Clasificación por contenido (solo lectura):
  python Files/clasificar_pregunta.py --dataset --solo-incoherentes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

FILES = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(FILES))

from utils_banco_cerrado import mensaje_comando_balance_bloqueado
from utils_dataset_csv import borrar_pycache_en_proyecto

_COMANDOS_BLOQUEADOS = frozenset(
    {
        "ajustar",
        "reordenar",
        "ordenar-ladder",
        "corregir",
        "conservador",
        "agresivo",
    }
)


def cmd_validar(args: argparse.Namespace) -> int:
    from balance_lib import ejecutar_validar

    return ejecutar_validar(detalle=args.detalle, estricto=args.estricto)


def cmd_bloqueado(comando: str) -> int:
    print(mensaje_comando_balance_bloqueado(comando))
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validación del dataset Preguntas.csv (banco cerrado, 480 preguntas).",
        epilog="Mantenimiento: Memoria_TFG.md §14.4",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_val = sub.add_parser("validar", help="Comprueba balance sin modificar el CSV")
    p_val.add_argument("--detalle", action="store_true")
    p_val.add_argument("--estricto", action="store_true")
    p_val.set_defaults(func=cmd_validar)

    # Subcomandos legacy: mensaje claro en lugar de argparse error
    for nombre in sorted(_COMANDOS_BLOQUEADOS):
        p = sub.add_parser(
            nombre,
            help=argparse.SUPPRESS,
            description=argparse.SUPPRESS,
        )
        p.set_defaults(func=lambda a, c=nombre: cmd_bloqueado(c))

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    finally:
        borrar_pycache_en_proyecto()


if __name__ == "__main__":
    raise SystemExit(main())
