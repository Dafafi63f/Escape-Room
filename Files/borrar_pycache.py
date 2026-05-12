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
import shutil
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent


def encontrar_pycache(base: Path) -> list[Path]:
    return [p for p in base.rglob("__pycache__") if p.is_dir()]


def borrar_pycache_en_proyecto(base: Path | None = None) -> tuple[int, int]:
    """
    Borra carpetas __pycache__ y devuelve (borradas, errores).
    """
    objetivo = base or BASE
    carpetas = encontrar_pycache(objetivo)
    borradas = 0
    errores = 0
    for p in carpetas:
        try:
            shutil.rmtree(p)
            borradas += 1
        except OSError:
            errores += 1
    return borradas, errores


def main() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo muestra qué carpetas se borrarían, sin borrar nada.",
    )
    args = parser.parse_args()

    carpetas = encontrar_pycache(BASE)
    if not carpetas:
        print("No se encontraron carpetas __pycache__.")
        return

    print(f"Encontradas {len(carpetas)} carpetas __pycache__.")
    for p in carpetas:
        print(f" - {p}")

    if args.dry_run:
        print("\nDry-run activo: no se ha borrado nada.")
        return

    borradas, errores = borrar_pycache_en_proyecto(BASE)
    if errores > 0:
        for p in carpetas:
            if p.exists():
                print(f"[ERROR] No se pudo borrar: {p}")

    print("\nResultado:")
    print(f" - Borradas: {borradas}")
    print(f" - Errores: {errores}")


if __name__ == "__main__":
    main()
