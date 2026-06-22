#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Semilla aleatoria para examen balanceado (contenido nuevo en cada partida)."""

from __future__ import annotations

import secrets

__all__ = [
    "semilla_aleatoria_examen",
]


def semilla_aleatoria_examen() -> int:
    """Nueva semilla en cada llamada (inicio o repetir partida)."""
    return secrets.randbelow(2**31 - 1) + 1
