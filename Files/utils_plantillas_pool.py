# -*- coding: utf-8 -*-
"""Selección del pool de plantillas para regeneración / creación de preguntas."""

from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

from objetivos_balanceo import USO_PLANTILLA_DATASET

USO_COPIA_DATASET = frozenset({USO_PLANTILLA_DATASET})
_USO_EXCLUIDO_DATASET = USO_COPIA_DATASET
_USO_REPUESTO = frozenset({"repuesto", "reserva"})


def es_uso_copia_dataset(uso: str) -> bool:
    return (uso or "").strip().lower() == USO_PLANTILLA_DATASET


def pool_plantillas_materia(items: list[dict]) -> list[dict]:
    """
    Prioridad: ``general`` → ``repuesto`` (temas no cubiertos por el CSV) → resto
    (excepto copias del dataset inyectadas).
    """
    general = [t for t in items if t.get("uso") == "general"]
    repuesto = [t for t in items if t.get("uso") in _USO_REPUESTO]
    otros = [
        t
        for t in items
        if not es_uso_copia_dataset(str(t.get("uso", "")))
        and t.get("uso") not in ("general", *_USO_REPUESTO)
    ]
    if general:
        return general + repuesto
    if repuesto:
        return repuesto
    return otros if otros else items
