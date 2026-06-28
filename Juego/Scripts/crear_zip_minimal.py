#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera ``Juego/Distribucion/MATCAD_juego_minimal.zip`` (motor + CSV reducido).

Uso (desde la raíz del repo):
  python Juego/Scripts/crear_zip_minimal.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
_JUEGO = _RAIZ / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))
_CSV_ORIGEN = _RAIZ / "Tests" / "Fixtures" / "Preguntas_minimal.csv"
_PRESETS_ORIGEN = _JUEGO / "presets.json"
_SALIDA_DEFECTO = _JUEGO / "Distribucion" / "MATCAD_juego_minimal.zip"
_BANCO_ORIGEN = _RAIZ / "Data" / "Banco" / "Preguntas.csv"
_CHANGELOG_JUEGO = _RAIZ / "Docs" / "CHANGELOG_JUEGO.md"
from Comun.presets_historia import PRESETS_JSON_MINIMO

# Módulos que NO van en el zip mínimo (rutas relativas a Juego/).
# Mantener alineado con Juego/Scripts/auditar_contenido_minimo.py
_MODULOS_EXCLUIDOS_MINIMO = frozenset({
    "Comun/escape_room.py",
    "Comun/escape_partida.py",
    "Comun/tienda_escape.py",
    "Grafico/pantallas_escape.py",
    "Grafico/pantallas_historia.py",
})


def _cargar_generador_minimal():
    ruta = _RAIZ / "Tests" / "Fixtures" / "generar_preguntas_minimal.py"
    spec = importlib.util.spec_from_file_location("generar_preguntas_minimal", ruta)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar {ruta}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.generar_preguntas_minimal


generar_preguntas_minimal = _cargar_generador_minimal()

_EXCLUIR_CARPETAS = frozenset(
    {"__pycache__", "build", "dist", "Scripts", "Distribucion"}
)
_EXCLUIR_SUFIJOS = frozenset({".pyc", ".exe", ".zip", ".ps1", ".spec", ".md"})

_LEEME = """\
MATCAD — paquete mínimo (solo CSV de preguntas)
===============================================

Contenido: motor del juego (pygame) + Preguntas.csv (columnas mínimas).
Modo libre simplificado; resistencia con eventos. Modo historia no incluido.
Examen fijo en la barra superior (📕): del día, aleatorio o semilla numérica.
Paquete aislado del MATCAD completo.

REQUISITOS
----------
- Python 3.10+ con pip
- pygame-ce (se instala abajo)

PASOS (Windows)
---------------
1. Descomprime el zip en una carpeta (p. ej. MATCAD_minimal\\).
2. Entra en esa carpeta e instala dependencias (solo la primera vez):
     pip install -r Juego\\requirements.txt
3. Arranca desde la misma carpeta:
     doble clic en Jugar.bat
   o:
     python Juego\\juego_grafico.py

Linux / macOS: mismos comandos con barras normales.

NOTAS
-----
- Los datos locales (preferencias, estadísticas) se crean al jugar en Data/Juego/
  dentro de la carpeta descomprimida (se generan solos).
- Para el juego completo (40 materias, escape room…) usa
  MATCAD_juego_portable.zip (paquete distinto; puedes tener ambos instalados).
"""

_JUGAR_BAT = """\
@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 Juego\\juego_grafico.py
    goto :fin
)

where python >nul 2>&1
if %errorlevel%==0 (
    python Juego\\juego_grafico.py
    goto :fin
)

echo.
echo No se encontro Python en el PATH.
echo Instala Python 3.10+ y ejecuta:
echo   pip install -r Juego\\requirements.txt
echo   python Juego\\juego_grafico.py
echo.

:fin
if errorlevel 1 pause
"""


def _iter_codigo_juego() -> list[tuple[Path, str]]:
    ficheros: list[tuple[Path, str]] = []
    for ruta in sorted(_JUEGO.rglob("*")):
        if not ruta.is_file():
            continue
        rel = ruta.relative_to(_JUEGO)
        if any(part in _EXCLUIR_CARPETAS for part in rel.parts):
            continue
        if ruta.suffix.lower() in _EXCLUIR_SUFIJOS:
            continue
        if ruta.suffix != ".py" and ruta.name not in ("requirements.txt",):
            continue
        if ruta.name == "presets.json":
            continue
        rel_posix = rel.as_posix()
        if rel_posix in _MODULOS_EXCLUIDOS_MINIMO:
            continue
        ficheros.append((ruta, f"Juego/{rel.as_posix()}"))
    return ficheros


def _ruta_en_zip(*partes: str) -> str:
    return "/".join(partes)


def entradas_zip_minimal() -> list[Path]:
    """Ficheros cuyo cambio invalida ``MATCAD_juego_minimal.zip``."""
    entradas: list[Path] = [
        _BANCO_ORIGEN,
        _PRESETS_ORIGEN,
        _CHANGELOG_JUEGO,
        Path(__file__).resolve(),
        _RAIZ / "Tests" / "Fixtures" / "generar_preguntas_minimal.py",
    ]
    entradas.extend(ruta for ruta, _ in _iter_codigo_juego())
    return entradas


def _presets_minimal_bytes() -> bytes:
    data = json.loads(_PRESETS_ORIGEN.read_text(encoding="utf-8"))
    presets = [p for p in data["presets"] if p["id"] in PRESETS_JSON_MINIMO]
    ids = {p["id"] for p in presets}
    if ids != PRESETS_JSON_MINIMO:
        raise ValueError(
            f"presets.json mínimo incompleto; faltan {sorted(PRESETS_JSON_MINIMO - ids)}"
        )
    reducido = {**data, "presets": presets}
    return (json.dumps(reducido, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def crear_zip_minimal(destino: Path = _SALIDA_DEFECTO) -> tuple[Path, int]:
    n_csv = generar_preguntas_minimal(_BANCO_ORIGEN, _CSV_ORIGEN)
    if n_csv == 0:
        raise ValueError("El CSV mínimo no contiene preguntas.")
    if not _CHANGELOG_JUEGO.is_file():
        raise FileNotFoundError(f"No se encontró el changelog: {_CHANGELOG_JUEGO}")

    destino.parent.mkdir(parents=True, exist_ok=True)
    ficheros = _iter_codigo_juego()

    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(_ruta_en_zip("LEEME.txt"), _LEEME)
        zf.writestr(_ruta_en_zip("Jugar.bat"), _JUGAR_BAT)
        zf.writestr(_ruta_en_zip(".matcad-paquete-minimo"), "MATCAD paquete mínimo\n")
        zf.write(_CSV_ORIGEN, _ruta_en_zip("Preguntas.csv"))
        zf.writestr(_ruta_en_zip("Juego", "presets.json"), _presets_minimal_bytes())
        zf.write(_CHANGELOG_JUEGO, _ruta_en_zip("Juego", "CHANGELOG_JUEGO.md"))
        for ruta, nombre in ficheros:
            zf.write(ruta, nombre)

    return destino, n_csv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Crea MATCAD_juego_minimal.zip (juego + CSV reducido)"
    )
    parser.add_argument(
        "-o",
        "--salida",
        type=Path,
        default=_SALIDA_DEFECTO,
        help=f"Ruta del zip (defecto: {_SALIDA_DEFECTO.relative_to(_RAIZ)})",
    )
    args = parser.parse_args()
    salida, n_csv = crear_zip_minimal(args.salida.resolve())
    tam_kb = salida.stat().st_size / 1024
    n_py = sum(1 for _, n in _iter_codigo_juego() if n.endswith(".py"))
    try:
        ruta_txt = salida.relative_to(_RAIZ)
    except ValueError:
        ruta_txt = salida
    print(f"ZIP creado: {ruta_txt}")
    print(f"  Tamaño: {tam_kb:.0f} KiB")
    print(f"  Módulos Python: {n_py}")
    print(f"  Excluidos: {len(_MODULOS_EXCLUIDOS_MINIMO)} módulos (escape room, carrusel historia)")
    print("  Raíz del zip: Juego/ (código + CHANGELOG_JUEGO.md), Preguntas.csv, Jugar.bat")
    print(f"  CSV: Preguntas.csv ({n_csv} preguntas)")
    print("\nPrueba local (sin descomprimir el zip):")
    print("  python Juego/juego_grafico.py --csv Tests/Fixtures/Preguntas_minimal.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
