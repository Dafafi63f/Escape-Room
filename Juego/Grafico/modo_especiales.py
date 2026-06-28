#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogo de modos especiales (resistencia, escape room…) en la interfaz gráfica."""

from __future__ import annotations

from Comun.presets_historia import PresetHistoria, cargar_presets_especiales
from Comun.rutas import resolver_presets


def cargar_catalogo_especiales(perfil=None) -> list[PresetHistoria]:
    return cargar_presets_especiales(resolver_presets(), perfil=perfil)
