#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Políticas de reglas: núcleo en ``Comun`` y resolución interactiva en consola."""

from __future__ import annotations

from Comun.configuracion_reglas_libre import alcance_para_contexto
from Comun.politica_reglas import (
    ContextoPartida,
    PoliticaReglas,
    clasificar_libre,
    politica_historia_reto,
    politica_historia_simulacro,
    validar_reglas,
)
from Comun.reglas_partida import ReglasPartida

from .configuracion_reglas_libre import configurar_reglas_personalizado
from .consola import pedir_menu_numerado
from Consola.textos_consola import campo, con_emoji

__all__ = [
    "ContextoPartida",
    "PoliticaReglas",
    "aplicar_politica",
    "clasificar_libre",
    "politica_historia_reto",
    "politica_historia_simulacro",
    "resolver_politica_historia",
    "resolver_politica_libre",
    "validar_reglas",
]


def resolver_politica_libre(*, modo_infinito: bool, n_preguntas: int) -> PoliticaReglas:
    ctx = clasificar_libre(modo_infinito=modo_infinito, n_preguntas=n_preguntas)
    alcance = alcance_para_contexto(ctx)
    titulo = alcance.titulo if alcance else ctx.value
    reglas = configurar_reglas_personalizado(
        ctx,
        modo_infinito=modo_infinito,
        n_preguntas=n_preguntas,
    )
    return PoliticaReglas(
        contexto=ctx,
        reglas=reglas,
        eleccion_jugador=True,
        mensaje=con_emoji(
            f"Modo libre — {titulo}: configura vidas, tiempo y puntuación.",
            "🎮",
        ),
    )


def resolver_politica_historia() -> PoliticaReglas:
    idx = pedir_menu_numerado(
        campo("tipo_partida", "Modo historia — reglas del creador"),
        [
            ("sim", "Simulacro de parcial [recomendado]"),
            ("reto", "Variante reto (vidas + arcade)"),
        ],
        defecto=1,
    )
    return politica_historia_simulacro() if idx == 1 else politica_historia_reto()


def aplicar_politica(politica: PoliticaReglas) -> ReglasPartida:
    print(f"\n>>> {politica.mensaje}")
    if not politica.eleccion_jugador:
        print(con_emoji("(Configuración fija para este tipo de partida.)", "🔒"))
    print(f">>> {politica.reglas.describe()}")
    return validar_reglas(politica.reglas, politica.contexto)
