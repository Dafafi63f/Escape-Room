#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades del modo historia en la interfaz gráfica."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from Comun.config_historia import ConfigPresetHistoria, validar_config
from Comun.navegacion_fin_partida import NavegacionFinPartida
from Comun.datos import cargar_orden_materias, cargar_plantillas_materia
from Comun.presets_historia import (
    PresetHistoria,
    aplicar_preset,
    argumentos_generador,
    cargar_presets_historia,
    cargar_presets_especiales,
    config_defecto,
    contenido_examen_estable,
    resolver_orden_preguntas,
    semilla_desde_preset,
)
from Comun.reglas_partida import ReglasPartida
from Grafico.arranque_partida import iniciar_pantalla_preset
from Comun.rutas import PATH_MATERIAS, resolver_presets
from Comun.generador_examen_historia import (
    PlanExamen,
    cargar_estadisticas_historicas,
    generar_examen,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego
    from Grafico.pantallas import Pantalla


def cargar_catalogo_historia() -> list[PresetHistoria]:
    return cargar_presets_historia(resolver_presets())


def cargar_catalogo_especiales() -> list[PresetHistoria]:
    return cargar_presets_especiales(resolver_presets())


def _kwargs_generador_examen(
    datos: DatosJuego,
    preset: PresetHistoria,
    cfg: ConfigPresetHistoria,
) -> dict:
    kwargs = argumentos_generador(preset, cfg, materias_meta=datos.materias_meta)
    if kwargs.get("usar_plantillas_materia"):
        materia = kwargs.get("materia_fija")
        if materia:
            kwargs["plantillas_materia"] = cargar_plantillas_materia(
                datos.path_plantillas_json,
                materia,
            )
    return kwargs


def preparar_partida_historia(
    datos: DatosJuego,
    preset: PresetHistoria,
    config: ConfigPresetHistoria | None = None,
    *,
    semilla: int | None = None,
    semilla_orden: int | None = None,
) -> tuple[PlanExamen, ReglasPartida]:
    from Comun.modos_diarios import semilla_aleatoria_examen

    orden = cargar_orden_materias(PATH_MATERIAS)
    stats = cargar_estadisticas_historicas(materias_validas=set(datos.materias_meta))
    cfg = config or config_defecto(
        preset,
        materias_meta=datos.materias_meta,
        materias_orden=orden,
    )
    plantillas_materia = None
    if any(o.id == "n_preguntas" for o in preset.opciones):
        materia = cfg.get_str("materia")
        if materia:
            plantillas_materia = cargar_plantillas_materia(
                datos.path_plantillas_json,
                materia,
            )
    cfg = validar_config(
        preset.opciones,
        cfg,
        materias_meta=datos.materias_meta,
        preset_id=preset.id,
        plantillas_materia=plantillas_materia,
    )
    semilla_contenido = (
        semilla if semilla is not None else semilla_desde_preset(preset, cfg)
    )
    orden = resolver_orden_preguntas(preset, cfg)
    if (
        semilla_orden is None
        and orden == "variar"
        and contenido_examen_estable(preset, cfg=cfg, semilla=semilla)
    ):
        semilla_orden = semilla_aleatoria_examen()
    plan = generar_examen(
        datos.preguntas,
        materias_orden=orden,
        materias_meta=datos.materias_meta,
        stats=stats,
        semilla=semilla_contenido,
        semilla_orden=semilla_orden,
        **(_kwargs_generador_examen(datos, preset, cfg)),
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
    ajustes_escape: AjustesEscapeRoom | None = None,
) -> Pantalla:
    """Alias de compatibilidad; usar ``iniciar_pantalla_preset``."""
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
