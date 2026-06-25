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
    BancoPreguntas.DATASET: "Modo seguro",
    BancoPreguntas.PLANTILLAS_TODO: "Modo beta",
}

ETIQUETA_BANCO: dict[BancoPreguntas, tuple[str, str]] = {
    BancoPreguntas.DATASET: (
        "MODO SEGURO",
        "Data/Banco/Preguntas.csv — 480 preguntas revisadas",
    ),
    BancoPreguntas.PLANTILLAS_TODO: (
        "MODO BETA",
        "Dataset revisado + plantillas extra — 1440 preguntas",
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
