#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Asistente de consola para opciones configurables del modo historia."""

from __future__ import annotations

from Comun.config_historia import (
    GRUPOS_TEMATICOS,
    ConfigPresetHistoria,
    OpcionPreset,
    cursos_disponibles,
    semestres_para_curso,
    validar_config,
)
from Comun.presets_historia import PresetHistoria, config_defecto
from Consola.consola import pedir_entero_en_rango, pedir_menu_numerado, pedir_opcion


def pedir_config_historia(
    preset: PresetHistoria,
    *,
    materias_meta: dict[str, dict[str, str]],
    materias_orden: list[str],
) -> ConfigPresetHistoria:
    if not preset.opciones:
        return ConfigPresetHistoria()

    config = config_defecto(
        preset,
        materias_meta=materias_meta,
        materias_orden=materias_orden,
    )
    valores = dict(config.valores)

    print(f"\n--- Opciones: {preset.nombre} ---")
    for op in preset.opciones:
        valores[op.id] = _pedir_opcion(op, valores, materias_meta, materias_orden)

    return validar_config(
        preset.opciones,
        ConfigPresetHistoria(valores=valores),
        materias_meta=materias_meta,
    )


def _pedir_opcion(
    op: OpcionPreset,
    valores: dict,
    materias_meta: dict[str, dict[str, str]],
    materias_orden: list[str],
) -> object:
    if op.tipo == "entero":
        defecto = int(op.defecto if op.defecto is not None else 0)
        min_v = op.min if op.min is not None else 0
        max_v = op.max if op.max is not None else 9999
        return pedir_entero_en_rango(
            f"{op.etiqueta} [{defecto}]: ",
            min_v,
            max_v,
            defecto,
        )
    if op.tipo == "curso":
        cursos = cursos_disponibles(materias_meta)
        if not cursos:
            raise ValueError("No hay cursos en los metadatos.")
        if not op.obligatorio:
            if pedir_opcion(f"{op.etiqueta} — ¿filtrar? (S/N): ", ["S", "N"], "N") == "N":
                return None
        idx = pedir_menu_numerado(
            op.etiqueta + ":",
            [(c, f"Curso {c}") for c in cursos],
            defecto=1,
        )
        return cursos[idx - 1]
    if op.tipo == "semestre":
        curso = valores.get("curso")
        if not curso:
            if op.obligatorio:
                raise ValueError("Indica el curso antes del semestre.")
            return None
        semestres = semestres_para_curso(materias_meta, str(curso))
        if not semestres:
            raise ValueError(f"No hay semestres para el curso {curso}.")
        idx = pedir_menu_numerado(
            op.etiqueta + ":",
            [(s, f"Semestre {s}") for s in semestres],
            defecto=1,
        )
        return semestres[idx - 1]
    if op.tipo == "grupo":
        items = list(GRUPOS_TEMATICOS.items())
        defecto_idx = 1
        if op.defecto:
            for i, (g, _) in enumerate(items, start=1):
                if g == str(op.defecto):
                    defecto_idx = i
                    break
        idx = pedir_menu_numerado(op.etiqueta + ":", items, defecto=defecto_idx)
        return items[idx - 1][0]
    if op.tipo == "materia":
        idx = pedir_menu_numerado(
            op.etiqueta + ":",
            [(m, m) for m in materias_orden],
            defecto=1,
        )
        return materias_orden[idx - 1]
    if op.tipo == "eleccion":
        items = list(op.valores)
        defecto_idx = 1
        for i, (v, _) in enumerate(items, start=1):
            if v == str(op.defecto):
                defecto_idx = i
                break
        idx = pedir_menu_numerado(op.etiqueta + ":", items, defecto=defecto_idx)
        return items[idx - 1][0]
    raise ValueError(f"Tipo de opción desconocido: {op.tipo}")
