#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Navegación en menús (atrás/adelante) y menú de pausa (Ctrl+C)."""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class AccionPausa(str, Enum):
    CONTINUAR = "continuar"
    PANTALLA_TITULO = "pantalla_titulo"
    SALIR = "salir"


class IrMenuPrincipal(Exception):
    """Volver al menú principal del juego."""


class VolverAtras(Exception):
    """Retroceder un paso en el asistente de configuración."""


class SalirPrograma(Exception):
    """Cerrar el programa por completo."""


@dataclass
class ContextoPantalla:
    """Pantalla actual: se reimprime tras continuar desde pausa."""

    titulo: str
    lineas: list[str] = field(default_factory=list)
    reimprimir: Callable[[], None] | None = None


_contexto_pantalla: ContextoPantalla | None = None


def establecer_contexto(ctx: ContextoPantalla | None) -> None:
    global _contexto_pantalla
    _contexto_pantalla = ctx


def limpiar_consola() -> None:
    """Borra la terminal (transiciones de menú, no entre preguntas del examen)."""
    import os

    if sys.platform == "win32":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="", flush=True)


def mostrar_transicion(
    dibujar: Callable[[], None],
    *,
    contexto: ContextoPantalla | None = None,
) -> None:
    """Limpia la consola y muestra una pantalla nueva (cambio de menú o paso)."""
    limpiar_consola()
    if contexto is not None:
        establecer_contexto(contexto)
    dibujar()


def refrescar_pantalla_activa() -> None:
    """Limpia la consola y vuelve a dibujar la pantalla registrada (tecla ignorada)."""
    limpiar_consola()

    ctx = _contexto_pantalla
    if ctx is None:
        return
    if ctx.reimprimir:
        try:
            ctx.reimprimir()
        except Exception:
            pass
        return
    if ctx.titulo:
        print(f"\n>> {ctx.titulo}")
    for linea in ctx.lineas:
        print(linea)


def _input_seguro(prompt: str) -> str:
    """Lee stdin; EOF (pipe cerrado) equivale a salir del programa."""
    try:
        return input(prompt)
    except EOFError:
        print("\n(Entrada cerrada.)")
        raise SalirPrograma() from None


def reimprimir_contexto() -> None:
    """Vuelve a mostrar dónde está el jugador (tras pausa → continuar)."""
    ctx = _contexto_pantalla
    if ctx is None:
        return
    print("\n" + "=" * 60)
    print(f">> {ctx.titulo}")
    for linea in ctx.lineas:
        print(linea)
    if ctx.reimprimir:
        try:
            ctx.reimprimir()
        except Exception:
            print("(No se pudo reimprimir el detalle de la pantalla.)")
    print("=" * 60)


def hint_navegacion(*, permitir_atras: bool, en_partida: bool = False) -> str:
    from .entrada_menu import hint_controles_menu

    return hint_controles_menu(
        defecto="confirmar",
        permitir_atras=permitir_atras,
        en_partida=en_partida,
    )


def _dibujar_menu_pausa(*, en_partida: bool) -> None:
    print("\n=== PAUSA ===")
    if en_partida:
        print("  1) Continuar la partida")
    else:
        print("  1) Continuar")
    print("  2) Pantalla de titulo (solo cabecera, sin reimprimir menu/pregunta)")
    print("  3) Salir del programa")


def menu_pausa(*, en_partida: bool = False) -> AccionPausa:
    from .entrada_menu import elegir_indice_menu

    ctx_previo = _contexto_pantalla
    _dibujar_menu_pausa(en_partida=en_partida)
    establecer_contexto(
        ContextoPantalla(
            titulo="Pausa",
            reimprimir=lambda: _dibujar_menu_pausa(en_partida=en_partida),
        )
    )
    try:
        idx = elegir_indice_menu(
            3,
            defecto=1,
            en_pausa=True,
            prompt="Opcion de pausa",
        )
    finally:
        establecer_contexto(ctx_previo)

    if idx == 1:
        return AccionPausa.CONTINUAR
    if idx == 2:
        return AccionPausa.PANTALLA_TITULO
    raise SalirPrograma()


def _reimprimir_solo_titulo() -> None:
    """Cabecera del contexto actual, sin volver a ejecutar reimprimir()."""
    ctx = _contexto_pantalla
    if ctx is None:
        return
    print("\n" + "=" * 60)
    print(f">> {ctx.titulo}")
    for linea in ctx.lineas:
        print(linea)
    print("=" * 60)


def _gestionar_pausa(*, en_partida: bool) -> None:
    """Primer Ctrl+C abre pausa; Ctrl+C en pausa o opcion 3 = salir del juego."""
    accion = menu_pausa(en_partida=en_partida)
    if accion == AccionPausa.CONTINUAR:
        if en_partida:
            limpiar_consola()
        reimprimir_contexto()
        return
    if accion == AccionPausa.PANTALLA_TITULO:
        if en_partida:
            limpiar_consola()
        _reimprimir_solo_titulo()
        return


def leer_linea(
    mensaje: str,
    *,
    permitir_atras: bool = False,
    en_partida: bool = False,
    mayusculas: bool = False,
) -> str:
    """Lee una línea; Ctrl+C abre pausa; 'A' retrocede si está permitido."""
    sufijo = hint_navegacion(permitir_atras=permitir_atras, en_partida=en_partida)
    prompt = f"{mensaje.rstrip()}{sufijo}: "
    while True:
        try:
            texto = _input_seguro(prompt).strip()
        except KeyboardInterrupt:
            _gestionar_pausa(en_partida=en_partida)
            continue
        except SalirPrograma:
            raise
        return texto.upper() if mayusculas else texto


class AsistentePasos:
    """
    Asistente lineal con pasos adelante y atras (Supr = paso anterior).
    El primer paso no puede ir mas atras -> IrMenuPrincipal.
    """

    def __init__(self, titulo: str) -> None:
        self.titulo = titulo
        self.datos: dict = {}
        self._indice = 0
        self._pasos: list[tuple[str, Callable[["AsistentePasos"], None]]] = []

    def _reimprimir_paso(self) -> None:
        if self._indice >= len(self._pasos):
            return
        nombre, _ = self._pasos[self._indice]
        total = len(self._pasos)
        print(f"\n--- {self.titulo}: paso {self._indice + 1}/{total} — {nombre} ---")

    def _registrar_contexto_paso(self) -> None:
        if self._indice >= len(self._pasos):
            return
        nombre, _ = self._pasos[self._indice]
        total = len(self._pasos)
        establecer_contexto(
            ContextoPantalla(
                titulo=f"{self.titulo} — paso {self._indice + 1}/{total}: {nombre}",
                lineas=[
                    "Enter = defecto · numeros = opcion · Supr = atras · Ctrl+C = pausa",
                ],
                reimprimir=self._reimprimir_paso,
            )
        )
        self._reimprimir_paso()

    def ejecutar(self, pasos: list[tuple[str, Callable[["AsistentePasos"], None]]]) -> None:
        self._pasos = pasos
        total = len(pasos)
        while self._indice < total:
            self._registrar_contexto_paso()
            _, fn = pasos[self._indice]
            try:
                fn(self)
            except VolverAtras:
                if self._indice > 0:
                    self._indice -= 1
                    print("<- Paso anterior")
                    continue
                print("<- Menu principal")
                raise IrMenuPrincipal() from None
            except (IrMenuPrincipal, SalirPrograma):
                raise
            except Exception as exc:
                print(f"\n[!] No se pudo completar este paso: {exc}")
                print("    Revisa la entrada o pulsa Supr para retroceder.")
                continue
            self._indice += 1
        establecer_contexto(None)
