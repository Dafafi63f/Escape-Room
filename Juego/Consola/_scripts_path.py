#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Añade ``Files/Scripts`` al path para importar utilidades compartidas con el juego."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "Files" / "Scripts"
if _SCRIPTS.is_dir() and str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
