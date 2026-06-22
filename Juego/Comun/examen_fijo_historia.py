#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Examen fijo balanceado (4×6): contenido diario, aleatorio o semilla numérica."""

from __future__ import annotations

from Comun.config_historia import ConfigPresetHistoria
from Comun.examen_aleatorio_historia import semilla_aleatoria_examen
from Comun.examen_dia_historia import semilla_examen_dia

__all__ = [
    "ID_PRESET_EXAMEN_FIJO",
    "config_atajo_aleatorio",
    "config_atajo_diario",
    "contenido_estable_examen_fijo",
    "es_id_examen_fijo",
    "orden_preguntas_examen_fijo",
    "origen_semilla_desde_config",
    "semilla_contenido_examen_fijo",
    "semilla_defecto_examen_fijo",
]

ID_PRESET_EXAMEN_FIJO = "examen_fijo"
_ORIGEN_SEMILLA_VALIDOS = frozenset({"diario", "aleatorio", "semilla"})


def es_id_examen_fijo(preset_id: str) -> bool:
    return preset_id == ID_PRESET_EXAMEN_FIJO


def semilla_defecto_examen_fijo() -> int:
    return semilla_examen_dia()


def origen_semilla_desde_config(cfg: ConfigPresetHistoria) -> str:
    raw = cfg.get_str("origen_semilla") or "diario"
    if raw not in _ORIGEN_SEMILLA_VALIDOS:
        return "diario"
    return raw


def semilla_contenido_examen_fijo(cfg: ConfigPresetHistoria) -> int:
    origen = origen_semilla_desde_config(cfg)
    if origen == "diario":
        return semilla_examen_dia()
    if origen == "aleatorio":
        return semilla_aleatoria_examen()
    return cfg.get_int("semilla", semilla_defecto_examen_fijo())


def orden_preguntas_examen_fijo(cfg: ConfigPresetHistoria) -> str:
    if origen_semilla_desde_config(cfg) == "diario":
        return "variar"
    return "dificultad"


def contenido_estable_examen_fijo(cfg: ConfigPresetHistoria) -> bool:
    return origen_semilla_desde_config(cfg) != "aleatorio"


def config_atajo_diario() -> ConfigPresetHistoria:
    return ConfigPresetHistoria(valores={"origen_semilla": "diario"})


def config_atajo_aleatorio() -> ConfigPresetHistoria:
    return ConfigPresetHistoria(valores={"origen_semilla": "aleatorio"})
