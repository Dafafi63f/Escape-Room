#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades del modo historia en la interfaz gráfica."""

from __future__ import annotations

from typing import TYPE_CHECKING

from Comun.config_historia import ConfigPresetHistoria, validar_config
from Comun.datos import cargar_orden_materias, cargar_plantillas_materia
from Comun.presets_historia import (
    PresetHistoria,
    aplicar_preset,
    argumentos_generador,
    cargar_presets_historia,
    config_defecto,
    resolver_orden_preguntas,
)
from Comun.reglas import ReglasPartida
from Comun.semillas import resolver_semillas_partida
from Comun.rutas import resolver_presets
from Comun.generador_examen_historia import (
    PlanExamen,
    cargar_estadisticas_historicas,
    generar_examen,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego


def orden_materias_juego(datos: DatosJuego) -> list[str]:
    """Orden curricular si hay listado; si no, claves del meta inferido del CSV."""
    if datos.perfil.tiene_listado_materias and datos.path_listado_materias is not None:
        try:
            return cargar_orden_materias(datos.path_listado_materias)
        except FileNotFoundError:
            pass
    return sorted(datos.materias_meta.keys())


def cargar_catalogo_historia(perfil=None) -> list[PresetHistoria]:
    return cargar_presets_historia(resolver_presets(), perfil=perfil)


def _kwargs_generador_examen(
    datos: DatosJuego,
    preset: PresetHistoria,
    cfg: ConfigPresetHistoria,
) -> dict:
    kwargs = argumentos_generador(
        preset,
        cfg,
        materias_meta=datos.materias_meta,
        perfil_datos=datos.perfil,
    )
    if kwargs.get("usar_plantillas_materia"):
        materia = kwargs.get("materia_fija")
        if materia and datos.path_plantillas_json and datos.perfil.tiene_plantillas:
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
) -> tuple[PlanExamen, ReglasPartida]:
    orden = orden_materias_juego(datos)
    stats: dict = {}
    if datos.perfil.analisis_historico_disponible and datos.path_historico is not None:
        try:
            stats = cargar_estadisticas_historicas(
                datos.path_historico,
                materias_validas=set(datos.materias_meta),
            )
        except FileNotFoundError:
            stats = {}
    cfg = config or config_defecto(
        preset,
        materias_meta=datos.materias_meta,
        materias_orden=orden,
        perfil=datos.perfil,
        path_plantillas=datos.path_plantillas_json,
    )
    from Comun.config_historia import sanitizar_estrategia_config

    sanitizar_estrategia_config(cfg, datos.perfil)
    plantillas_materia = None
    if any(o.id == "n_preguntas" for o in preset.opciones):
        materia = cfg.get_str("materia")
        if materia and datos.path_plantillas_json and datos.perfil.tiene_plantillas:
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
    orden_preguntas = resolver_orden_preguntas(preset, cfg)
    semilla_partida = resolver_semillas_partida(
        preset_id=preset.id,
        cfg=cfg,
        semilla_override=semilla,
        orden_preguntas=orden_preguntas,
    )
    from Comun.modos_diarios import es_id_examen_fijo, origen_semilla_desde_config

    semilla_contenido = None
    if es_id_examen_fijo(preset.id) and origen_semilla_desde_config(cfg) == "diario":
        from Comun.modos_diarios import semilla_contenido_examen_fijo

        semilla_contenido = semilla_contenido_examen_fijo(cfg)
    plan = generar_examen(
        datos.preguntas,
        materias_orden=orden,
        materias_meta=datos.materias_meta,
        stats=stats,
        semilla=semilla_partida,
        semilla_contenido=semilla_contenido,
        **(_kwargs_generador_examen(datos, preset, cfg)),
    )
    reglas = aplicar_preset(preset, cfg)
    return plan, reglas
