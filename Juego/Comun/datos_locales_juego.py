#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Datos locales en ``Data/Juego/``: creación al inicio y limpieza **desde el juego**.

Política de limpieza
--------------------

+---------------------------+------------------+------------------+
| Fichero                   | Desde el juego   | Desde fuera      |
+===========================+==================+==================+
| ``*.txt``                 | borrar           | borrar           |
| ``preferencias_grafico.json`` | vaciar contenido | borrar fichero   |
| ``ranking_*.json``            | vaciar contenido | borrar fichero   |
| presets, pool resistencia | no tocar         | no tocar         |
+---------------------------+------------------+------------------+

Desde fuera: ``python Docs/utilidades_tfg.py --solo-limpieza`` (``Files/borrar_temporales.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Comun.preferencias_grafico import (
    PreferenciasGrafico,
    guardar_preferencias_grafico,
    resolver_path_preferencias_grafico,
)
from Comun.ranking_resistencia import vaciar_ranking_variante
from Comun.rutas import resolver_dir_informes, resolver_ranking_resistencia

__all__ = [
    "ResumenBorradoTxt",
    "borrar_txt_informes_feedback",
    "inicializar_datos_locales_juego",
    "listar_txt_informes_feedback",
    "vaciar_contenido_json_locales",
    "vaciar_preferencias_locales",
    "vaciar_rankings_locales",
]


@dataclass
class ResumenBorradoTxt:
    borrados: int = 0
    errores: int = 0


def inicializar_datos_locales_juego() -> None:
    """Crea los JSON de runtime en ``Data/Juego/`` si aún no existen."""
    resolver_ranking_resistencia()
    if not resolver_path_preferencias_grafico().is_file():
        guardar_preferencias_grafico(PreferenciasGrafico())


def _dir_juego_local() -> Path:
    return resolver_dir_informes()


def listar_txt_informes_feedback() -> list[Path]:
    carpeta = _dir_juego_local()
    if not carpeta.is_dir():
        return []
    return sorted(p for p in carpeta.glob("*.txt") if p.is_file())


def borrar_txt_informes_feedback() -> ResumenBorradoTxt:
    """Elimina ``.txt`` de informes y feedback (único borrado de ficheros desde el juego)."""
    resumen = ResumenBorradoTxt()
    for fichero in listar_txt_informes_feedback():
        try:
            fichero.unlink()
            resumen.borrados += 1
        except OSError:
            resumen.errores += 1
    return resumen


def vaciar_preferencias_locales() -> None:
    """Restablece las preferencias del menú de opciones (``preferencias_grafico.json``)."""
    guardar_preferencias_grafico(PreferenciasGrafico())


def vaciar_rankings_locales() -> None:
    """Vacía el historial del ranking local (conserva el fichero JSON)."""
    vaciar_ranking_variante("resistencia")


def vaciar_contenido_json_locales() -> None:
    """Restablece preferencias y vacía rankings (sin eliminar ningún ``.json``)."""
    vaciar_preferencias_locales()
    vaciar_rankings_locales()
