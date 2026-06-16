#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada del cuestionario MATCAD en consola.

Orquesta el flujo de alto nivel (sin lógica de partida):
  1. Carga datos (materias, plantillas).
  2. Tutorial de foco de teclado (clic en >> + Enter).
  3. Bucle: menú principal → modo libre / historia / feedback → volver o salir.

La implementación está en Juego/Consola/.

Uso:
  python Juego/juego_consola.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_JUEGO = Path(__file__).resolve().parent
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Consola.app import bucle_juego, tutorial_inicio
from Comun.datos import cargar_materias, cargar_preguntas
from Consola.modo_feedback import ejecutar_feedback_rapido
from Consola.navegacion import SalirPrograma, registrar_atajo_feedback
from Comun.rutas import PATH_MATERIAS, PATH_PREGUNTAS, resolver_plantillas


def main() -> None:
    try:
        materias_meta = cargar_materias(PATH_MATERIAS)
        preguntas_dataset = cargar_preguntas(PATH_PREGUNTAS, materias_meta)
        path_plantillas = resolver_plantillas()
    except FileNotFoundError as e:
        print(str(e))
        return

    registrar_atajo_feedback(ejecutar_feedback_rapido)
    try:
        tutorial_inicio()
        bucle_juego(materias_meta, preguntas_dataset, path_plantillas)
    except SalirPrograma:
        pass
    except KeyboardInterrupt:
        print("\n\nInterrupción.")
    except EOFError:
        print("\n\nEntrada cerrada.")
    except Exception as exc:
        print(f"\n\nError inesperado: {exc}")
        print("El juego se ha cerrado de forma segura.")
    finally:
        registrar_atajo_feedback(None)

    print("¡Hasta pronto!")


if __name__ == "__main__":
    main()
