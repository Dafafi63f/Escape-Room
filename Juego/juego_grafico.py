#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada del cuestionario MATCAD en pygame.

Prototipo: menú principal y modo libre jugable (bloque corto arcade).
Controles: ratón para navegar; teclado solo para escribir texto cuando haga falta.

Uso:
  pip install -r requirements.txt
  python Juego/juego_grafico.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_JUEGO = Path(__file__).resolve().parent
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.datos import cargar_materias, cargar_preguntas
from Comun.rutas import PATH_MATERIAS, PATH_PREGUNTAS, resolver_plantillas
from Grafico.app import AplicacionGrafica, DatosJuego


def main() -> None:
    try:
        import pygame  # noqa: F401 — comprobación temprana de dependencia
    except ImportError:
        print("Falta pygame. Instálalo con:")
        print("  pip install -r requirements.txt")
        return

    try:
        materias_meta = cargar_materias(PATH_MATERIAS)
        preguntas_dataset = cargar_preguntas(PATH_PREGUNTAS, materias_meta)
    except FileNotFoundError as e:
        print(str(e))
        return

    datos = DatosJuego(
        num_preguntas=len(preguntas_dataset),
        num_materias=len(materias_meta),
        preguntas=preguntas_dataset,
        materias_meta=materias_meta,
        path_preguntas_csv=PATH_PREGUNTAS,
        path_plantillas_json=resolver_plantillas(),
    )
    AplicacionGrafica(datos).ejecutar()


if __name__ == "__main__":
    main()
