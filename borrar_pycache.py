#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Borra carpetas ``__pycache__`` del proyecto.

No depende de ``Files/Scripts``; funciona solo con la biblioteca estándar.

Uso (desde la raíz del TFG):
  python borrar_pycache.py
  python borrar_pycache.py --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent

# No recorrer entornos virtuales ni artefactos de build del .exe.
_OMITIR_PARTES = frozenset({
    ".venv",
    "venv",
    ".git",
    "build",
    "dist",
    "node_modules",
})


def _dentro_de_omitidos(ruta: Path) -> bool:
    return any(parte in _OMITIR_PARTES for parte in ruta.parts)


def listar_pycache(base: Path | None = None) -> list[Path]:
    raiz = base or BASE
    return sorted(
        p
        for p in raiz.rglob("__pycache__")
        if p.is_dir() and not _dentro_de_omitidos(p.relative_to(raiz))
    )


def borrar_pycache_en_proyecto(base: Path | None = None) -> tuple[int, int]:
    """Borra carpetas ``__pycache__`` bajo ``base``. Devuelve (borradas, errores)."""
    carpetas = listar_pycache(base)
    borradas = 0
    errores = 0
    for p in carpetas:
        try:
            shutil.rmtree(p)
            borradas += 1
        except OSError:
            errores += 1
    return borradas, errores


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Borra carpetas __pycache__ del proyecto")
    parser.add_argument("--dry-run", action="store_true", help="Solo lista carpetas, sin borrar")
    args = parser.parse_args(argv)

    carpetas = listar_pycache(BASE)
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
    print(f"\nBorradas: {borradas} | Errores: {errores}")
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
