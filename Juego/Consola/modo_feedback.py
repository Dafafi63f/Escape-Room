#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modo feedback — en desarrollo.

Previsto: explicación pedagógica tras cada respuesta. Reutilizará politica_reglas
para fijar el contexto (sin mezclar examen con arcade libre).
"""

from __future__ import annotations

from .modelos import Pregunta


def jugar_modo_feedback(
    preguntas: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
) -> None:
    _ = preguntas, materias_meta
    print("\n=== MODO FEEDBACK ===")
    print("Este modo aún no está implementado.")
    print("Objetivo: retroalimentación didáctica tras cada respuesta.")
    print("Compartirá reglas de partida (examen / arcade / personalizado) con historia y libre.")
    print("Mientras tanto, usa modo historia (simulacro examen) o modo libre (repaso).")
