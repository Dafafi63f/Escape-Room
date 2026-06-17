#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Navegación en menús (atrás/adelante) y menú de pausa (Esc)."""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from Consola.textos_consola import (
    BTN_CONTINUAR,
    BTN_CONTINUAR_PARTIDA,
    BTN_PANTALLA_TITULO,
    BTN_SALIR_PROGRAMA,
    banner,
    btn,
    con_emoji,
    nombre_paso,
    titulo as titulo_ui,
)


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


class CancelarFeedbackRapido(Exception):
    """Sale del feedback rapido (tecla F) sin ir al menu principal."""


@dataclass
class ContextoPantalla:
    """Pantalla actual: se reimprime tras continuar desde pausa."""

    titulo: str
    lineas: list[str] = field(default_factory=list)
    reimprimir: Callable[[], None] | None = None


_contexto_pantalla: ContextoPantalla | None = None
_callback_feedback_rapido: Callable[[], None] | None = None
_feedback_rapido_activo: bool = False


def establecer_contexto(ctx: ContextoPantalla | None) -> None:
    global _contexto_pantalla
    _contexto_pantalla = ctx


def obtener_contexto_pantalla() -> ContextoPantalla | None:
    return _contexto_pantalla


def registrar_atajo_feedback(callback: Callable[[], None] | None) -> None:
    """Registra la accion de la tecla F (feedback rapido desde cualquier pantalla)."""
    global _callback_feedback_rapido
    _callback_feedback_rapido = callback


def feedback_rapido_disponible() -> bool:
    return _callback_feedback_rapido is not None and not _feedback_rapido_activo


def invocar_feedback_rapido() -> None:
    """Abre el asistente de feedback sin limpiar la terminal (si esta registrado)."""
    global _feedback_rapido_activo
    if not feedback_rapido_disponible() or _callback_feedback_rapido is None:
        return
    _feedback_rapido_activo = True
    ctx_previo = _contexto_pantalla
    try:
        _callback_feedback_rapido()
    finally:
        _feedback_rapido_activo = False
        establecer_contexto(ctx_previo)
        if ctx_previo is not None:
            continuar_pantalla_sin_limpiar()


def continuar_pantalla_sin_limpiar() -> None:
    """Reimprime la pantalla actual debajo del historial (sin borrar la terminal)."""
    ctx = _contexto_pantalla
    if ctx is None:
        return
    print("\n" + "=" * 60)
    print(">> Vuelves a donde estabas")
    print("=" * 60)
    if ctx.reimprimir:
        try:
            ctx.reimprimir()
        except Exception:
            print("(No se pudo reimprimir el detalle de la pantalla.)")
    elif ctx.titulo:
        print(f"\n>> {ctx.titulo}")
        for linea in ctx.lineas:
            print(linea)


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


def _dibujar_menu_ayuda() -> None:
    from .entrada_menu import lineas_ayuda_dinamica

    print(f"\n{banner('AYUDA — CONTROLES ACTUALES')}")
    for linea in lineas_ayuda_dinamica(desde_menu_ayuda=True):
        if not linea:
            print()
        elif linea.startswith("  "):
            print(linea)
        else:
            print(f"  {linea}")


def menu_ayuda_dinamico(*, en_partida: bool = False) -> None:
    """Muestra controles del momento actual. Solo Supr o Esc tienen efecto."""
    from .entrada_menu import TECLA_PAUSA, TipoTecla, _imprimir_linea_accion, leer_tecla

    while True:
        limpiar_consola()
        _dibujar_menu_ayuda()
        _imprimir_linea_accion(f"Supr cerrar, {TECLA_PAUSA} pausa", con_dos_puntos=False)
        try:
            ev = leer_tecla()
        except EOFError:
            raise SalirPrograma() from None
        if ev.tipo == TipoTecla.SUPR:
            return
        if ev.tipo == TipoTecla.ESCAPE:
            _gestionar_pausa(en_partida=en_partida)
            continue


def _dibujar_menu_pausa(*, en_partida: bool) -> None:
    print(f"\n{banner('PAUSA')}")
    if en_partida:
        print(f"  1) {btn(BTN_CONTINUAR_PARTIDA)}")
    else:
        print(f"  1) {btn(BTN_CONTINUAR)}")
    print(f"  2) {btn(BTN_PANTALLA_TITULO)}")
    print(f"  3) {btn(BTN_SALIR_PROGRAMA)}")


def menu_pausa(*, en_partida: bool = False) -> AccionPausa:
    from .entrada_menu import elegir_indice_menu

    ctx_previo = _contexto_pantalla
    _dibujar_menu_pausa(en_partida=en_partida)
    establecer_contexto(
        ContextoPantalla(
            titulo=titulo_ui("PAUSA"),
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


def _gestionar_pausa(*, en_partida: bool) -> None:
    """Primer Esc abre pausa; segundo Esc en pausa o opcion 3 = salir del juego."""
    accion = menu_pausa(en_partida=en_partida)
    if accion == AccionPausa.CONTINUAR:
        if en_partida:
            limpiar_consola()
        reimprimir_contexto()
        return
    if accion == AccionPausa.PANTALLA_TITULO:
        raise IrMenuPrincipal()


def leer_linea(
    mensaje: str,
    *,
    permitir_atras: bool = False,
    en_partida: bool = False,
    mayusculas: bool = False,
) -> str:
    """Lee una linea; en Windows tecla a tecla (Esc = atras o pausa segun contexto)."""
    if sys.platform == "win32":
        from .entrada_menu import leer_linea_teclado

        return leer_linea_teclado(
            mensaje,
            permitir_atras=permitir_atras,
            en_partida=en_partida,
            mayusculas=mayusculas,
        )

    from .entrada_menu import ContextoEntrada, _formatear_prompt, establecer_contexto_entrada

    establecer_contexto_entrada(
        ContextoEntrada(
            tipo="texto",
            defecto="confirmar",
            permitir_atras=permitir_atras,
            en_partida=en_partida,
        )
    )
    prompt = _formatear_prompt(mensaje)
    while True:
        print()
        try:
            texto = _input_seguro(prompt).strip()
        except SalirPrograma:
            raise
        return texto.upper() if mayusculas else texto


class AsistentePasos:
    """
    Asistente lineal con pasos adelante y atras (Supr = paso anterior).
    El primer paso no puede ir mas atras -> excepcion configurada (p. ej. IrMenuPrincipal).
    """

    def __init__(
        self,
        titulo: str,
        *,
        excepcion_paso1_atras: type[Exception] = IrMenuPrincipal,
        mensaje_paso1_atras: str = "<- Menu principal",
    ) -> None:
        self.titulo = titulo_ui(titulo)
        self.datos: dict = {}
        self._indice = 0
        self._pasos: list[tuple[str, Callable[["AsistentePasos"], None]]] = []
        self._excepcion_paso1_atras = excepcion_paso1_atras
        self._mensaje_paso1_atras = mensaje_paso1_atras

    def _reimprimir_paso(self) -> None:
        if self._indice >= len(self._pasos):
            return
        nombre, _ = self._pasos[self._indice]
        total = len(self._pasos)
        print(
            f"\n--- {self.titulo}: paso {self._indice + 1}/{total} — {nombre_paso(nombre)} ---"
        )

    def _registrar_contexto_paso(self) -> None:
        if self._indice >= len(self._pasos):
            return
        nombre, _ = self._pasos[self._indice]
        total = len(self._pasos)
        establecer_contexto(
            ContextoPantalla(
                titulo=(
                    f"{self.titulo} — paso {self._indice + 1}/{total}: "
                    f"{nombre_paso(nombre)}"
                ),
                lineas=[
                    "Menus: numeros o Enter · Supr = atras (paso 1 = menu principal)",
                    "Texto: Supr/Retroceso borra · Esc = atras (o pausa) · Ctrl+C = cerrar",
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
                    print(con_emoji("<- Paso anterior", "⬅️"))
                    continue
                print(self._mensaje_paso1_atras)
                raise self._excepcion_paso1_atras() from None
            except (IrMenuPrincipal, SalirPrograma):
                raise
            except Exception as exc:
                print(f"\n[!] No se pudo completar este paso: {exc}")
                print("    Revisa la entrada o pulsa Supr para retroceder.")
                continue
            self._indice += 1
        establecer_contexto(None)
