#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades del modo historia en la interfaz gráfica."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from Comun.config_historia import ConfigPresetHistoria, validar_config
from Comun.navegacion_fin_partida import NavegacionFinPartida
from Comun.datos import cargar_orden_materias
from Comun.presets_historia import (
    PresetHistoria,
    aplicar_preset,
    argumentos_generador,
    cargar_presets_historia,
    cargar_presets_especiales,
    config_defecto,
    semilla_desde_preset,
)
from Comun.reglas_partida import ReglasPartida
from Comun.resistencia_historia import construir_banco_resistencia, es_preset_resistencia
from Comun.rutas import PATH_MATERIAS, resolver_presets_especiales, resolver_presets_historia
from Consola.generador_examen_historia import (
    PlanExamen,
    cargar_estadisticas_historicas,
    generar_examen,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego
    from Grafico.pantallas import Pantalla


def cargar_catalogo_historia() -> list[PresetHistoria]:
    return cargar_presets_historia(resolver_presets_historia())


def cargar_catalogo_especiales() -> list[PresetHistoria]:
    return cargar_presets_especiales(resolver_presets_especiales())


def preparar_partida_historia(
    datos: DatosJuego,
    preset: PresetHistoria,
    config: ConfigPresetHistoria | None = None,
    *,
    semilla: int | None = None,
) -> tuple[PlanExamen, ReglasPartida]:
    orden = cargar_orden_materias(PATH_MATERIAS)
    stats = cargar_estadisticas_historicas(materias_validas=set(datos.materias_meta))
    cfg = config or config_defecto(
        preset,
        materias_meta=datos.materias_meta,
        materias_orden=orden,
    )
    cfg = validar_config(preset.opciones, cfg, materias_meta=datos.materias_meta)
    plan = generar_examen(
        datos.preguntas,
        materias_orden=orden,
        materias_meta=datos.materias_meta,
        stats=stats,
        semilla=semilla if semilla is not None else semilla_desde_preset(preset),
        **argumentos_generador(preset, cfg, materias_meta=datos.materias_meta),
    )
    reglas = aplicar_preset(preset, cfg)
    return plan, reglas


def construir_navegacion_fin_partida_historia(
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
        return iniciar_pantalla_partida_historia(
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


def iniciar_pantalla_partida_historia(
    datos: DatosJuego,
    preset: PresetHistoria,
    config: ConfigPresetHistoria,
    nombre: str,
    ir_a: Callable[[Pantalla], None],
    salir_app: Callable[[], None],
    *,
    navegacion_fin: NavegacionFinPartida | None = None,
) -> Pantalla:
    """Devuelve la pantalla de partida adecuada (examen fijo o resistencia)."""
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
        navegacion_fin=navegacion_fin,
    )
