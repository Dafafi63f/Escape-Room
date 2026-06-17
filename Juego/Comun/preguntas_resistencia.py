#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preguntas exclusivas del modo resistencia (no aparecen en otros modos)."""

from __future__ import annotations

import json
from pathlib import Path

from Comun.modelos import Pregunta
from Comun.rutas import resolver_preguntas_resistencia

__all__ = [
    "ETIQUETAS_TIER_RESISTENCIA",
    "cargar_preguntas_exclusivas_resistencia",
    "construir_pool_resistencia",
    "pool_resistencia_desde_dataset",
]

ETIQUETAS_TIER_RESISTENCIA: dict[int, str] = {
    1: "Élite",
    2: "Maestro",
    3: "Legendario",
    4: "Imposible",
}


def pool_resistencia_desde_dataset(preguntas: list[Pregunta]) -> list[Pregunta]:
    """Preguntas del dataset revisado válidas para resistencia (sin exclusivas)."""
    return [
        p
        for p in preguntas
        if p.correcta in {"A", "B", "C", "D"}
        and any(p.opciones.get(letra) for letra in "ABCD")
        and not p.exclusiva_resistencia
    ]


def _parse_opciones(raw: dict | None) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    return {k: str(v) for k, v in raw.items() if k in "ABCD"}


def cargar_preguntas_exclusivas_resistencia(
    materias_meta: dict[str, dict[str, str]],
    *,
    path: Path | None = None,
) -> list[Pregunta]:
    """Carga el banco extra solo para resistencia avanzada."""
    ruta = path or resolver_preguntas_resistencia()
    if not ruta.exists():
        return []
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    items = data.get("preguntas", [])
    if not isinstance(items, list):
        return []

    resultado: list[Pregunta] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        correcta = str(item.get("correcta", "")).strip().upper()
        if correcta not in {"A", "B", "C", "D"}:
            continue
        opciones = _parse_opciones(item.get("opciones"))
        if not all(opciones.get(l) for l in "ABCD"):
            continue
        texto = str(item.get("pregunta", "")).strip()
        if not texto:
            continue
        materia = str(item.get("materia", "General")).strip() or "General"
        mm = materias_meta.get(materia, {})
        racha_min = int(item.get("racha_minima", 100))
        tier = int(item.get("tier", 1))
        resultado.append(
            Pregunta(
                texto=texto,
                materia=materia,
                tematica=str(item.get("tematica") or mm.get("tematica", "")),
                dificultad=str(item.get("dificultad", "Dificil")),
                tipo=str(item.get("tipo", "Teoria")),
                grupo=str(item.get("grupo") or mm.get("grupo", "")),
                nivel=str(item.get("nivel") or mm.get("nivel", "3")),
                curso=str(item.get("curso") or mm.get("curso", "")),
                semestre=str(item.get("semestre") or mm.get("semestre", "")),
                opciones=opciones,
                correcta=correcta,
                fuente="resistencia_exclusiva",
                exclusiva_resistencia=True,
                racha_minima_resistencia=max(1, racha_min),
                tier_resistencia=max(1, min(4, tier)),
            )
        )
    return resultado


def construir_pool_resistencia(
    preguntas_dataset: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
    *,
    path_exclusivas: Path | None = None,
) -> list[Pregunta]:
    """Pool completo: dataset + exclusivas de resistencia."""
    base = pool_resistencia_desde_dataset(preguntas_dataset)
    exclusivas = cargar_preguntas_exclusivas_resistencia(
        materias_meta, path=path_exclusivas
    )
    return base + exclusivas
