#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compatibilidad: delega en ``mantenimiento.py validar`` (y bloquea regeneración)."""

from __future__ import annotations

import sys
from pathlib import Path

FILES = Path(__file__).resolve().parent
sys.path.insert(0, str(FILES))

from mantenimiento import main  # noqa: E402

if __name__ == "__main__":
    forward = sys.argv[1:]
    if not forward:
        forward = ["validar"]
    elif forward[0] not in (
        "validar",
        "ajustar",
        "reordenar",
        "ordenar-ladder",
        "corregir",
        "conservador",
        "agresivo",
    ):
        forward = ["validar", *forward]
    raise SystemExit(main(forward))
