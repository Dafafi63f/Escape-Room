#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Añade ``Files`` al path para importar utilidades compartidas con el juego."""

from __future__ import annotations

import sys
from pathlib import Path

_FILES = Path(__file__).resolve().parent.parent.parent / "Files"
if _FILES.is_dir() and str(_FILES) not in sys.path:
    sys.path.insert(0, str(_FILES))
