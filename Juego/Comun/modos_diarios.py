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
    "semilla_seleccion_examen_fijo",
    "lineas_semillas_fin_examen_fijo",
    "titulo_fin_partida_historia",
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


_ETIQUETAS_FIN_EXAMEN_FIJO = {
    "diario": "Examen diario",
    "aleatorio": "Examen aleatorio",
    "semilla": "Examen fijo",
}


def semilla_seleccion_examen_fijo(
    cfg: ConfigPresetHistoria,
    *,
    semilla_partida: int = 0,
) -> int:
    """Semilla que fija el contenido del examen (reproducible)."""
    origen = origen_semilla_desde_config(cfg)
    if origen == "diario":
        return semilla_examen_dia()
    if origen == "semilla":
        return cfg.get_int("semilla", semilla_defecto_examen_fijo())
    return semilla_partida


def titulo_fin_examen_fijo(
    cfg: ConfigPresetHistoria,
    *,
    abandonado: bool = False,
    semilla_partida: int = 0,
    max_len: int | None = None,
) -> str:
    """Título de fin/abandono según diario, aleatorio o semilla fija (sin semillas en cabecera)."""
    del semilla_partida
    origen = origen_semilla_desde_config(cfg)
    modo = _ETIQUETAS_FIN_EXAMEN_FIJO.get(origen, "Examen fijo")
    prefijo = "ABANDONO" if abandonado else "FIN"
    titulo = f"{prefijo} — {modo}"
    if max_len is not None:
        titulo = titulo[:max_len]
    return titulo


def lineas_semillas_fin_examen_fijo(
    cfg: ConfigPresetHistoria,
    *,
    semilla_partida: int = 0,
    semilla_contenido: int = 0,
) -> list[str]:
    """Líneas de metadatos bajo «Jugador» en el resumen del examen fijo."""
    sel = semilla_contenido or semilla_seleccion_examen_fijo(
        cfg, semilla_partida=semilla_partida
    )
    if not sel:
        return []
    lineas = [f"Semilla contenido: {formatear_semilla_diaria(sel)}"]
    if semilla_partida and semilla_partida != sel:
        lineas.append(f"Semilla orden: {formatear_semilla_diaria(semilla_partida)}")
    return lineas


def titulo_fin_partida_historia(
    preset_id: str,
    preset_nombre: str,
    cfg: ConfigPresetHistoria,
    *,
    abandonado: bool = False,
    semilla_partida: int = 0,
    max_len: int | None = None,
) -> str:
    """Título de resumen para presets historia; examen fijo distingue diario/aleatorio/fijo."""
    if es_id_examen_fijo(preset_id):
        return titulo_fin_examen_fijo(
            cfg,
            abandonado=abandonado,
            semilla_partida=semilla_partida,
            max_len=max_len,
        )
    prefijo = "ABANDONO" if abandonado else "FIN"
    limite = 40 if abandonado else 44
    if max_len is not None:
        limite = min(limite, max_len)
    titulo = f"{prefijo} — {preset_nombre[:limite]}"
    if max_len is not None:
        titulo = titulo[:max_len]
    return titulo
