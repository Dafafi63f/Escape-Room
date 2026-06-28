#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bootstrap de ``sys.path`` para los tests del juego en ``Tests/``."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JUEGO_DIR = ROOT / "Juego"


def _prepend(path: Path) -> None:
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)


def ensure_root_on_path() -> None:
    _prepend(ROOT)


def ensure_files_path() -> None:
    ensure_root_on_path()
    _prepend(ROOT / "Files")


def ensure_juego_path() -> None:
    ensure_root_on_path()
    _prepend(JUEGO_DIR)


def emoji_font_disponible() -> bool:
    """True si el runner tiene fuente emoji (p. ej. Noto Color Emoji en CI)."""
    ensure_juego_path()
    from Grafico.fuentes import fuente_disponible

    return fuente_disponible("emoji")
