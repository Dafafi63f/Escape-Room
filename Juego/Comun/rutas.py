#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolución de rutas a datos y persistencia (script, exe, PyInstaller)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

_COMUN_DIR = Path(__file__).resolve().parent
_JUEGO_DIR = _COMUN_DIR.parent
_FILES_DIR = _JUEGO_DIR.parent / "Files"

_ZonaDatos = Literal["banco", "juego"]
_LEGACY_DATA_SUBDIRS = ("CSV", "csv", "JSON", "json", "Informes", "Feedback")


def registrar_scripts_en_path() -> None:
    """Añade ``Files`` al path para importar utilidades compartidas con el juego."""
    if _FILES_DIR.is_dir() and str(_FILES_DIR) not in sys.path:
        sys.path.insert(0, str(_FILES_DIR))


def juego_dir() -> Path:
    return _JUEGO_DIR


def _roots_busqueda() -> list[Path]:
    candidatos: list[Path] = []
    vistos: set[Path] = set()

    rutas_base = [_JUEGO_DIR, Path.cwd()]
    if getattr(sys, "frozen", False):
        rutas_base.append(Path(sys.executable).resolve().parent)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        rutas_base.append(Path(meipass))

    for base in rutas_base:
        try:
            base = base.resolve()
        except OSError:
            continue
        for ruta in (base, *base.parents):
            if ruta not in vistos and ruta.exists():
                vistos.add(ruta)
                candidatos.append(ruta)
    return candidatos


def _data_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "Data"
    return _JUEGO_DIR.parent / "Data"


def _ancestros_desde_hoja(carpeta: Path) -> list[Path]:
    partes: list[Path] = []
    actual = carpeta
    while True:
        partes.append(actual)
        if actual.parent == actual:
            break
        actual = actual.parent
    return list(reversed(partes))


def _crear_directorio_si_falta(ruta: Path) -> None:
    if ruta.is_file():
        ruta.unlink()
    if ruta.is_dir():
        return
    try:
        ruta.mkdir(exist_ok=True)
    except OSError as exc:
        winerror = getattr(exc, "winerror", None)
        if (winerror == 183 or isinstance(exc, FileExistsError)) and ruta.is_dir():
            return
        raise


def _asegurar_directorio(carpeta: Path) -> Path:
    """Crea ``carpeta`` y corrige ficheros anómalos en la ruta (p. ej. tras limpieza parcial)."""
    for ruta in _ancestros_desde_hoja(carpeta):
        _crear_directorio_si_falta(ruta)
    return carpeta


def _dir_banco() -> Path:
    """Directorio plano ``Data/Banco/`` (banco de preguntas y catálogos)."""
    return _asegurar_directorio(_data_root() / "Banco")


def _dir_juego_datos() -> Path:
    """Directorio plano ``Data/Juego/`` (estado local del jugador)."""
    return _asegurar_directorio(_data_root() / "Juego")


def _dir_data_escritura() -> Path:
    return _dir_juego_datos()


def _candidatos_bajo_data(raiz: Path, nombre: str, *, zona: _ZonaDatos) -> list[Path]:
    data = raiz / "Data"
    if not data.is_dir():
        return []
    principal = "Banco" if zona == "banco" else "Juego"
    secundario = "Juego" if zona == "banco" else "Banco"
    orden: list[Path] = [
        data / principal / nombre,
        data / secundario / nombre,
    ]
    for subdir in _LEGACY_DATA_SUBDIRS:
        orden.append(data / subdir / nombre)
    orden.append(data / nombre)
    return orden


def _buscar_archivo(
    nombre: str,
    preferidas: tuple[str, ...],
    *,
    bajo_data: bool = True,
    zona: _ZonaDatos = "banco",
) -> Path:
    candidatos_raiz: list[Path] = []
    vistos: set[Path] = set()
    for raiz in _roots_busqueda():
        if raiz in vistos:
            continue
        vistos.add(raiz)
        candidatos_raiz.append(raiz)

    if bajo_data:
        for raiz in candidatos_raiz:
            for p in _candidatos_bajo_data(raiz, nombre, zona=zona):
                if p.exists():
                    return p

    for raiz in candidatos_raiz:
        p = raiz / nombre
        if p.exists():
            return p

    for raiz in candidatos_raiz:
        coincidencias = sorted(
            raiz.rglob(nombre),
            key=lambda p: (
                0 if p.parent.name.lower() in {"data", "banco", "juego", "csv", "json"} else 1,
                len(p.parts),
                str(p),
            ),
        )
        if coincidencias:
            return coincidencias[0]

    raise FileNotFoundError(f"No se encontró '{nombre}' en rutas accesibles.")


def _ruta_juego_escritura(nombre: str) -> Path:
    return _dir_juego_datos() / nombre


def _ruta_json_escritura(nombre: str) -> Path:
    """Alias: JSON de estado local del jugador en ``Data/Juego/``."""
    return _ruta_juego_escritura(nombre)


def resolver_dataset() -> Path:
    return _buscar_archivo("Preguntas.csv", ("Preguntas.csv",), zona="banco")


def resolver_listado_materias() -> Path:
    return _buscar_archivo("listado_materias.csv", ("listado_materias.csv",), zona="banco")


def resolver_plantillas() -> Path:
    return _buscar_archivo("plantillas.json", ("plantillas.json",), zona="banco")


def resolver_preguntas_resistencia() -> Path:
    return _buscar_archivo("preguntas_resistencia.json", ("preguntas_resistencia.json",), zona="juego")


def resolver_presets() -> Path:
    """Catálogo unificado de presets (historia, escape room, resistencia…)."""
    for nombre in ("presets.json", "presets_historia.json"):
        try:
            return _buscar_archivo(nombre, (nombre,), zona="juego")
        except FileNotFoundError:
            continue
    raise FileNotFoundError(
        "No se encontró el catálogo de presets (presets.json o presets_historia.json)."
    )


def resolver_presets_historia() -> Path:
    return resolver_presets()


def resolver_presets_especiales() -> Path:
    return resolver_presets()


def resolver_ranking_resistencia() -> Path:
    """JSON local del ranking de resistencia."""
    base = _ruta_juego_escritura("ranking_resistencia.json")
    if not base.exists():
        base.write_text('{"version": 1, "records": []}', encoding="utf-8")
    return base


def resolver_historico_qualificacions() -> Path:
    return _buscar_archivo(
        "Historic_qualificacions_MatCAD_completo.csv",
        ("Historic_qualificacions_MatCAD_completo.csv",),
        zona="banco",
    )


def resolver_config_creador_privado() -> Path | None:
    """JSON local del creador (datos personales y secretos; no se versiona)."""
    try:
        return _buscar_archivo(
            "creador_privado.json",
            ("creador_privado.json",),
            zona="banco",
        )
    except FileNotFoundError:
        return None


def resolver_ruta_creador_privado_defecto() -> Path:
    """Ruta canónica para crear ``creador_privado.json`` si no existe."""
    existente = resolver_config_creador_privado()
    if existente is not None:
        return existente
    return _dir_banco() / "creador_privado.json"


def resolver_dir_informes() -> Path:
    """Carpeta donde se guardan los informes de examen (.txt)."""
    return _dir_juego_datos()


def ruta_informe_para_usuario(archivo: Path) -> str:
    """Ruta corta sin caracteres problemáticos para la terminal de Windows."""
    return f"Data/Juego/{archivo.name}"


def resolver_dir_feedback() -> Path:
    """Carpeta donde se guardan los avisos del modo feedback."""
    return _dir_juego_datos()


def ruta_feedback_para_usuario(archivo: Path) -> str:
    return f"Data/Juego/{archivo.name}"


_path_preguntas: Path | None = None
_path_materias: Path | None = None


def path_preguntas() -> Path:
    """Ruta a ``Preguntas.csv`` (resuelve en la primera llamada)."""
    global _path_preguntas
    if _path_preguntas is None:
        _path_preguntas = resolver_dataset()
    return _path_preguntas


def path_materias() -> Path:
    """Ruta a ``listado_materias.csv`` (resuelve en la primera llamada)."""
    global _path_materias
    if _path_materias is None:
        _path_materias = resolver_listado_materias()
    return _path_materias


def __getattr__(name: str) -> Path:
    if name == "PATH_PREGUNTAS":
        return path_preguntas()
    if name == "PATH_MATERIAS":
        return path_materias()
    raise AttributeError(f"module {name!r} has no attribute {name!r}")
