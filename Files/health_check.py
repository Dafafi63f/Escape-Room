#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprobación integral del TFG: datos del juego, tests y validación del banco.

  python Files/health_check.py
  python Files/health_check.py --solo-datos
  python Files/health_check.py --solo-tests
  python Files/health_check.py --solo-validar
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_FILES = Path(__file__).resolve().parent
ROOT = _FILES.parent

if sys.platform == "win32":
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")


def _bootstrap() -> None:
    juego = ROOT / "Juego"
    for path in (ROOT, juego, _FILES):
        s = str(path)
        if s not in sys.path:
            sys.path.insert(0, s)


def paso_datos() -> int:
    _bootstrap()
    from Comun.contenido import cargar_contenido_juego, construir_datos_juego

    contenido = cargar_contenido_juego()
    datos = construir_datos_juego(contenido)
    print(
        f"OK datos: {datos.num_preguntas} preguntas, "
        f"{datos.num_materias} materias, paquete={contenido.perfil.tipo_paquete}"
    )
    if datos.num_preguntas <= 0:
        print("ERROR: pool de preguntas vacío", file=sys.stderr)
        return 1
    return 0


def paso_tests(*, verbose: bool) -> int:
    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "Tests",
        "-t",
        ".",
    ]
    if verbose:
        cmd.append("-v")
    print(">>", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def paso_validar(*, detalle: bool, estricto: bool) -> int:
    cmd = [sys.executable, str(_FILES / "mantenimiento.py"), "validar"]
    if detalle:
        cmd.append("--detalle")
    if estricto:
        cmd.append("--estricto")
    print(">>", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Health check del TFG (datos + tests + banco)")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--solo-datos", action="store_true", help="Solo comprobar carga de datos")
    modo.add_argument("--solo-tests", action="store_true", help="Solo ejecutar tests de Tests/")
    modo.add_argument("--solo-validar", action="store_true", help="Solo validar banco cerrado")
    parser.add_argument("-v", "--verbose", action="store_true", help="Tests en modo verbose")
    parser.add_argument("--detalle", action="store_true", help="Pasar --detalle a validar")
    parser.add_argument("--estricto", action="store_true", help="Pasar --estricto a validar")
    args = parser.parse_args(argv)

    pasos: list[tuple[str, int]] = []
    if args.solo_datos:
        pasos = [("datos", paso_datos())]
    elif args.solo_tests:
        pasos = [("tests", paso_tests(verbose=args.verbose))]
    elif args.solo_validar:
        pasos = [("validar", paso_validar(detalle=args.detalle, estricto=args.estricto))]
    else:
        pasos = [
            ("datos", paso_datos()),
            ("tests", paso_tests(verbose=args.verbose)),
            ("validar", paso_validar(detalle=args.detalle, estricto=args.estricto)),
        ]

    fallos = [nombre for nombre, codigo in pasos if codigo != 0]
    if fallos:
        print(f"Health check FALLIDO en: {', '.join(fallos)}", file=sys.stderr)
        return 1
    print("Health check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
