#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arranque de partidas por preset (historia, resistencia, escape room…)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from Comun.config_historia import ConfigPresetHistoria
from Comun.escape_room import AjustesEscapeRoom, es_preset_escape_room
from Comun.navegacion_fin_partida import NavegacionFinPartida
from Comun.presets_historia import PresetHistoria, aplicar_preset
from Comun.resistencia_partida import construir_banco_resistencia, es_preset_resistencia

if TYPE_CHECKING:
    from Grafico.app import DatosJuego
    from Grafico.pantallas import Pantalla


def iniciar_pantalla_preset(
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
    """Devuelve la pantalla de partida según el preset (examen, resistencia o escape room)."""
    if es_preset_resistencia(preset):
        from Grafico.pantallas_historia import PartidaResistenciaHistoria

        banco = construir_banco_resistencia(
            datos.preguntas,
            datos.materias_meta,
            path_plantillas=datos.path_plantillas_json,
            path_preguntas_csv=datos.path_preguntas_csv,
        )
        pool = banco.pool_completo()
        if not pool:
            raise ValueError("No hay preguntas disponibles para el modo resistencia.")
        reglas = aplicar_preset(preset, config)
        return PartidaResistenciaHistoria(
            nombre=nombre,
            preset=preset,
            pool=pool,
            banco=banco,
            reglas=reglas,
            ir_a=ir_a,
            datos=datos,
            salir_app=salir_app,
            navegacion_fin=navegacion_fin,
        )

    if es_preset_escape_room(preset):
        from Comun.datos import cargar_preguntas
        from Comun.escape_partida import construir_pool_escape, materias_del_pool
        from Comun.escape_room import (
            AjustesEscapeRoom,
            config_escape_room,
            total_preguntas_escape,
        )
        from Comun.semillas import semilla_partida_aleatoria
        from Grafico.pantallas_modos import PartidaEscapeRoom

        ajustes = ajustes_escape or AjustesEscapeRoom()
        config_escape = config_escape_room(n_salas=ajustes.n_salas)
        pool = construir_pool_escape(
            cargar_preguntas(datos.path_preguntas_csv, datos.materias_meta),
            banco=ajustes.banco,
            path_csv=datos.path_preguntas_csv,
            path_plantillas=datos.path_plantillas_json,
            materias_meta=datos.materias_meta,
        )
        if not pool:
            raise ValueError("No hay preguntas disponibles para el escape room.")
        reglas = aplicar_preset(preset, None)
        semilla = semilla_partida_aleatoria()
        return PartidaEscapeRoom(
            nombre=nombre,
            preset=preset,
            config=config_escape,
            pool=pool,
            materias_pool=materias_del_pool(pool),
            reglas=reglas,
            semilla=semilla,
            total_previsto=total_preguntas_escape(config_escape),
            ir_a=ir_a,
            datos=datos,
            salir_app=salir_app,
            navegacion_fin=navegacion_fin,
        )

    from Grafico.modo_historia import preparar_partida_historia
    from Grafico.pantallas_historia import PartidaModoHistoria

    plan, reglas = preparar_partida_historia(datos, preset, config)
    if not plan.preguntas:
        raise ValueError("No se pudo generar el examen.")
    return PartidaModoHistoria(
        nombre=nombre,
        preset=preset,
        preguntas=plan.preguntas,
        materias_examen=plan.materias,
        reglas=reglas,
        ir_a=ir_a,
        datos=datos,
        salir_app=salir_app,
        config_historia=config,
        semilla_partida=plan.semilla_partida,
        rng_partida=plan.rng,
        navegacion_fin=navegacion_fin,
    )
