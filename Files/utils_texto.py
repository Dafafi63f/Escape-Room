#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidades de normalización de texto para comparaciones.
"""

from __future__ import annotations

import re


def normalizar_basico(texto: str) -> str:
    """Minúsculas + trim + espacios normalizados."""
    texto = (texto or "").strip().lower()
    return re.sub(r"\s+", " ", texto)


def normalizar_pregunta(texto: str) -> str:
    """Normalización para comparar enunciados (quita puntuación básica)."""
    texto = normalizar_basico(texto)
    texto = texto.replace("¿", "").replace("?", "")
    texto = re.sub(r"[^\w\s]", " ", texto, flags=re.UNICODE)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto
