#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atajo de consola a examen del día y reto del día."""

from __future__ import annotations

from pathlib import Path

from Comun.modelos import Pregunta
from Comun.examen_dia_historia import ID_PRESET_EXAMEN_DIA, etiqueta_fecha_examen_dia
from Comun.modos_diarios import ID_PRESET_RETO_DIA
from Comun.presets_historia import buscar_preset
from Comun.reto_dia_resistencia import etiqueta_fecha_reto_dia
from Consola.consola import pedir_menu_numerado
from Consola.modo_especiales import jugar_modos_especiales
from Consola.modo_historia import jugar_modo_historia
from Consola.navegacion import (
    AsistentePasos,
    IrMenuPrincipal,
    SalirPrograma,
    mostrar_transicion,
)
from Consola.textos_consola import banner, campo, con_emoji


def jugar_modos_diarios(
    preguntas: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
    *,
    path_plantillas: Path | None = None,
    path_preguntas_csv: Path | None = None,
) -> bool:
    def _pantalla_intro() -> None:
        print(f"\n{banner('RETOS DEL DÍA')}")
        print(
            con_emoji(
                f"Examen ({etiqueta_fecha_examen_dia()}) y reto "
                f"({etiqueta_fecha_reto_dia()}): misma secuencia para todos hoy.",
                "📅",
            )
        )

    mostrar_transicion(_pantalla_intro)

    try:
        buscar_preset(ID_PRESET_EXAMEN_DIA)
        buscar_preset(ID_PRESET_RETO_DIA)
    except KeyError as e:
        print(f"\nNo se encontró un modo diario: {e}")
        return False

    def paso_modo(asist: AsistentePasos) -> None:
        idx = pedir_menu_numerado(
            campo("reto_diario", "Reto del día"),
            [
                (ID_PRESET_EXAMEN_DIA, "Examen del día (historia, examen cerrado)"),
                (ID_PRESET_RETO_DIA, "Reto del día (resistencia, ranking diario)"),
            ],
            defecto=1,
        )
        asist.datos["modo"] = idx

    asistente = AsistentePasos("Retos del día")
    try:
        asistente.ejecutar([("Modo", paso_modo)])
    except IrMenuPrincipal:
        return False
    except SalirPrograma:
        raise

    if asistente.datos["modo"] == 1:
        return jugar_modo_historia(
            preguntas,
            materias_meta,
            preset_id_fijo=ID_PRESET_EXAMEN_DIA,
        )
    return jugar_modos_especiales(
        preguntas,
        materias_meta,
        preset_id_fijo=ID_PRESET_RETO_DIA,
        path_plantillas=path_plantillas,
        path_preguntas_csv=path_preguntas_csv,
    )
