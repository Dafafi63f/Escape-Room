#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Perfiles pedagógicos del generador de exámenes (modo historia)."""

from __future__ import annotations

from enum import Enum


class PerfilPedagogico(str, Enum):
    """Perfiles v1 (datos agregados del histórico)."""

    BALANCEADO = "balanceado"
    REFUERZO = "refuerzo"
    DESAFIO = "desafio"
    POR_CURSO = "por_curso"
    SIMULACRO = "simulacro"


def describir_perfil(perfil: PerfilPedagogico) -> str:
    textos = {
        PerfilPedagogico.BALANCEADO: "Reparto equitativo; el histórico solo informa.",
        PerfilPedagogico.REFUERZO: "Prioriza materias con más suspensos en el histórico.",
        PerfilPedagogico.DESAFIO: "Prioriza materias con mejores medias históricas.",
        PerfilPedagogico.POR_CURSO: "Las materias de un curso (10 asignaturas); balance por slots.",
        PerfilPedagogico.SIMULACRO: "Una pregunta por materia del ámbito (repaso global).",
    }
    return textos.get(perfil, perfil.value)
