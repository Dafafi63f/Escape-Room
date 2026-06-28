#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades transversales del motor (sin pygame)."""

from __future__ import annotations

# --- stdio_utf8 ---


import sys


def configurar_stdio_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, AttributeError):
            pass
