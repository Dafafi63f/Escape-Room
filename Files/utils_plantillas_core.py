# -*- coding: utf-8 -*-
"""Reexporta el módulo canónico en ``Juego/Comun/`` (compatibilidad con scripts de Files/)."""

from __future__ import annotations

import sys
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[1] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.utils_plantillas_core import (  # noqa: E402
    clave_contenido,
    clave_contenido_sin_materia,
    claves_desde_csv,
    expandir_plantilla_base,
    expandir_plantilla_csv_filas,
    expandir_plantilla_instancias,
    norm_clave_texto,
    quitar_etiqueta_materia_enunciado,
    tiene_placeholders,
)

__all__ = [
    "clave_contenido",
    "clave_contenido_sin_materia",
    "claves_desde_csv",
    "expandir_plantilla_base",
    "expandir_plantilla_csv_filas",
    "expandir_plantilla_instancias",
    "norm_clave_texto",
    "quitar_etiqueta_materia_enunciado",
    "tiene_placeholders",
]
