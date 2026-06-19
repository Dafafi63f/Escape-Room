#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Categorías y áreas del modo feedback."""

from __future__ import annotations

__all__ = [
    "AREAS_FEEDBACK",
    "CATEGORIAS_FEEDBACK",
    "etiqueta_area",
    "etiqueta_categoria",
    "indice_area_defecto",
]

CATEGORIAS_FEEDBACK: list[tuple[str, str]] = [
    ("bug", "Error o fallo del juego"),
    ("sugerencia", "Sugerencia de mejora"),
    ("pregunta_incorrecta", "Pregunta con error o respuesta dudosa"),
    ("controles_interfaz", "Controles, menús o interfaz"),
    ("otro", "Otro tema"),
]

AREAS_FEEDBACK: list[tuple[str, str]] = [
    ("menu", "Menús y navegación"),
    ("partida", "Durante una partida o pregunta"),
    ("datos", "Preguntas, materias o banco de datos"),
    ("informes", "Informes o resultados"),
    ("rendimiento", "Rendimiento o carga"),
    ("general", "General / no sé"),
]


def etiqueta_categoria(cat_id: str) -> str:
    for cid, desc in CATEGORIAS_FEEDBACK:
        if cid == cat_id:
            return desc
    return cat_id


def etiqueta_area(area_id: str) -> str:
    for aid, desc in AREAS_FEEDBACK:
        if aid == area_id:
            return desc
    return area_id


def indice_area_defecto() -> int:
    """Índice de «general» en AREAS_FEEDBACK (base 0)."""
    for i, (aid, _) in enumerate(AREAS_FEEDBACK):
        if aid == "general":
            return i
    return len(AREAS_FEEDBACK) - 1
