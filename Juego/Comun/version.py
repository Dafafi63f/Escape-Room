#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versión del juego entregable (TFG)."""

from __future__ import annotations

VERSION = "1.0.0"
VERSION_FECHA = "2026-06-29"
VERSION_ALCANCE = "Entrega TFG — desarrollo en pausa"


def etiqueta_version() -> str:
    return f"v{VERSION}"


def texto_version_completo() -> str:
    return f"MATCAD {etiqueta_version()} ({VERSION_FECHA}) — {VERSION_ALCANCE}"
