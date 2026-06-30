#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tipos de dominio del cuestionario."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BancoPreguntas(str, Enum):
    DATASET = "dataset"
    PLANTILLAS_TODO = "plantillas_todo"


OPCIONES_BANCO_JUEGO: tuple[BancoPreguntas, ...] = (
    BancoPreguntas.DATASET,
    BancoPreguntas.PLANTILLAS_TODO,
)

ETIQUETAS_BANCO_CORTAS: dict[BancoPreguntas, str] = {
    BancoPreguntas.DATASET: "480 revisadas",
    BancoPreguntas.PLANTILLAS_TODO: "Banco ampliado",
}

ETIQUETA_BANCO: dict[BancoPreguntas, tuple[str, str]] = {
    BancoPreguntas.DATASET: (
        "BANCO REVISADO",
        "480 preguntas del dataset (Preguntas.csv), listas para estudio.",
    ),
    BancoPreguntas.PLANTILLAS_TODO: (
        "BANCO AMPLIADO",
        "960 preguntas reales: 480 revisadas + 480 extras JSON (opcional; sin revisión completa).",
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
