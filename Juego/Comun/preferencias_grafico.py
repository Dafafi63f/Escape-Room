#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preferencias globales de la interfaz gráfica (persistidas en JSON) y nombre de jugador."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from Comun.persistencia import preferencias_grafico_vacio
from Comun.rutas import _ruta_json_escritura

NOMBRE_JUGADOR_DEFECTO = "Anonimo"

__all__ = [
    "NOMBRE_JUGADOR_DEFECTO",
    "PreferenciasGrafico",
    "cargar_preferencias_grafico",
    "ciclar_emojis",
    "ciclar_guardar_informes",
    "ciclar_tooltips",
    "debe_saltar_bienvenida_grafico",
    "emojis_habilitados",
    "es_nombre_anonimo",
    "guardar_informes_txt_habilitados",
    "guardar_preferencias_grafico",
    "nombre_inicial_grafico",
    "nombre_jugador_efectivo",
    "nombre_jugador_grafico",
    "resolver_path_preferencias_grafico",
    "tooltips_habilitados",
]


def nombre_jugador_efectivo(texto: str) -> str:
    limpio = (texto or "").strip()
    return limpio or NOMBRE_JUGADOR_DEFECTO


def es_nombre_anonimo(nombre: str) -> bool:
    return nombre_jugador_efectivo(nombre) == NOMBRE_JUGADOR_DEFECTO


@dataclass
class PreferenciasGrafico:
    nombre_jugador: str = ""
    mostrar_tooltips: bool = True
    mostrar_emojis: bool = True
    guardar_informes_txt: bool = True


def resolver_path_preferencias_grafico() -> Path:
    return _ruta_json_escritura("preferencias_grafico.json")


def ciclar_tooltips(activo: bool) -> bool:
    return not activo


def ciclar_emojis(activo: bool) -> bool:
    return not activo


def ciclar_guardar_informes(activo: bool) -> bool:
    return not activo


def tooltips_habilitados() -> bool:
    return cargar_preferencias_grafico().mostrar_tooltips


def emojis_habilitados() -> bool:
    return cargar_preferencias_grafico().mostrar_emojis


def guardar_informes_txt_habilitados() -> bool:
    return cargar_preferencias_grafico().guardar_informes_txt


def nombre_inicial_grafico() -> str:
    """Nombre guardado para pre-rellenar bienvenida y opciones (vacío si es el anónimo por defecto)."""
    raw = (cargar_preferencias_grafico().nombre_jugador or "").strip()
    if not raw or raw == NOMBRE_JUGADOR_DEFECTO:
        return ""
    return raw


def nombre_jugador_grafico() -> str:
    """Nombre efectivo para partidas e informes (desde preferencias guardadas)."""
    return nombre_jugador_efectivo(cargar_preferencias_grafico().nombre_jugador)


def debe_saltar_bienvenida_grafico() -> bool:
    """Omite la pantalla de bienvenida si ya hay un nombre distinto del anónimo."""
    return bool(nombre_inicial_grafico())


def cargar_preferencias_grafico() -> PreferenciasGrafico:
    path = resolver_path_preferencias_grafico()
    if not path.is_file():
        return PreferenciasGrafico()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return PreferenciasGrafico()
    nombre = str(data.get("nombre_jugador", "") or "").strip()
    tooltips = bool(data.get("mostrar_tooltips", True))
    emojis = bool(data.get("mostrar_emojis", True))
    guardar_informes = bool(data.get("guardar_informes_txt", True))
    return PreferenciasGrafico(
        nombre_jugador=nombre,
        mostrar_tooltips=tooltips,
        mostrar_emojis=emojis,
        guardar_informes_txt=guardar_informes,
    )


def guardar_preferencias_grafico(prefs: PreferenciasGrafico) -> None:
    path = resolver_path_preferencias_grafico()
    path.parent.mkdir(parents=True, exist_ok=True)
    nombre = nombre_jugador_efectivo(prefs.nombre_jugador)
    if nombre == NOMBRE_JUGADOR_DEFECTO:
        nombre = ""
    payload = dict(preferencias_grafico_vacio())
    payload["nombre_jugador"] = nombre
    payload["mostrar_tooltips"] = prefs.mostrar_tooltips
    payload["mostrar_emojis"] = prefs.mostrar_emojis
    payload["guardar_informes_txt"] = prefs.guardar_informes_txt
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
