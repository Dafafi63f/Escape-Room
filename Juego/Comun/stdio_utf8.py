#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configura stdout/stderr en UTF-8 (emojis en consola Windows)."""

from __future__ import annotations

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
