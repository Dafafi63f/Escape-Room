#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pantalla de estadísticas locales del jugador."""

from __future__ import annotations

from collections.abc import Callable

from Comun.estadisticas_jugador import formatear_panel_estadisticas
from Grafico.pantallas_sistema import PantallaInfoTexto


class PantallaEstadisticasJugador(PantallaInfoTexto):
    """Resumen de evolución, récords y materias débiles."""

    def __init__(self, volver_a: Callable[[], None], *, perfil=None) -> None:
        super().__init__(
            "Mis estadísticas",
            formatear_panel_estadisticas(perfil),
            volver_a,
        )
