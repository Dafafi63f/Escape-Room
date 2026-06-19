#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rutas canónicas a ``Data/Banco/`` y ``Data/Juego/`` (scripts de mantenimiento)."""

from __future__ import annotations

from pathlib import Path

PROYECTO = Path(__file__).resolve().parents[1]
DATA = PROYECTO / "Data"
DATA_BANCO = DATA / "Banco"
DATA_JUEGO = DATA / "Juego"

# Alias de compatibilidad (mantenimiento del banco cerrado)
DATA_CSV = DATA_BANCO
DATA_JSON = DATA_BANCO
BASE = PROYECTO

_LEGACY_SUBDIRS = ("CSV", "csv", "JSON", "json", "Juego")


def _resolver(nombre: str, *, en_juego: bool = False) -> Path:
    principal = DATA_JUEGO if en_juego else DATA_BANCO
    secundario = DATA_BANCO if en_juego else DATA_JUEGO
    if (principal / nombre).exists():
        return principal / nombre
    if (secundario / nombre).exists():
        return secundario / nombre
    for subdir in _LEGACY_SUBDIRS:
        legado = DATA / subdir / nombre
        if legado.exists():
            return legado
    legado_raiz = DATA / nombre
    if legado_raiz.exists():
        return legado_raiz
    return principal / nombre


def ruta_banco(nombre: str) -> Path:
    return _resolver(nombre, en_juego=False)


def ruta_juego(nombre: str) -> Path:
    return _resolver(nombre, en_juego=True)


def ruta_datos(nombre: str) -> Path:
    return ruta_banco(nombre)


def ruta_csv(nombre: str) -> Path:
    return ruta_banco(nombre)


def ruta_json(nombre: str) -> Path:
    return ruta_banco(nombre)


PATH_PREGUNTAS = ruta_banco("Preguntas.csv")
PATH_LISTADO_MATERIAS = ruta_banco("listado_materias.csv")
PATH_CRITERIOS_CLASIFICACION = ruta_banco("criterios_clasificacion_materia.csv")
PATH_HISTORICO_QUALIFICACIONS = ruta_banco("Historic_qualificacions_MatCAD_completo.csv")
PATH_PLANTILLAS = ruta_banco("plantillas.json")
PATH_PRESETS_HISTORIA = ruta_juego("presets_historia.json")
PATH_PREGUNTAS_RESISTENCIA = ruta_juego("preguntas_resistencia.json")
PATH_CREADOR_PRIVADO = ruta_banco("creador_privado.json")
