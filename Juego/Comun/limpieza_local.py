#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Borrado de datos locales generados al jugar (informes, feedback, rankings)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Comun.ranking_resistencia import (
    VARIANTES_RANKING,
    etiqueta_variante_ranking,
    path_ranking_para_variante,
    vaciar_ranking,
)
from Comun.rutas import resolver_dir_feedback, resolver_dir_informes

__all__ = [
    "ResumenBorradoTxt",
    "borrar_txt_informes_feedback",
    "etiqueta_variante_ranking",
    "listar_txt_informes_feedback",
    "vaciar_ranking_variante",
]


@dataclass
class ResumenBorradoTxt:
    borrados: int = 0
    errores: int = 0


def _carpetas_txt() -> tuple[Path, ...]:
    return (resolver_dir_informes(), resolver_dir_feedback())


def listar_txt_informes_feedback() -> list[Path]:
    """Lista ``.txt`` en ``Informes/`` y ``Feedback/`` (solo ficheros, no subcarpetas)."""
    encontrados: list[Path] = []
    for carpeta in _carpetas_txt():
        if not carpeta.is_dir():
            continue
        for fichero in carpeta.glob("*.txt"):
            if fichero.is_file():
                encontrados.append(fichero)
    return sorted(encontrados)


def borrar_txt_informes_feedback() -> ResumenBorradoTxt:
    resumen = ResumenBorradoTxt()
    for fichero in listar_txt_informes_feedback():
        try:
            fichero.unlink()
            resumen.borrados += 1
        except OSError:
            resumen.errores += 1
    return resumen


def vaciar_ranking_variante(variante: str) -> None:
    if variante not in VARIANTES_RANKING:
        raise ValueError(f"Variante de ranking desconocida: {variante}")
    vaciar_ranking(path_ranking_para_variante(variante))
