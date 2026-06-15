#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Borra artefactos temporales del proyecto: ``__pycache__`` y ficheros ``.txt`` de informes/feedback.

Los ``.txt`` solo se buscan en ``Juego/Informes/`` y ``Juego/Feedback/`` (no en todo el repo).
Recorre todo el TFG para ``__pycache__`` (salvo ``.venv``, ``build``, ``.git``, etc.).

Uso (desde la raíz del TFG):
  python borrar_temporales.py
  python borrar_temporales.py --dry-run
  python borrar_temporales.py --solo-pycache
  python borrar_temporales.py --solo-txt
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_BASE = Path(__file__).resolve().parent

# Solo estos directorios contienen .txt generados al jugar (informes, feedback).
_CARPETAS_TXT_TEMPORALES = (
    _BASE / "Juego" / "Informes",
    _BASE / "Juego" / "Feedback",
)

_OMITIR_PARTES = frozenset({
    ".venv",
    "venv",
    ".git",
    "build",
    "dist",
    "node_modules",
})


@dataclass
class ResumenLimpieza:
    pycache_borradas: int = 0
    pycache_errores: int = 0
    txt_borrados: int = 0
    txt_errores: int = 0
    bytes_txt: int = 0

    @property
    def errores_totales(self) -> int:
        return self.pycache_errores + self.txt_errores


def _dentro_de_omitidos(ruta: Path, raiz: Path) -> bool:
    try:
        relativa = ruta.relative_to(raiz)
    except ValueError:
        return True
    return any(parte in _OMITIR_PARTES for parte in relativa.parts)


def _formatear_tamano(bytes_total: int) -> str:
    if bytes_total < 1024:
        return f"{bytes_total} B"
    if bytes_total < 1024 * 1024:
        return f"{bytes_total / 1024:.1f} KiB"
    return f"{bytes_total / (1024 * 1024):.2f} MiB"


def listar_pycache(base: Path | None = None) -> list[Path]:
    raiz = base or _BASE
    return sorted(
        p
        for p in raiz.rglob("__pycache__")
        if p.is_dir() and not _dentro_de_omitidos(p, raiz)
    )


def listar_txt_temporales(base: Path | None = None) -> list[Path]:
    """Solo informes y feedback del juego; no toca otros ``.txt`` del repo."""
    raiz = base or _BASE
    encontrados: list[Path] = []
    for carpeta in _CARPETAS_TXT_TEMPORALES:
        if not carpeta.is_dir():
            continue
        for p in carpeta.glob("*.txt"):
            if p.is_file() and not _dentro_de_omitidos(p, raiz):
                encontrados.append(p)
    return sorted(encontrados)


def borrar_temporales(
    base: Path | None = None,
    *,
    incluir_pycache: bool = True,
    incluir_txt: bool = True,
) -> ResumenLimpieza:
    raiz = base or _BASE
    resumen = ResumenLimpieza()

    if incluir_pycache:
        for carpeta in listar_pycache(raiz):
            try:
                shutil.rmtree(carpeta)
                resumen.pycache_borradas += 1
            except OSError:
                resumen.pycache_errores += 1

    if incluir_txt:
        for fichero in listar_txt_temporales(raiz):
            try:
                resumen.bytes_txt += fichero.stat().st_size
                fichero.unlink()
                resumen.txt_borrados += 1
            except OSError:
                resumen.txt_errores += 1

    return resumen


def _imprimir_listado(
    *,
    pycache: list[Path],
    txt: list[Path],
    incluir_pycache: bool,
    incluir_txt: bool,
) -> bool:
    hay_algo = False

    if incluir_pycache and pycache:
        hay_algo = True
        print(f"__pycache__: {len(pycache)} carpetas")
        for p in pycache:
            print(f" - {p}")

    if incluir_txt and txt:
        hay_algo = True
        bytes_total = sum(p.stat().st_size for p in txt)
        print(f".txt: {len(txt)} ficheros ({_formatear_tamano(bytes_total)})")
        for p in txt:
            print(f" - {p}")

    return hay_algo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Borra artefactos temporales (__pycache__ y .txt) en todo el proyecto",
    )
    parser.add_argument("--dry-run", action="store_true", help="Solo lista, sin borrar")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument(
        "--solo-pycache",
        action="store_true",
        help="Solo carpetas __pycache__",
    )
    grupo.add_argument(
        "--solo-txt",
        action="store_true",
        help="Solo ficheros .txt",
    )
    args = parser.parse_args(argv)

    incluir_pycache = not args.solo_txt
    incluir_txt = not args.solo_pycache

    pycache = listar_pycache(_BASE) if incluir_pycache else []
    txt = listar_txt_temporales(_BASE) if incluir_txt else []

    if not _imprimir_listado(
        pycache=pycache,
        txt=txt,
        incluir_pycache=incluir_pycache,
        incluir_txt=incluir_txt,
    ):
        print("No se encontraron artefactos temporales en el proyecto.")
        return 0

    if args.dry_run:
        print("\nDry-run: no se ha borrado nada.")
        return 0

    resumen = borrar_temporales(
        _BASE,
        incluir_pycache=incluir_pycache,
        incluir_txt=incluir_txt,
    )
    print("\nResumen:")
    if incluir_pycache:
        print(
            f"  __pycache__: {resumen.pycache_borradas} borradas | "
            f"errores: {resumen.pycache_errores}"
        )
    if incluir_txt:
        print(
            f"  .txt: {resumen.txt_borrados} borrados | errores: {resumen.txt_errores} | "
            f"liberados: {_formatear_tamano(resumen.bytes_txt)}"
        )
    return 1 if resumen.errores_totales else 0


if __name__ == "__main__":
    raise SystemExit(main())
