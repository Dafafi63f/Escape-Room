#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Borra de forma recursiva todas las carpetas __pycache__ del proyecto.

Uso:
  python Files/borrar_pycache.py
  python Files/borrar_pycache.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "Files"))

from utils_dataset_csv import borrar_pycache_en_proyecto  # noqa: E402


def _encontrar_pycache(base: Path) -> list[Path]:
    return [p for p in base.rglob("__pycache__") if p.is_dir()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Borra carpetas __pycache__ del proyecto")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo lista carpetas, sin borrar.",
    )
    args = parser.parse_args()

    carpetas = _encontrar_pycache(BASE)
    if not carpetas:
        print("No se encontraron carpetas __pycache__.")
        return 0

    print(f"Encontradas {len(carpetas)} carpetas __pycache__.")
    for p in carpetas:
        print(f" - {p}")

    if args.dry_run:
        print("\nDry-run: no se ha borrado nada.")
        return 0

    borradas, errores = borrar_pycache_en_proyecto(BASE)
    print("\nResultado:")
    print(f" - Borradas: {borradas}")
    print(f" - Errores: {errores}")
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
