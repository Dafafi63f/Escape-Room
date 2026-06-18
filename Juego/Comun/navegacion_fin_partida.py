#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Acciones disponibles al terminar una partida (repetir, reconfigurar, menú)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Grafico.pantallas import Pantalla


@dataclass
class NavegacionFinPartida:
    """Pantallas a las que puede ir el jugador desde el resumen final."""

    repetir: Callable[[], Pantalla] | None = None
    configurar: Callable[[], Pantalla] | None = None
