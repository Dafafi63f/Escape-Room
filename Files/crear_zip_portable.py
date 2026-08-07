#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera el zip jugable (Juego + Data necesarios; sin Tests/Docs/Files).

Uso (desde la raíz del repo)::

    python Docs/utilidades.py --solo-zip
    python Files/crear_zip_portable.py

Salida por defecto: ``MATCAD_juego_portable.zip`` en la raíz del repo
(no se versiona; CI lo publica en el release ``juego``).
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[1]
_JUEGO = _RAIZ / "Juego"
_DATA = _RAIZ / "Data"
_SALIDA_DEFECTO = _RAIZ / "MATCAD_juego_portable.zip"

_MARCADOR_COMPLETO = ".matcad-paquete-completo"

# Solo lo imprescindible para jugar el paquete completo.
_DATA_INCLUIR = (
    "Banco/Preguntas.csv",
    "Banco/listado_materias.csv",
    "Banco/plantillas.json",
    "Plantillas/Preguntas.csv",
    "Plantillas/README.md",
    "README.md",
)

_EXCLUIR_NOMBRES = {
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".git",
}

_LEEME_ZIP = """CUESTIONARIO MATCAD — Paquete jugable
=====================================

1. Instala Python 3.10+ desde https://www.python.org/downloads/
   (marca "Add python.exe to PATH").
2. En esta carpeta (la del zip descomprimido):
     pip install -r Juego\\requirements.txt
   o haz doble clic en Jugar.bat (Windows).
3. Arranca:
     python Juego\\juego_grafico.py

Más ayuda: Juego\\COMO_JUGAR.md
Repositorio (código completo, tests, docs):
  https://github.com/Dafafi63f/Escape-Room
"""


def _omitir(ruta: Path) -> bool:
    return any(parte in _EXCLUIR_NOMBRES for parte in ruta.parts)


def _anadir_archivo(zf: zipfile.ZipFile, origen: Path, arcname: str) -> None:
    zf.write(origen, arcname.replace("\\", "/"))


def crear_zip_portable(destino: Path = _SALIDA_DEFECTO) -> Path:
    destino = destino.resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    jugar_bat = _RAIZ / "Jugar.bat"
    if not jugar_bat.is_file():
        raise FileNotFoundError(f"Falta {jugar_bat}")

    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("LEEME.txt", _LEEME_ZIP)
        _anadir_archivo(zf, jugar_bat, "Jugar.bat")
        zf.writestr(_MARCADOR_COMPLETO, "completo\n")

        for ruta in sorted(_JUEGO.rglob("*")):
            if not ruta.is_file() or _omitir(ruta.relative_to(_JUEGO)):
                continue
            if ruta.suffix.lower() in {".pyc", ".pyo"}:
                continue
            rel = ruta.relative_to(_RAIZ).as_posix()
            _anadir_archivo(zf, ruta, rel)

        for rel in _DATA_INCLUIR:
            origen = _DATA / rel
            if not origen.is_file():
                raise FileNotFoundError(f"Falta dato requerido: {origen}")
            _anadir_archivo(zf, origen, f"Data/{rel}")

    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera el zip jugable MATCAD.")
    parser.add_argument(
        "-o",
        "--salida",
        type=Path,
        default=_SALIDA_DEFECTO,
        help=f"Ruta del zip (defecto: {_SALIDA_DEFECTO})",
    )
    args = parser.parse_args()
    salida = crear_zip_portable(args.salida)
    tamano_kib = salida.stat().st_size / 1024
    print(f"OK: {salida} ({tamano_kib:.0f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
