#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esquemas JSON locales, inicialización y limpieza de ``Data/Juego/``."""

from __future__ import annotations

# --- esquemas ---


from pathlib import Path
from typing import Any

__all__ = [
    "auditar_carpetas_data",
    "es_fichero_runtime_juego",
    "estadisticas_jugador_vacio",
    "preferencias_grafico_vacio",
    "texto_referencia_datos_juego",
]

# Ficheros de catálogo / banco que no deben aparecer en Data/Juego/.
_FICHEROS_PROHIBIDOS_EN_JUEGO = frozenset({
    "presets.json",
    "preguntas_resistencia.json",
    "plantillas.json",
    "Preguntas.csv",
    "listado_materias.csv",
    "criterios_clasificacion_materia.csv",
    "creador_privado.json",
})

_CARPETAS_PROHIBIDAS_EN_JUEGO = frozenset({"defaults", "Banco"})

# Runtime del jugador: no deben versionarse ni empaquetarse en el zip jugable.
_PATRONES_RUNTIME_JUEGO = (
    "preferencias_grafico.json",
    "estadisticas_jugador.json",
    "ranking_*.json",
    "*.txt",
)  # documentación; ver es_fichero_runtime_juego()

CAMPOS_ESTADISTICAS = {
    "totales": "partidas, preguntas, aciertos, fallos, segundos_jugados (enteros >= 0)",
    "por_modo": "dict modo -> {partidas, preguntas, aciertos, segundos_jugados}",
    "por_materia": "dict materia -> {intentos, aciertos}",
    "por_concepto": "dict token enunciado -> {intentos, aciertos, fallos}",
    "por_tipo": "dict Teoria|Calculo -> {intentos, aciertos}",
    "records": (
        "resistencia_racha, resistencia_puntos, resistencia_preguntas, "
        "escape_salas, escape_puntos_arcade, mejor_porcentaje_sesion"
    ),
    "resistencia_variedad": (
        "pity entre partidas cortas: partidas, sin_por_categoria "
        "(escalada_hostil, escalada_buena, bloque, jefe, maldicion, evento_si_no)"
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
            "salas_escape": 0,
        },
        "por_modo": {},
        "por_materia": {},
        "por_concepto": {},
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
        "resistencia_variedad": {
            "partidas": 0,
            "sin_por_categoria": {},
        },
    }


def es_fichero_runtime_juego(nombre: str) -> bool:
    """True si el fichero es estado local del jugador (no empaquetar en zip)."""
    bajo = nombre.lower()
    if bajo.endswith(".txt"):
        return True
    if bajo == "estadisticas_jugador.json":
        return True
    if bajo == "metadatos_inferidos.json":
        return True
    if bajo.startswith("preferencias_") and bajo.endswith(".json"):
        return True
    return bajo.startswith("ranking_") and bajo.endswith(".json")


def auditar_carpetas_data(raiz: Path | None = None) -> list[str]:
    """Detecta ficheros fuera de sitio en ``Data/Banco/``, ``Data/Juego/`` y ``Data/Privado/``."""
    from Comun.rutas import etiqueta_dir_datos_jugador, juego_dir, layout_datos_jugador_plano

    base = (raiz or juego_dir().parent) / "Data"
    problemas: list[str] = []
    banco = base / "Banco"
    juego = base / "Juego"
    destino_runtime = etiqueta_dir_datos_jugador()

    if not layout_datos_jugador_plano():
        for fichero in sorted(base.iterdir()) if base.is_dir() else []:
            if not fichero.is_file():
                continue
            nombre = fichero.name
            if es_fichero_runtime_juego(nombre):
                problemas.append(
                    f"Data/{nombre}: estado local del jugador "
                    f"(debe estar en {destino_runtime}/)"
                )
    else:
        for subdir in ("Banco", "Juego", "Privado"):
            ruta = base / subdir
            if ruta.is_dir():
                problemas.append(
                    f"Data/{subdir}/: subdirectorio no usado en paquete mínimo "
                    "(todos los ficheros van en Data/ plano)"
                )

    if not layout_datos_jugador_plano():
        for fichero in sorted(banco.iterdir()) if banco.is_dir() else []:
            if not fichero.is_file():
                continue
            nombre = fichero.name
            if nombre.endswith(".txt") or nombre.startswith("preferencias_"):
                problemas.append(
                    f"Data/Banco/{nombre}: informe o preferencias del jugador "
                    f"(debe estar en {destino_runtime}/)"
                )
            elif nombre in ("estadisticas_jugador.json",) or nombre.startswith("ranking_"):
                problemas.append(
                    f"Data/Banco/{nombre}: estadísticas locales "
                    f"(debe estar en {destino_runtime}/)"
                )
            elif nombre == "presets.json":
                problemas.append(
                    f"Data/Banco/{nombre}: catálogo de modos "
                    "(debe estar en Juego/presets.json)"
                )
            elif nombre == "creador_privado.json":
                problemas.append(
                    f"Data/Banco/{nombre}: configuración privada del autor "
                    "(mover a Data/Privado/)"
                )
            elif fichero.suffix.lower() == ".xlsx":
                problemas.append(
                    f"Data/Banco/{nombre}: fuente de mantenimiento "
                    "(mover a Data/Privado/)"
                )

    if not layout_datos_jugador_plano() and juego.is_dir():
        for entrada in sorted(juego.rglob("*")):
            if not entrada.is_file():
                continue
            rel = entrada.relative_to(juego)
            partes = rel.parts
            if partes and partes[0] in _CARPETAS_PROHIBIDAS_EN_JUEGO:
                problemas.append(
                    f"Data/Juego/{rel.as_posix()}: carpeta obsoleta "
                    "(los valores por defecto están en Comun/persistencia.py)"
                )
                continue
            nombre = entrada.name
            if nombre in _FICHEROS_PROHIBIDOS_EN_JUEGO:
                if nombre == "presets.json":
                    destino = "Juego/presets.json"
                elif nombre == "preguntas_resistencia.json":
                    destino = "Juego/Comun/preguntas_resistencia_exclusivas_datos.py"
                elif nombre == "creador_privado.json":
                    destino = "Data/Privado/"
                else:
                    destino = "Data/Banco/"
                problemas.append(
                    f"Data/Juego/{rel.as_posix()}: catálogo o banco fuera de sitio "
                    f"(usar {destino})"
                )

    for fichero in sorted(base.glob("*.xlsx")):
        problemas.append(
            f"Data/{fichero.name}: fuente de mantenimiento "
            "(mover a Data/Privado/)"
        )

    fuentes_legacy = (raiz or juego_dir().parent) / "Files" / "fuentes"
    if fuentes_legacy.is_dir() and any(fuentes_legacy.iterdir()):
        problemas.append(
            "Files/fuentes/: carpeta obsoleta (mover su contenido a Data/Privado/)"
        )

    fixture_csv = (raiz or juego_dir().parent) / "Tests" / "Fixtures" / "Preguntas_minimal.csv"
    if fixture_csv.is_file():
        problemas.append(
            "Tests/Fixtures/Preguntas_minimal.csv: obsoleto (usar Data/Privado/Preguntas_minimal.csv)"
        )

    return problemas


def texto_referencia_datos_juego() -> str:
    """Texto plano para documentación o consola (esquemas JSON del jugador)."""
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

from Comun.rutas import resolver_dir_informes

__all__ = [
    "ResumenBorradoTxt",
    "auditar_carpetas_data",
    "borrar_txt_informes_feedback",
    "es_fichero_runtime_juego",
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
