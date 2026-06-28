#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades gráficas compartidas para arrancar partidas por preset y navegación al fin de partida."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from Comun.config_historia import ConfigPresetHistoria
from Comun.motor_nucleo import NavegacionFinPartida
from Comun.presets_historia import PresetHistoria
from Grafico.arranque_partida import iniciar_pantalla_preset

if TYPE_CHECKING:
    from Comun.escape_room import AjustesEscapeRoom
    from Grafico.app import DatosJuego
    from Grafico.pantallas import Pantalla


def construir_navegacion_fin_partida(
    datos: DatosJuego,
    preset: PresetHistoria,
    config: ConfigPresetHistoria,
    nombre: str,
    ir_a: Callable[[Pantalla], None],
    salir_app: Callable[[], None],
    pantalla_configuracion: Callable[[], Pantalla],
) -> NavegacionFinPartida:
    """Repetir regenera la partida; configurar vuelve a la pantalla de ajustes previa."""
    nav: NavegacionFinPartida

    def repetir() -> Pantalla:
        return iniciar_pantalla_partida(
            datos,
            preset,
            config,
            nombre,
            ir_a,
            salir_app,
            navegacion_fin=nav,
        )

    nav = NavegacionFinPartida(
        repetir=repetir,
        configurar=pantalla_configuracion,
    )
    return nav


def iniciar_pantalla_partida(
    datos: DatosJuego,
    preset: PresetHistoria,
    config: ConfigPresetHistoria,
    nombre: str,
    ir_a: Callable[[Pantalla], None],
    salir_app: Callable[[], None],
    *,
    navegacion_fin: NavegacionFinPartida | None = None,
    ajustes_escape: AjustesEscapeRoom | None = None,
) -> Pantalla:
    return iniciar_pantalla_preset(
        datos,
        preset,
        config,
        nombre,
        ir_a,
        salir_app,
        navegacion_fin=navegacion_fin,
        ajustes_escape=ajustes_escape,
    )
