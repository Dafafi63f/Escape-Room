#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tipos de dominio del cuestionario."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BancoPreguntas(str, Enum):
    DATASET = "dataset"
    PLANTILLAS_TODO = "plantillas_todo"
    PLANTILLAS_EXTRA = "plantillas_extra"


ETIQUETA_BANCO: dict[BancoPreguntas, tuple[str, str]] = {
    BancoPreguntas.DATASET: ("MODO SEGURO", "Data/CSV/Preguntas.csv (banco revisado)"),
    BancoPreguntas.PLANTILLAS_TODO: (
        "MODO BETA",
        "dataset revisado + plantillas fuera del dataset",
    ),
    BancoPreguntas.PLANTILLAS_EXTRA: (
        "MODO BETA",
        "solo plantillas.json fuera del dataset (no revisadas)",
    ),
}


@dataclass
class Pregunta:
    texto: str
    materia: str
    tematica: str
    dificultad: str
    tipo: str
    grupo: str
    nivel: str
    curso: str
    semestre: str
    opciones: dict[str, str]
    correcta: str
    fuente: str = "dataset"
    exclusiva_resistencia: bool = False
    racha_minima_resistencia: int = 0
    tier_resistencia: int = 0
