#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modos especiales: resistencia y futuros retos fuera del catálogo de historia."""

from __future__ import annotations

from pathlib import Path

from Comun.config_historia import ConfigPresetHistoria
from Comun.jugador import NOMBRE_JUGADOR_DEFECTO
from Comun.modelos import Pregunta
from Comun.presets_historia import (
    PresetHistoria,
    cargar_presets_especiales,
    politica_desde_preset,
)
from Comun.rutas import resolver_presets_especiales
from Consola.consola import pedir_menu_numerado, pedir_texto
from Consola.entrada_menu import esperar_enter
from Consola.generador_examen_historia import cargar_estadisticas_historicas
from Consola.motor_resistencia import ejecutar_resistencia_historia
from Consola.navegacion import (
    AsistentePasos,
    IrMenuPrincipal,
    SalirPrograma,
    limpiar_consola,
    mostrar_transicion,
)
from Consola.politica_reglas import aplicar_politica
from Consola.textos_consola import banner, campo, con_emoji


def _elegir_preset(presets: list[PresetHistoria]) -> PresetHistoria:
    opciones = [(p.id, f"{p.nombre} — {p.descripcion}") for p in presets]
    idx = pedir_menu_numerado(
        campo("modo_especial", "Modo especial"),
        opciones,
        defecto=1,
    )
    return presets[idx - 1]


def jugar_modos_especiales(
    preguntas: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
    *,
    preset_id_fijo: str | None = None,
    path_plantillas: Path | None = None,
    path_preguntas_csv: Path | None = None,
) -> bool:
    def _pantalla_intro() -> None:
        print(f"\n{banner('MODOS ESPECIALES')}")
        print(
            con_emoji(
                "Partidas aparte del modo historia: de momento resistencia infinita y reto del día.",
                "⚡",
            )
        )

    mostrar_transicion(_pantalla_intro)

    try:
        presets = cargar_presets_especiales(resolver_presets_especiales())
    except (FileNotFoundError, ValueError) as e:
        print(f"\nNo se pudo cargar el catálogo de modos especiales: {e}")
        return False

    def paso_nombre(asist: AsistentePasos) -> None:
        asist.datos["nombre"] = pedir_texto(
            f"{campo('nombre', 'Nombre de jugador')}: ",
            default=NOMBRE_JUGADOR_DEFECTO,
            permitir_atras=True,
        )

    def paso_preset(asist: AsistentePasos) -> None:
        if preset_id_fijo:
            for preset in presets:
                if preset.id == preset_id_fijo:
                    asist.datos["preset"] = preset
                    return
            raise KeyError(f"Preset no encontrado: {preset_id_fijo!r}")
        asist.datos["preset"] = _elegir_preset(presets)

    def paso_reglas(asist: AsistentePasos) -> None:
        preset: PresetHistoria = asist.datos["preset"]
        config = ConfigPresetHistoria()
        politica = politica_desde_preset(preset, config)
        asist.datos["config"] = config
        asist.datos["reglas"] = aplicar_politica(politica)

    pasos = [
        ("Nombre", paso_nombre),
        ("Modo", paso_preset),
        ("Preparación", paso_reglas),
    ]

    asistente = AsistentePasos("Modos especiales")
    try:
        asistente.ejecutar(pasos)
    except IrMenuPrincipal:
        return False
    except SalirPrograma:
        raise

    nombre = asistente.datos["nombre"]
    preset: PresetHistoria = asistente.datos["preset"]
    reglas = asistente.datos["reglas"]
    stats = cargar_estadisticas_historicas(materias_validas=set(materias_meta))

    def _pantalla_resistencia() -> None:
        print(f"\n{banner('RESISTENCIA')}")
        print(f"{campo('modo_especial', 'Modo')}: {preset.nombre}")
        print(
            con_emoji(
                "Una falla corta la racha. La dificultad sube con el nº de pregunta.",
                "🔥",
            )
        )
        print(
            con_emoji(
                "Récords locales en este equipo (configurables desde el ranking gráfico).",
                "🏆",
            )
        )

    limpiar_consola()
    _pantalla_resistencia()
    esperar_enter("\nPulsa Enter para comenzar")
    try:
        ejecutar_resistencia_historia(
            preguntas,
            nombre=nombre,
            reglas=reglas,
            preset_id=preset.id,
            preset_nombre=preset.nombre,
            perfil=preset.perfil,
            materias_meta=materias_meta,
            stats_historicas=stats,
            path_plantillas=path_plantillas,
            path_preguntas_csv=path_preguntas_csv,
        )
    except SalirPrograma:
        raise
    return True
