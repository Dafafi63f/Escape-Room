#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada del cuestionario MATCAD en pygame.

Cinco modos: libre, historia, resistencia, escape room y feedback.
Controles: ratón para navegar; teclado solo para escribir texto cuando haga falta.

Uso:
  pip install -r Juego/requirements.txt
  python Juego/juego_grafico.py
  python Juego/juego_grafico.py --csv ruta/Preguntas.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_JUEGO = Path(__file__).resolve().parent
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.contenido import cargar_contenido_juego, construir_datos_juego
from Comun.persistencia import inicializar_datos_locales_juego
from Comun.util import configurar_stdio_utf8
from Grafico.app import AplicacionGrafica


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MATCAD — cuestionario gráfico")
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Ruta al CSV de preguntas (por defecto: Data/Banco/Preguntas.csv)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    configurar_stdio_utf8()
    args = _parse_args([] if argv is None else argv)
    try:
        import pygame  # noqa: F401 — comprobación temprana de dependencia
    except ImportError:
        print("Falta pygame. Instálalo con:")
        print("  pip install -r Juego/requirements.txt")
        print("  (desde la raíz del proyecto descomprimido)")
        return

    try:
        contenido = cargar_contenido_juego(path_csv=args.csv)
    except FileNotFoundError as e:
        print(str(e))
        return

    inicializar_datos_locales_juego()
    datos = construir_datos_juego(contenido)
    AplicacionGrafica(datos).ejecutar()


if __name__ == "__main__":
    main(sys.argv[1:])
