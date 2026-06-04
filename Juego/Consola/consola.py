#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entrada por consola, puntuación y utilidades de dificultad."""

from __future__ import annotations

from collections.abc import Callable
from typing import Iterable

from .entrada_menu import elegir_indice_menu, elegir_letra_menu, hint_controles_menu
from .modelos import Pregunta
from .navegacion import (
    ContextoPantalla,
    IrMenuPrincipal,
    SalirPrograma,
    VolverAtras,
    establecer_contexto,
    leer_linea,
)

_ORDEN_DEFECTO_LETRAS = "ABCDSN"


def _activar_menu_consola(titulo: str, dibujar: Callable[[], None]) -> None:
    establecer_contexto(ContextoPantalla(titulo=titulo, reimprimir=dibujar))
    dibujar()


def _validas_son_digitos(validas: set[str]) -> bool:
    return bool(validas) and all(v.isdigit() for v in validas)


def _defecto_opcion(validas: Iterable[str], default: str | None) -> str:
    """Enter = primera opcion: 1 en menus numericos, A en ABCD, S antes que N, etc."""
    validas_set = {v.upper() for v in validas}
    if default:
        d = default.upper()
        if d in validas_set:
            return d
    if _validas_son_digitos(validas_set):
        return "1" if "1" in validas_set else str(min(int(v) for v in validas_set))
    for letra in _ORDEN_DEFECTO_LETRAS:
        if letra in validas_set:
            return letra
    return sorted(validas_set)[0]


def pedir_opcion(
    mensaje: str,
    validas: Iterable[str],
    default: str | None = None,
    *,
    permitir_atras: bool = False,
    en_partida: bool = False,
    es_menu_principal: bool = False,
) -> str:
    validas_set = {v.upper() for v in validas}
    default_up = _defecto_opcion(validas_set, default)

    if _validas_son_digitos(validas_set):
        enteros = sorted(int(v) for v in validas_set)
        max_n = max(enteros)
        defecto = int(default_up) if default_up.isdigit() else enteros[0]
        idx = elegir_indice_menu(
            max_n,
            defecto=defecto,
            permitir_cero=0 in enteros,
            permitir_atras=permitir_atras,
            en_partida=en_partida,
            prompt=mensaje,
            es_menu_principal=es_menu_principal,
        )
        return str(idx)

    return elegir_letra_menu(
        validas_set,
        defecto=default_up,
        permitir_atras=permitir_atras,
        en_partida=en_partida,
        prompt=mensaje,
        es_menu_principal=es_menu_principal,
    )


def pedir_texto(
    mensaje: str,
    *,
    default: str = "",
    permitir_atras: bool = False,
    en_partida: bool = False,
) -> str:
    try:
        valor = leer_linea(
            mensaje,
            permitir_atras=permitir_atras,
            en_partida=en_partida,
            mayusculas=False,
        )
    except (VolverAtras, IrMenuPrincipal, SalirPrograma):
        raise
    return valor if valor else default


def elegir_filtro(
    nombre: str,
    valores: list[str],
    *,
    permitir_atras: bool = True,
) -> str | None:
    valores = list(dict.fromkeys(v for v in valores if v))

    def _dibujar() -> None:
        print(f"\nFiltrar por {nombre}:")
        print("0) Todos (por defecto)")
        for i, valor in enumerate(valores, start=1):
            print(f"{i}) {valor}")

    _activar_menu_consola(f"Filtrar por {nombre}", _dibujar)

    idx = elegir_indice_menu(
        len(valores),
        defecto=0,
        permitir_cero=True,
        permitir_atras=permitir_atras,
        prompt="Selecciona",
    )
    if idx == 0:
        return None
    return valores[idx - 1]


def elegir_filtro_obligatorio(
    nombre: str,
    valores: list[str],
    *,
    permitir_atras: bool = True,
) -> str:
    valores = list(dict.fromkeys(v for v in valores if v))
    if not valores:
        print(f"No hay valores disponibles para «{nombre}». Pulsa Supr para retroceder.")
        raise VolverAtras()

    def _dibujar() -> None:
        print(f"\nFiltrar por {nombre}:")
        for i, valor in enumerate(valores, start=1):
            etiqueta = " (por defecto)" if i == 1 else ""
            print(f"{i}) {valor}{etiqueta}")

    _activar_menu_consola(f"Filtrar por {nombre}", _dibujar)

    idx = elegir_indice_menu(
        len(valores),
        defecto=1,
        permitir_atras=permitir_atras,
        prompt="Selecciona",
    )
    return valores[idx - 1]


def pedir_entero_en_rango(
    mensaje: str,
    minimo: int,
    maximo: int,
    defecto: int,
    *,
    permitir_atras: bool = True,
) -> int:
    if maximo < minimo:
        maximo = minimo
    defecto = max(minimo, min(defecto, maximo))
    print(hint_controles_menu(defecto=defecto, permitir_atras=permitir_atras))
    while True:
        try:
            entrada = leer_linea(mensaje, permitir_atras=permitir_atras)
        except VolverAtras:
            raise
        except (IrMenuPrincipal, SalirPrograma):
            raise
        if not entrada:
            return defecto
        if entrada.isdigit():
            valor = int(entrada)
            if minimo <= valor <= maximo:
                return valor


def pedir_menu_numerado(
    titulo: str,
    opciones: list[tuple[str, str]],
    *,
    defecto: int = 1,
    permitir_atras: bool = True,
) -> int:
    """Muestra opciones numeradas y devuelve el índice elegido (1-based)."""

    def _dibujar() -> None:
        print(f"\n{titulo}")
        for i, (_clave, desc) in enumerate(opciones, start=1):
            marca = " (por defecto)" if i == defecto else ""
            print(f"  {i}) {desc}{marca}")

    _activar_menu_consola(titulo, _dibujar)

    return elegir_indice_menu(
        len(opciones),
        defecto=defecto,
        permitir_atras=permitir_atras,
        prompt="Selecciona",
    )


def calcular_puntos(dificultad: str, acierto: bool) -> int:
    from .reglas_partida import calcular_puntos_arcade

    return calcular_puntos_arcade(dificultad, acierto)


def dificultad_base(dificultad: str) -> int:
    return {"Facil": 1, "Media": 2, "Dificil": 3}.get(dificultad, 2)


def nivel_materia(nivel: str) -> int:
    try:
        return max(1, int(nivel))
    except (TypeError, ValueError):
        return 1


def complejidad_pregunta(pregunta: Pregunta) -> int:
    return nivel_materia(pregunta.nivel) + dificultad_base(pregunta.dificultad) - 1


def dificultad_global_actual(
    respondidas: int,
    global_inicial: int,
    max_global: int,
    cada_n: int = 40,
) -> int:
    subida = respondidas // max(1, cada_n)
    return min(global_inicial + subida, max_global)
