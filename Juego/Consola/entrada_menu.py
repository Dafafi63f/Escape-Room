#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lectura de teclas en menus (Windows: tecla a tecla).

  Enter     -> primera opcion (1 en menus; A en pregunta)
  1-9       -> opcion del menu; en pregunta ignorados (solo A-D)
  Supr      -> atras (menu principal: cierra juego); en pausa = continuar; en pregunta: ignorada
  Ctrl+C    -> pausa (en pausa: salir del programa)
  A-D       -> respuesta en pregunta; fuera del examen, ignoradas
  S/N       -> solo en menus Si/No; fuera, ignoradas
  Resto     -> ignorado (sin mensaje)
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from enum import Enum

_LETRAS_RESPUESTA = frozenset({"A", "B", "C", "D"})
_LETRAS_SN = frozenset({"S", "N"})


def _es_menu_si_no(validas: set[str]) -> bool:
    return bool(validas) and validas <= _LETRAS_SN


class TipoTecla(str, Enum):
    ENTER = "enter"
    DIGITO = "digito"
    LETRA = "letra"
    SUPR = "supr"
    CTRL_C = "ctrl_c"
    IGNORAR = "ignorar"


class _EventoTecla:
    __slots__ = ("tipo", "valor")

    def __init__(self, tipo: TipoTecla, valor: str = "") -> None:
        self.tipo = tipo
        self.valor = valor


def hint_controles_menu(
    *,
    defecto: int | str | None = 1,
    permitir_atras: bool = False,
    en_pausa: bool = False,
    es_menu_principal: bool = False,
    en_partida: bool = False,
    menu_si_no: bool = False,
) -> str:
    partes = [f"Enter={defecto}"]
    if menu_si_no:
        partes.append("S/N=Si/No")
    if es_menu_principal:
        partes.append("Supr=salir")
    elif en_pausa:
        partes.append("Supr=continuar")
        partes.append("Ctrl+C=salir")
    else:
        if not en_partida:
            partes.append("Supr=atras")
        partes.append("Ctrl+C=pausa")
    return " [" + " · ".join(partes) + "]"


def _leer_tecla_windows(*, en_pausa: bool) -> _EventoTecla:
    import msvcrt

    b = msvcrt.getch()
    if b == b"\x03":
        return _EventoTecla(TipoTecla.CTRL_C)
    if b in (b"\r", b"\n"):
        return _EventoTecla(TipoTecla.ENTER)
    if b in (b"\x7f", b"\x08"):
        return _EventoTecla(TipoTecla.SUPR)
    if b in (b"\x00", b"\xe0"):
        b2 = msvcrt.getch()
        if b2 == b"S":
            return _EventoTecla(TipoTecla.SUPR)
        return _EventoTecla(TipoTecla.IGNORAR)

    try:
        c = b.decode("utf-8", errors="ignore")
    except Exception:
        return _EventoTecla(TipoTecla.IGNORAR)

    if not c:
        return _EventoTecla(TipoTecla.IGNORAR)

    if c.isdigit():
        return _EventoTecla(TipoTecla.DIGITO, c)
    if c.isalpha():
        return _EventoTecla(TipoTecla.LETRA, c.upper())
    return _EventoTecla(TipoTecla.IGNORAR)


def _leer_tecla_fallback() -> _EventoTecla:
    """Entornos sin msvcrt: una linea; Enter vacio = ENTER."""
    try:
        linea = input().strip()
    except EOFError:
        from .navegacion import SalirPrograma

        raise SalirPrograma() from None
    if linea == "":
        return _EventoTecla(TipoTecla.ENTER)
    if linea.isdigit() and len(linea) == 1:
        return _EventoTecla(TipoTecla.DIGITO, linea)
    if len(linea) == 1 and linea.isalpha():
        return _EventoTecla(TipoTecla.LETRA, linea.upper())
    return _EventoTecla(TipoTecla.IGNORAR)


def leer_tecla(*, en_pausa: bool = False) -> _EventoTecla:
    if sys.platform == "win32":
        return _leer_tecla_windows(en_pausa=en_pausa)
    return _leer_tecla_fallback()


def _procesar_tecla(
    ev: _EventoTecla,
    *,
    en_pausa: bool,
    permitir_atras: bool,
    es_menu_principal: bool = False,
    en_partida: bool = False,
    menu_si_no: bool = False,
) -> _EventoTecla | None:
    from .navegacion import IrMenuPrincipal, SalirPrograma, VolverAtras

    if ev.tipo == TipoTecla.CTRL_C:
        if en_pausa:
            raise SalirPrograma() from None
        raise KeyboardInterrupt

    if ev.tipo == TipoTecla.SUPR:
        if en_pausa:
            return _EventoTecla(TipoTecla.ENTER)
        if en_partida:
            return None
        if es_menu_principal:
            raise SalirPrograma() from None
        if permitir_atras:
            raise VolverAtras()
        raise IrMenuPrincipal() from None

    if ev.tipo == TipoTecla.LETRA:
        if not en_partida and ev.valor in _LETRAS_RESPUESTA:
            return None
        if ev.valor in _LETRAS_SN and not menu_si_no:
            return None
        return ev

    if ev.tipo == TipoTecla.DIGITO and en_partida:
        return None

    if ev.tipo == TipoTecla.IGNORAR:
        return None
    if ev.tipo in (TipoTecla.ENTER, TipoTecla.DIGITO):
        return ev
    return None


def esperar_tecla_menu(
    prompt: str,
    *,
    defecto: int | str = 1,
    permitir_atras: bool = False,
    en_partida: bool = False,
    en_pausa: bool = False,
    es_menu_principal: bool = False,
    menu_si_no: bool = False,
    validar: Callable[[_EventoTecla], bool] | None = None,
) -> _EventoTecla:
    """Bucle hasta tecla valida; las ignoradas refrescan pantalla sin mensajes."""
    from .navegacion import SalirPrograma, _gestionar_pausa, refrescar_pantalla_activa

    hint = hint_controles_menu(
        defecto=defecto,
        permitir_atras=permitir_atras,
        en_pausa=en_pausa,
        es_menu_principal=es_menu_principal,
        en_partida=en_partida,
        menu_si_no=menu_si_no,
    )
    linea_prompt = f"{prompt.rstrip()}{hint}"

    while True:
        print(linea_prompt, end="", flush=True)
        try:
            ev = leer_tecla(en_pausa=en_pausa)
        except EOFError:
            raise SalirPrograma() from None
        try:
            res = _procesar_tecla(
                ev,
                en_pausa=en_pausa,
                permitir_atras=permitir_atras,
                es_menu_principal=es_menu_principal,
                en_partida=en_partida,
                menu_si_no=menu_si_no,
            )
        except KeyboardInterrupt:
            if en_pausa:
                raise
            _gestionar_pausa(en_partida=en_partida)
            if not en_partida:
                refrescar_pantalla_activa()
            continue
        if res is None or (validar is not None and not validar(res)):
            refrescar_pantalla_activa()
            continue
        print()
        return res


def elegir_indice_menu(
    num_opciones: int,
    *,
    defecto: int = 1,
    permitir_cero: bool = False,
    permitir_atras: bool = False,
    en_partida: bool = False,
    prompt: str = "Selecciona",
    en_pausa: bool = False,
    es_menu_principal: bool = False,
) -> int:
    """Devuelve indice 1-based (o 0 si permitir_cero)."""

    def _validar(ev: _EventoTecla) -> bool:
        if ev.tipo == TipoTecla.ENTER:
            return True
        if ev.tipo == TipoTecla.DIGITO:
            n = int(ev.valor)
            if permitir_cero and n == 0:
                return True
            return 1 <= n <= num_opciones
        return False

    ev = esperar_tecla_menu(
        prompt,
        defecto=defecto,
        permitir_atras=permitir_atras,
        en_partida=en_partida,
        en_pausa=en_pausa,
        es_menu_principal=es_menu_principal,
        validar=_validar,
    )
    if ev.tipo == TipoTecla.ENTER:
        return 0 if permitir_cero and defecto == 0 else defecto
    return int(ev.valor)


def elegir_letra_menu(
    validas: set[str],
    *,
    defecto: str,
    permitir_atras: bool = False,
    en_partida: bool = False,
    prompt: str = "Selecciona",
    es_menu_principal: bool = False,
) -> str:
    """Letras validas (A-D en pregunta; S/N solo en menus Si/No)."""
    menu_si_no = _es_menu_si_no(validas)
    validas_set = set(validas)

    def _validar(ev: _EventoTecla) -> bool:
        if ev.tipo == TipoTecla.ENTER:
            return True
        return ev.tipo == TipoTecla.LETRA and ev.valor in validas_set

    ev = esperar_tecla_menu(
        prompt,
        defecto=defecto,
        permitir_atras=permitir_atras,
        en_partida=en_partida,
        es_menu_principal=es_menu_principal,
        menu_si_no=menu_si_no,
        validar=_validar,
    )
    if ev.tipo == TipoTecla.ENTER:
        return defecto
    return ev.valor
