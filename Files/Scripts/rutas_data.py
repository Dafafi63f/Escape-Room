#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rutas canónicas a ``Data/CSV`` y ``Data/JSON`` (scripts de mantenimiento)."""

from __future__ import annotations

from pathlib import Path

PROYECTO = Path(__file__).resolve().parents[2]
DATA = PROYECTO / "Data"
DATA_CSV = DATA / "CSV"
DATA_JSON = DATA / "JSON"

# Alias usado en scripts legacy
BASE = PROYECTO

_SUBDIRS_CSV = ("CSV", "csv")
_SUBDIRS_JSON = ("JSON", "json")


def _resolver(nombre: str, subdirs: tuple[str, ...]) -> Path:
    for subdir in subdirs:
        canon = DATA / subdir / nombre
        if canon.exists():
            return canon
    legado = DATA / nombre
    if legado.exists():
        return legado
    return DATA / subdirs[0] / nombre


def ruta_csv(nombre: str) -> Path:
    return _resolver(nombre, _SUBDIRS_CSV)


def ruta_json(nombre: str) -> Path:
    return _resolver(nombre, _SUBDIRS_JSON)


PATH_PREGUNTAS = ruta_csv("Preguntas.csv")
PATH_LISTADO_MATERIAS = ruta_csv("listado_materias.csv")
PATH_CRITERIOS_CLASIFICACION = ruta_csv("criterios_clasificacion_materia.csv")
PATH_HISTORICO_QUALIFICACIONS = ruta_csv("Historic_qualificacions_MatCAD_completo.csv")
PATH_PLANTILLAS = ruta_json("plantillas.json")
PATH_PRESETS_HISTORIA = ruta_json("presets_historia.json")
PATH_PREGUNTAS_RESISTENCIA = ruta_json("preguntas_resistencia.json")
PATH_RANKING_RESISTENCIA = ruta_json("ranking_resistencia.json")
PATH_CREADOR_PRIVADO = ruta_json("creador_privado.json")
