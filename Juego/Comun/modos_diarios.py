#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modos diarios: atajos del examen del día y aleatorio (preset ``examen_fijo``)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from Comun.config_historia import ConfigPresetHistoria
from Comun.semillas import (
    formatear_semilla_diaria,
    semilla_diaria,
    semilla_partida_aleatoria,
)

__all__ = [
    "ID_PRESET_EXAMEN_FIJO",
    "MATERIAS_EXAMEN_BALANCEADO",
    "MATERIAS_EXAMEN_DIA",
    "PREGUNTAS_EXAMEN_BALANCEADO",
    "PREGUNTAS_EXAMEN_DIA",
    "PREGUNTAS_POR_MATERIA_BALANCEADO",
    "PREGUNTAS_POR_MATERIA_DIA",
    "config_atajo_aleatorio",
    "config_atajo_diario",
    "config_atajo_semilla",
    "contenido_estable_examen_fijo",
    "es_id_examen_fijo",
    "etiqueta_fecha_examen_dia",
    "formatear_semilla_diaria",
    "orden_preguntas_examen_fijo",
    "origen_semilla_desde_config",
    "prioridad_orden_preset",
    "semilla_aleatoria_examen",
    "semilla_contenido_examen_fijo",
    "semilla_defecto_examen_fijo",
    "semilla_diaria",
    "semilla_examen_dia",
]

# --- Plantilla examen balanceado 4×6 ---
MATERIAS_EXAMEN_BALANCEADO = 4
PREGUNTAS_POR_MATERIA_BALANCEADO = 6
PREGUNTAS_EXAMEN_BALANCEADO = MATERIAS_EXAMEN_BALANCEADO * PREGUNTAS_POR_MATERIA_BALANCEADO

MATERIAS_EXAMEN_DIA = MATERIAS_EXAMEN_BALANCEADO
PREGUNTAS_POR_MATERIA_DIA = PREGUNTAS_POR_MATERIA_BALANCEADO
PREGUNTAS_EXAMEN_DIA = PREGUNTAS_EXAMEN_BALANCEADO

ID_PRESET_EXAMEN_FIJO = "examen_fijo"
_ORIGEN_SEMILLA_VALIDOS = frozenset({"diario", "aleatorio", "semilla"})


def _etiqueta_fecha(d: date | None = None) -> str:
    d = d or datetime.now(timezone.utc).date()
    return d.strftime("%d/%m/%Y")


def semilla_examen_dia(d: date | None = None) -> int:
    return semilla_diaria(d)


def etiqueta_fecha_examen_dia(d: date | None = None) -> str:
    return _etiqueta_fecha(d)


def semilla_aleatoria_examen() -> int:
    return semilla_partida_aleatoria()


def prioridad_orden_preset(preset_id: str) -> int:
    del preset_id
    return 1


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


def config_atajo_semilla(semilla: int | None = None) -> ConfigPresetHistoria:
    return ConfigPresetHistoria(
        valores={
            "origen_semilla": "semilla",
            "semilla": semilla if semilla is not None else semilla_defecto_examen_fijo(),
        }
    )
