#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esquemas JSON locales, inicialización y limpieza de ``Data/Juego/``."""

from __future__ import annotations

# --- esquemas ---


from typing import Any

__all__ = [
    "estadisticas_jugador_vacio",
    "preferencias_grafico_vacio",
    "texto_referencia_datos_juego",
]

CAMPOS_ESTADISTICAS = {
    "totales": "partidas, preguntas, aciertos, fallos, segundos_jugados (enteros >= 0)",
    "por_modo": "dict modo -> {partidas, preguntas, aciertos, segundos_jugados}",
    "por_materia": "dict materia -> {intentos, aciertos}",
    "por_tipo": "dict Teoria|Calculo -> {intentos, aciertos}",
    "records": (
        "resistencia_racha, resistencia_puntos, resistencia_preguntas, "
        "escape_salas, escape_puntos_arcade, mejor_porcentaje_sesion"
    ),
    "sesiones": "lista interna ({duracion_seg, ...}; evolución semanal)",
    "dias_activos": "fechas ISO locales con actividad",
}

CAMPOS_PREFERENCIAS = {
    "nombre_jugador": 'str; vacío = anónimo ("Anonimo" en partida)',
    "mostrar_tooltips": "bool",
    "mostrar_emojis": "bool",
    "guardar_informes_txt": "bool; generar .txt al terminar partida",
}


def preferencias_grafico_vacio() -> dict[str, Any]:
    """Estado inicial de ``preferencias_grafico.json``."""
    return {
        "nombre_jugador": "",
        "mostrar_tooltips": True,
        "mostrar_emojis": True,
        "guardar_informes_txt": True,
    }


def estadisticas_jugador_vacio() -> dict[str, Any]:
    """Estado inicial de ``estadisticas_jugador.json``."""
    return {
        "totales": {
            "partidas": 0,
            "preguntas": 0,
            "aciertos": 0,
            "fallos": 0,
            "segundos_jugados": 0,
        },
        "por_modo": {},
        "por_materia": {},
        "por_tipo": {},
        "records": {
            "resistencia_racha": 0,
            "resistencia_puntos": 0,
            "resistencia_preguntas": 0,
            "escape_salas": 0,
            "escape_puntos_arcade": 0,
            "mejor_porcentaje_sesion": 0,
        },
        "sesiones": [],
        "dias_activos": [],
    }


def texto_referencia_datos_juego() -> str:
    """Texto plano para documentación o consola (``utilidades_tfg.py --esquemas-juego``)."""
    lineas = [
        "Data/Juego/ — datos locales del jugador (generados al jugar)",
        "",
        "  preferencias_grafico.json",
        "  estadisticas_jugador.json",
        "  *.txt (informes y feedback)",
        "",
        "Catálogo de modos: Juego/presets.json",
        "",
        "preferencias_grafico.json — campos:",
    ]
    for clave, desc in CAMPOS_PREFERENCIAS.items():
        lineas.append(f"  {clave}: {desc}")
    lineas.extend(["", "estadisticas_jugador.json — secciones:"])
    for clave, desc in CAMPOS_ESTADISTICAS.items():
        lineas.append(f"  {clave}: {desc}")
    return "\n".join(lineas)

# --- datos_locales ---


from dataclasses import dataclass
from pathlib import Path

from Comun.rutas import resolver_dir_informes

__all__ = [
    "ResumenBorradoTxt",
    "borrar_txt_informes_feedback",
    "inicializar_datos_locales_juego",
    "listar_txt_informes_feedback",
    "vaciar_contenido_json_locales",
    "vaciar_preferencias_locales",
    "vaciar_estadisticas_locales",
    "estadisticas_jugador_vacio",
    "preferencias_grafico_vacio",
    "texto_referencia_datos_juego",
]


@dataclass
class ResumenBorradoTxt:
    borrados: int = 0
    errores: int = 0


def inicializar_datos_locales_juego() -> None:
    """Crea los JSON de runtime en ``Data/Juego/`` si aún no existen."""
    from Comun.estadisticas_jugador import (
        resolver_path_estadisticas_jugador,
        vaciar_estadisticas_jugador,
    )
    from Comun.preferencias_grafico import (
        PreferenciasGrafico,
        guardar_preferencias_grafico,
        resolver_path_preferencias_grafico,
    )

    if not resolver_path_estadisticas_jugador().is_file():
        vaciar_estadisticas_jugador()
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
    from Comun.preferencias_grafico import PreferenciasGrafico, guardar_preferencias_grafico

    guardar_preferencias_grafico(PreferenciasGrafico())


def vaciar_estadisticas_locales() -> None:
    """Restablece las estadísticas agregadas del jugador."""
    from Comun.estadisticas_jugador import vaciar_estadisticas_jugador

    vaciar_estadisticas_jugador()


def vaciar_contenido_json_locales() -> None:
    """Restablece preferencias y estadísticas (sin eliminar ``.json``)."""
    vaciar_preferencias_locales()
    vaciar_estadisticas_locales()


def __getattr__(name: str):
    if name == "resolver_path_preferencias_grafico":
        from Comun.preferencias_grafico import resolver_path_preferencias_grafico

        return resolver_path_preferencias_grafico
    if name == "resolver_path_estadisticas_jugador":
        from Comun.estadisticas_jugador import resolver_path_estadisticas_jugador

        return resolver_path_estadisticas_jugador
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
