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
        PerfilPedagogico.BALANCEADO: "Preferencia histórica suave al repartir preguntas entre materias.",
        PerfilPedagogico.REFUERZO: "Más preguntas en materias con más suspensos del ámbito.",
        PerfilPedagogico.DESAFIO: "Más preguntas en materias con mejores medias del ámbito.",
        PerfilPedagogico.POR_CURSO: "Cobertura del ámbito curricular; más preguntas en las más exigentes.",
        PerfilPedagogico.SIMULACRO: "Una pregunta por materia del ámbito (repaso global).",
    }
    return textos.get(perfil, perfil.value)
