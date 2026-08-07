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
_FICHERO_PRESETS = "presets.json"
_FICHERO_CREADOR_PRIVADO = "creador_privado.json"
_FICHERO_ESTADISTICAS_JUGADOR = "estadisticas_jugador.json"
_FICHEROS_PROHIBIDOS_EN_JUEGO = frozenset({
    _FICHERO_PRESETS,
    "preguntas_resistencia.json",
    "plantillas.json",
    "Preguntas.csv",
    "listado_materias.csv",
    "criterios_clasificacion_materia.csv",
    _FICHERO_CREADOR_PRIVADO,
})

_CARPETAS_PROHIBIDAS_EN_JUEGO = frozenset({"defaults", "Banco"})

# Runtime del jugador: no deben versionarse ni empaquetarse en el zip jugable.
_PATRONES_RUNTIME_JUEGO = (
    "preferencias_grafico.json",
    _FICHERO_ESTADISTICAS_JUGADOR,
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
    if bajo == _FICHERO_ESTADISTICAS_JUGADOR:
        return True
    if bajo == "metadatos_inferidos.json":
        return True
    if bajo.startswith("preferencias_") and bajo.endswith(".json"):
        return True
    return bajo.startswith("ranking_") and bajo.endswith(".json")


def _destino_catalogo_prohibido_juego(nombre: str) -> str:
    if nombre == _FICHERO_PRESETS:
        return "Juego/presets.json"
    if nombre == "preguntas_resistencia.json":
        return "Juego/Comun/preguntas_resistencia_exclusivas_datos.py"
    if nombre == _FICHERO_CREADOR_PRIVADO:
        return "Data/Privado/"
    return "Data/Banco/"


def _problema_fichero_banco(nombre: str, destino_runtime: str, fichero: Path) -> str | None:
    if nombre.endswith(".txt") or nombre.startswith("preferencias_"):
        return (
            f"Data/Banco/{nombre}: informe o preferencias del jugador "
            f"(debe estar en {destino_runtime}/)"
        )
    if nombre in (_FICHERO_ESTADISTICAS_JUGADOR,) or nombre.startswith("ranking_"):
        return (
            f"Data/Banco/{nombre}: estadísticas locales "
            f"(debe estar en {destino_runtime}/)"
        )
    if nombre == _FICHERO_PRESETS:
        return (
            f"Data/Banco/{nombre}: catálogo de modos "
            "(debe estar en Juego/presets.json)"
        )
    if nombre == _FICHERO_CREADOR_PRIVADO:
        return (
            f"Data/Banco/{nombre}: configuración privada del autor "
            "(mover a Data/Privado/)"
        )
    if fichero.suffix.lower() == ".xlsx":
        return (
            f"Data/Banco/{nombre}: fuente de mantenimiento "
            "(mover a Data/Privado/)"
        )
    return None


def _problema_entrada_juego(entrada: Path, juego: Path) -> str | None:
    rel = entrada.relative_to(juego)
    partes = rel.parts
    if partes and partes[0] in _CARPETAS_PROHIBIDAS_EN_JUEGO:
        return (
            f"Data/Juego/{rel.as_posix()}: carpeta obsoleta "
            "(los valores por defecto están en Comun/persistencia.py)"
        )
    nombre = entrada.name
    if nombre not in _FICHEROS_PROHIBIDOS_EN_JUEGO:
        return None
    destino = _destino_catalogo_prohibido_juego(nombre)
    return (
        f"Data/Juego/{rel.as_posix()}: catálogo o banco fuera de sitio "
        f"(usar {destino})"
    )


def _auditar_runtime_en_data_raiz(base: Path, destino_runtime: str) -> list[str]:
    problemas: list[str] = []
    for fichero in sorted(base.iterdir()) if base.is_dir() else []:
        if not fichero.is_file():
            continue
        if es_fichero_runtime_juego(fichero.name):
            problemas.append(
                f"Data/{fichero.name}: estado local del jugador "
                f"(debe estar en {destino_runtime}/)"
            )
    return problemas


def _auditar_subdirs_layout_plano(base: Path) -> list[str]:
    problemas: list[str] = []
    for subdir in ("Banco", "Juego", "Privado"):
        ruta = base / subdir
        if ruta.is_dir():
            problemas.append(
                f"Data/{subdir}/: subdirectorio no usado en paquete mínimo "
                "(todos los ficheros van en Data/ plano)"
            )
    return problemas


def _auditar_carpeta_banco(banco: Path, destino_runtime: str) -> list[str]:
    problemas: list[str] = []
    for fichero in sorted(banco.iterdir()) if banco.is_dir() else []:
        if not fichero.is_file():
            continue
        msg = _problema_fichero_banco(fichero.name, destino_runtime, fichero)
        if msg:
            problemas.append(msg)
    return problemas


def _auditar_carpeta_juego(juego: Path) -> list[str]:
    problemas: list[str] = []
    if not juego.is_dir():
        return problemas
    for entrada in sorted(juego.rglob("*")):
        if not entrada.is_file():
            continue
        msg = _problema_entrada_juego(entrada, juego)
        if msg:
            problemas.append(msg)
    return problemas


def _auditar_xlsx_en_data(base: Path) -> list[str]:
    return [
        f"Data/{fichero.name}: fuente de mantenimiento "
        "(mover a Data/Privado/)"
        for fichero in sorted(base.glob("*.xlsx"))
    ]


def _auditar_rutas_legacy(raiz: Path) -> list[str]:
    problemas: list[str] = []
    fuentes_legacy = raiz / "Files" / "fuentes"
    if fuentes_legacy.is_dir() and any(fuentes_legacy.iterdir()):
        problemas.append(
            "Files/fuentes/: carpeta obsoleta (mover su contenido a Data/Privado/)"
        )
    fixture_csv = raiz / "Tests" / "Fixtures" / "Preguntas_minimal.csv"
    if fixture_csv.is_file():
        problemas.append(
            "Tests/Fixtures/Preguntas_minimal.csv: obsoleto "
            "(usar Data/Privado/Preguntas_minimal.csv)"
        )
    return problemas


def auditar_carpetas_data(raiz: Path | None = None) -> list[str]:
    """Detecta ficheros fuera de sitio en ``Data/Banco/``, ``Data/Juego/`` y ``Data/Privado/``."""
    from Comun.rutas import etiqueta_dir_datos_jugador, juego_dir, layout_datos_jugador_plano

    raiz_pkg = raiz or juego_dir().parent
    base = raiz_pkg / "Data"
    destino_runtime = etiqueta_dir_datos_jugador()
    plano = layout_datos_jugador_plano()

    problemas: list[str] = []
    if plano:
        problemas.extend(_auditar_subdirs_layout_plano(base))
    else:
        problemas.extend(_auditar_runtime_en_data_raiz(base, destino_runtime))
        problemas.extend(_auditar_carpeta_banco(base / "Banco", destino_runtime))
        problemas.extend(_auditar_carpeta_juego(base / "Juego"))

    problemas.extend(_auditar_xlsx_en_data(base))
    problemas.extend(_auditar_rutas_legacy(raiz_pkg))
    return problemas


def texto_referencia_datos_juego() -> str:
    """Texto plano para documentación o consola (esquemas JSON del jugador)."""
    lineas = [
        "Data/Juego/ — datos locales del jugador (generados al jugar)",
        "",
        "  preferencias_grafico.json",
        f"  {_FICHERO_ESTADISTICAS_JUGADOR}",
        "  *.txt (informes y feedback)",
        "",
        "Catálogo de modos: Juego/presets.json",
        "",
        "preferencias_grafico.json — campos:",
    ]
    for clave, desc in CAMPOS_PREFERENCIAS.items():
        lineas.append(f"  {clave}: {desc}")
    lineas.extend(["", f"{_FICHERO_ESTADISTICAS_JUGADOR} — secciones:"])
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
