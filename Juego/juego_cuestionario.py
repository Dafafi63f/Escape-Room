#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada del cuestionario MATCAD en consola.

La implementación está en Juego/Consola/; este archivo solo arranca el menú.

Uso:
  python Juego/juego_cuestionario.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_JUEGO = Path(__file__).resolve().parent
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Consola.consola import pedir_opcion
from Consola.entrada_menu import esperar_enter_en_foco
from Consola.datos import cargar_materias, cargar_preguntas, elegir_banco_preguntas
from Consola.modo_feedback import ejecutar_feedback_rapido, jugar_modo_feedback
from Consola.modo_historia import jugar_modo_historia
from Consola.modo_libre import jugar_modo_libre
from Consola.navegacion import (
    ContextoPantalla,
    IrMenuPrincipal,
    SalirPrograma,
    VolverAtras,
    establecer_contexto,
    mostrar_transicion,
    registrar_atajo_feedback,
)
from Consola.rutas import PATH_MATERIAS, PATH_PREGUNTAS, resolver_plantillas

from Consola.datos import cargar_orden_materias  # noqa: F401
from Consola.modelos import BancoPreguntas, Pregunta  # noqa: F401
from Consola.rutas import resolver_dataset  # noqa: F401


def _mostrar_tutorial_inicio() -> None:
    print("\n=== CUESTIONARIO MATCAD ===")
    print("\n  Tutorial - donde hacer clic")
    print()
    print("  Este juego no usa comandos de texto: cada accion es una tecla.")
    print()
    print("  Para que el teclado responda, haz clic dentro de esta ventana")
    print("  (la terminal del juego). Sin ese clic, las teclas no se registran.")
    print()
    print("  Cuando veas >> al inicio de una linea, haz clic ahi")
    print("  y usa el teclado como indique esa linea.")
    print()
    print("  Pulsa H en cualquier momento para ver los controles del momento.")
    print("  Pulsa F en cualquier momento para enviar feedback (sin borrar la pantalla).")


def _contexto_tutorial_inicio() -> ContextoPantalla:
    return ContextoPantalla(
        titulo="Tutorial - foco del teclado",
        lineas=["Haz clic en la linea que empieza por >> y pulsa Enter."],
        reimprimir=_mostrar_tutorial_inicio,
    )


def _tutorial_inicio() -> None:
    """Pantalla inicial: tutorial de clic. Solo Enter en >> continua."""
    ctx = _contexto_tutorial_inicio()
    mostrar_transicion(_mostrar_tutorial_inicio, contexto=ctx)
    esperar_enter_en_foco(reimprimir=_mostrar_tutorial_inicio)


def _mostrar_menu_principal() -> None:
    print("\n=== CUESTIONARIO MATCAD ===")
    print("  1) Modo libre — partida abierta, filtros e informes")
    print("  2) Modo historia — examen balanceado (histórico de qualificacions)")
    print("  3) Modo feedback — enviar aviso al creador (bug, sugerencia, etc.)")
    print("  4) Salir")


def _contexto_menu_principal() -> ContextoPantalla:
    return ContextoPantalla(
        titulo="Menú principal",
        lineas=["Elige un modo de juego."],
        reimprimir=_mostrar_menu_principal,
    )


def _ir_menu_principal() -> None:
    mostrar_transicion(_mostrar_menu_principal, contexto=_contexto_menu_principal())


def elegir_modo_juego() -> str:
    _ir_menu_principal()
    return pedir_opcion(
        "Selecciona modo",
        ["1", "2", "3", "4"],
        default="1",
        es_menu_principal=True,
    )


def _ejecutar_modo(
    modo: str,
    materias_meta: dict,
    path_plantillas,
) -> bool:
    if modo == "2":
        preguntas = cargar_preguntas(PATH_PREGUNTAS, materias_meta)
        if not preguntas:
            print("No hay preguntas en el dataset.")
            return False
        return jugar_modo_historia(preguntas, materias_meta)

    if modo == "3":
        preguntas = cargar_preguntas(PATH_PREGUNTAS, materias_meta)
        if not preguntas:
            print("No hay preguntas en el dataset.")
            return False
        jugar_modo_feedback(preguntas, materias_meta)
        return True

    try:
        preguntas, banco = elegir_banco_preguntas(
            PATH_PREGUNTAS, path_plantillas, materias_meta
        )
    except (VolverAtras, IrMenuPrincipal):
        return False
    except SalirPrograma:
        raise
    if not preguntas:
        print("No hay preguntas jugables en ese banco.")
        return False
    return jugar_modo_libre(preguntas, banco)


def _bucle_juego(materias_meta: dict, path_plantillas) -> None:
    while True:
        try:
            modo = elegir_modo_juego()
        except IrMenuPrincipal:
            continue
        except SalirPrograma:
            return

        if modo == "4":
            return

        try:
            flujo_completo = _ejecutar_modo(modo, materias_meta, path_plantillas)
        except IrMenuPrincipal:
            _ir_menu_principal()
            continue
        except SalirPrograma:
            return

        if not flujo_completo:
            _ir_menu_principal()
            continue

        try:
            otra = pedir_opcion(
                "\n¿Volver al menú principal? (S/N): ",
                ["S", "N"],
                default="S",
                permitir_atras=False,
            )
        except SalirPrograma:
            return
        except IrMenuPrincipal:
            _ir_menu_principal()
            continue
        if otra == "N":
            return
        _ir_menu_principal()


def main() -> None:
    try:
        materias_meta = cargar_materias(PATH_MATERIAS)
        path_plantillas = resolver_plantillas()
    except FileNotFoundError as e:
        print(str(e))
        return

    registrar_atajo_feedback(ejecutar_feedback_rapido)
    try:
        _tutorial_inicio()
        _bucle_juego(materias_meta, path_plantillas)
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
