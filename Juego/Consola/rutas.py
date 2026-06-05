#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolución de rutas a datos y persistencia (script, exe, PyInstaller)."""

from __future__ import annotations

import sys
from pathlib import Path

_CONSOLA_DIR = Path(__file__).resolve().parent
_JUEGO_DIR = _CONSOLA_DIR.parent


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


def _buscar_archivo(
    nombre: str,
    preferidas: tuple[str, ...],
    *,
    bajo_data: bool = True,
) -> Path:
    candidatos: list[Path] = []
    vistos: set[Path] = set()
    for raiz in _roots_busqueda():
        if raiz in vistos:
            continue
        vistos.add(raiz)
        candidatos.append(raiz)

    if bajo_data:
        for raiz in candidatos:
            p = raiz / "Data" / nombre
            if p.exists():
                return p

    for raiz in candidatos:
        p = raiz / nombre
        if p.exists():
            return p

    for raiz in candidatos:
        coincidencias = sorted(
            raiz.rglob(nombre),
            key=lambda p: (
                0 if p.parent.name.lower() == "data" else 1,
                len(p.parts),
                str(p),
            ),
        )
        if coincidencias:
            return coincidencias[0]

    raise FileNotFoundError(f"No se encontró '{nombre}' en rutas accesibles.")


def resolver_dataset() -> Path:
    return _buscar_archivo("Preguntas.csv", ("Preguntas.csv",))


def resolver_listado_materias() -> Path:
    return _buscar_archivo("listado_materias.csv", ("listado_materias.csv",))


def resolver_plantillas() -> Path:
    return _buscar_archivo("plantillas.json", ("plantillas.json",))


def resolver_historico_qualificacions() -> Path:
    return _buscar_archivo(
        "Historic_qualificacions_MatCAD_completo.csv",
        ("Historic_qualificacions_MatCAD_completo.csv",),
    )


def resolver_dir_informes() -> Path:
    """Carpeta donde se guardan los informes de examen (.txt)."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent / "Informes"
    else:
        base = _JUEGO_DIR / "Informes"
    base.mkdir(parents=True, exist_ok=True)
    return base


def ruta_informe_para_usuario(archivo: Path) -> str:
    """Ruta corta sin caracteres problemáticos para la consola de Windows."""
    return f"Juego/Informes/{archivo.name}"


def resolver_dir_feedback() -> Path:
    """Carpeta donde se guardan los avisos del modo feedback."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent / "Feedback"
    else:
        base = _JUEGO_DIR / "Feedback"
    base.mkdir(parents=True, exist_ok=True)
    return base


def ruta_feedback_para_usuario(archivo: Path) -> str:
    return f"Juego/Feedback/{archivo.name}"


def resolver_config_creador_privado() -> Path | None:
    """JSON local del creador (datos personales y secretos; no se versiona)."""
    try:
        return _buscar_archivo(
            "creador_privado.json",
            ("creador_privado.json",),
        )
    except FileNotFoundError:
        return None


PATH_PREGUNTAS = resolver_dataset()
PATH_MATERIAS = resolver_listado_materias()
