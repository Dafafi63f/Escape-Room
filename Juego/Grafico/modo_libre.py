#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades gráficas del modo libre (UI); lógica compartida en ``Comun``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from Comun.reglas import max_complejidad_pool
from Comun.modelos import BancoPreguntas, Pregunta
from Comun.pool_libre import (
    cargar_pool_por_banco,
    filtrar_pool,
    opciones_curso_semestre,
    opciones_tematica,
    opciones_tipo,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego


def cargar_pool_banco(datos: DatosJuego, banco: BancoPreguntas) -> list[Pregunta]:
    return cargar_pool_por_banco(
        banco,
        preguntas_dataset=datos.preguntas,
        path_preguntas_csv=datos.path_preguntas_csv,
        path_plantillas_json=datos.path_plantillas_json,
        materias_meta=datos.materias_meta,
    )


# Abreviaturas solo cuando el nombre completo no cabe en el botón.
ETIQUETAS_TEMATICA_CORTA: dict[str, str] = {
    "Algoritmia i Teoria de Jocs": "Algoritmia i Jocs",
    "Intel·ligencia Artificial i Aprenentatge Automatic": "IA i Aprenentatge",
    "Metodes Numerics i Optimitzacio": "Metodes Numerics",
    "Modelitzacio Fisica i Informacio": "Fisica i Informacio",
    "Probabilitat i Ciencia de Dades": "Prob. i Dades",
    "Programacio de Software": "Programacio",
    "Sistemes i Seguretat Computacional": "Sistemes i Seguretat",
}


def _cabe_texto_en_ancho(texto: str, fuente: pygame.font.Font, ancho_max: int) -> bool:
    from Grafico.texto import preparar_texto_ui

    etiqueta = preparar_texto_ui(texto)
    return fuente.size(etiqueta)[0] <= ancho_max


def etiqueta_subfiltro_visible(
    clave: str,
    modo_filtro: str,
    *,
    ancho_boton: int | None = None,
    fuente: pygame.font.Font | None = None,
) -> str:
    if clave == "__todas__":
        return "Todas"
    if modo_filtro == "tematica":
        corto = ETIQUETAS_TEMATICA_CORTA.get(clave, clave)
        if (
            corto != clave
            and ancho_boton is not None
            and fuente is not None
        ):
            from Grafico.ui import BotonMarcable

            ancho_max = BotonMarcable.ancho_etiqueta(ancho_boton)
            if _cabe_texto_en_ancho(clave, fuente, ancho_max):
                return clave
            return corto
        return clave
    return clave
