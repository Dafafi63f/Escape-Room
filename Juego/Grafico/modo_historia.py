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
    generar_examen,
    resolver_stats_para_generador,
)

if TYPE_CHECKING:
    from Comun.cadena_examen_dirigido import CadenaExamenDirigido
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


def preparar_examen_dirigido_sesion(
    datos: DatosJuego,
    preset: PresetHistoria,
    config: ConfigPresetHistoria,
    registros_sesion: list,
    *,
    cadena: CadenaExamenDirigido | None = None,
    semilla: int | None = None,
) -> tuple[PlanExamen, ReglasPartida, CadenaExamenDirigido]:
    """Genera un examen nuevo con memoria acumulada de la cadena de dirigidos."""
    from Comun.cadena_examen_dirigido import (
        CadenaExamenDirigido,
        extender_cadena,
        perfiles_fallo_desde_registros,
    )
    from Comun.config_historia import sanitizar_estrategia_config
    from Comun.semillas import semilla_partida_aleatoria

    cadena_actualizada = extender_cadena(cadena, registros_sesion)
    registros_acum = list(cadena_actualizada.registros)
    if not registros_acum:
        raise ValueError("No hay respuestas en la sesión para orientar el examen.")

    orden = orden_materias_juego(datos)
    cfg = config
    sanitizar_estrategia_config(cfg, datos.perfil)
    perfiles = perfiles_fallo_desde_registros(registros_acum)
    kwargs = _kwargs_generador_examen(datos, preset, cfg)
    kwargs["usar_analisis_historico"] = False
    plantillas_materia = None
    if kwargs.get("usar_plantillas_materia"):
        materia = kwargs.get("materia_fija")
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
    kwargs["orden_preguntas"] = orden_preguntas
    preguntas_excluir = cadena_actualizada.preguntas_en_ventana_exclusion()
    preguntas_ultima = [r.pregunta for r in registros_sesion]

    plan: PlanExamen | None = None
    ultimo_error: str | None = None
    estrategias: tuple[tuple[list | None, dict | None, bool], ...] = (
        (preguntas_excluir, perfiles, False),
        (preguntas_excluir, None, True),
        (preguntas_ultima, None, True),
    )
    for excluir, perfiles_intento, nueva_semilla in estrategias:
        semilla_intento = (
            semilla_partida_aleatoria() if nueva_semilla or semilla is None else semilla
        )
        try:
            plan = generar_examen(
                datos.preguntas,
                materias_orden=orden,
                materias_meta=datos.materias_meta,
                stats={},
                semilla=semilla_intento,
                registros_dirigido=registros_acum,
                preguntas_excluir=excluir,
                perfiles_fallo=perfiles_intento,
                **kwargs,
            )
            break
        except ValueError as exc:
            ultimo_error = str(exc)

    if plan is None:
        raise ValueError(
            ultimo_error
            or "No se pudo montar otro examen dirigido con el banco disponible."
        )
    reglas = aplicar_preset(preset, cfg)
    return plan, reglas, cadena_actualizada


def preparar_partida_historia(
    datos: DatosJuego,
    preset: PresetHistoria,
    config: ConfigPresetHistoria | None = None,
    *,
    semilla: int | None = None,
    semilla_contenido: int | None = None,
) -> tuple[PlanExamen, ReglasPartida]:
    orden = orden_materias_juego(datos)
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
    from Comun.modos_diarios import (
        es_id_examen_fijo,
        origen_semilla_desde_config,
        semilla_contenido_examen_fijo,
    )
    from Comun.semillas import semilla_partida_aleatoria

    semilla_contenido_generador: int | None = semilla_contenido
    if semilla_contenido is not None:
        semilla_partida = (
            semilla if semilla is not None else semilla_partida_aleatoria()
        )
    else:
        semilla_partida = resolver_semillas_partida(
            preset_id=preset.id,
            cfg=cfg,
            semilla_override=semilla,
            orden_preguntas=orden_preguntas,
        )
        if es_id_examen_fijo(preset.id):
            origen = origen_semilla_desde_config(cfg)
            if origen in ("diario", "semilla"):
                semilla_contenido_generador = semilla_contenido_examen_fijo(cfg)
    stats = resolver_stats_para_generador(
        preset=preset,
        cfg=cfg,
        perfil=datos.perfil,
        materias_meta=datos.materias_meta,
    )
    plan = generar_examen(
        datos.preguntas,
        materias_orden=orden,
        materias_meta=datos.materias_meta,
        stats=stats,
        semilla=semilla_partida,
        semilla_contenido=semilla_contenido_generador,
        **(_kwargs_generador_examen(datos, preset, cfg)),
    )
    reglas = aplicar_preset(preset, cfg)
    return plan, reglas
