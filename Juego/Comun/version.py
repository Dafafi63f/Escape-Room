#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versión del juego (proyecto personal / educativo)."""

from __future__ import annotations

VERSION = "1.1.0"
VERSION_FECHA = "2026-08-07"
VERSION_ALCANCE = "Juego educativo · proyecto personal"


def etiqueta_version() -> str:
    return f"v{VERSION}"


def texto_version_completo() -> str:
    return f"MATCAD {etiqueta_version()} ({VERSION_FECHA}) — {VERSION_ALCANCE}"
