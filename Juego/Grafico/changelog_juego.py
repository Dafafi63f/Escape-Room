#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lectura de changelogs para mostrarlos en el juego (pantalla Info)."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from Comun.rutas import juego_dir

__all__ = [
    "cargar_changelog_juego",
    "cargar_changelog_juego_grafico",
    "cargar_changelog_proyecto",
    "resolver_changelog",
    "resolver_changelog_juego_grafico",
    "resolver_changelog_proyecto",
    "simplificar_changelog_para_ui",
]

FICHERO_CHANGELOG_PROYECTO = "CHANGELOG_PROYECTO.md"
FICHERO_CHANGELOG_JUEGO = "CHANGELOG_JUEGO.md"
_SUBDIR_DOCS = "Docs"
_LEGACY_CHANGELOG_PROYECTO = "CHANGELOG.md"
_LEGACY_CHANGELOG_JUEGO = "CHANGELOG_JUEGO_GRAFICO.md"


def _raiz_repo() -> Path:
    import sys

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return juego_dir().parent


def _docs_dir() -> Path:
    return _raiz_repo() / _SUBDIR_DOCS


def _primer_existente(candidatos: list[Path]) -> Path | None:
    for path in candidatos:
        if path.is_file():
            return path
    return None


def resolver_changelog_proyecto() -> Path | None:
    """``CHANGELOG_PROYECTO.md`` en ``Docs/`` (o raíz legada)."""
    raiz = _raiz_repo()
    docs = _docs_dir()
    candidatos = [
        docs / FICHERO_CHANGELOG_PROYECTO,
        raiz / FICHERO_CHANGELOG_PROYECTO,
        raiz / _LEGACY_CHANGELOG_PROYECTO,
    ]
    for base in (raiz, *raiz.parents):
        for nombre in (FICHERO_CHANGELOG_PROYECTO, _LEGACY_CHANGELOG_PROYECTO):
            p = base / nombre
            if p not in candidatos:
                candidatos.append(p)
    return _primer_existente(candidatos)


def resolver_changelog_juego_grafico() -> Path | None:
    """``CHANGELOG_JUEGO.md`` en ``Docs/`` (o raíz legada)."""
    raiz = _raiz_repo()
    docs = _docs_dir()
    candidatos = [
        docs / FICHERO_CHANGELOG_JUEGO,
        raiz / FICHERO_CHANGELOG_JUEGO,
        raiz / _LEGACY_CHANGELOG_JUEGO,
        juego_dir() / _LEGACY_CHANGELOG_JUEGO,
    ]
    for base in (raiz, *raiz.parents):
        for nombre in (FICHERO_CHANGELOG_JUEGO, _LEGACY_CHANGELOG_JUEGO):
            p = base / nombre
            if p not in candidatos:
                candidatos.append(p)
    legado_juego = juego_dir() / _LEGACY_CHANGELOG_JUEGO
    if legado_juego not in candidatos:
        candidatos.append(legado_juego)
    return _primer_existente(candidatos)


def resolver_changelog() -> Path | None:
    """Alias legado → changelog del proyecto."""
    return resolver_changelog_proyecto()


def _anadir_parrafo_vacio(salida: list[str]) -> None:
    if salida and salida[-1] != "":
        salida.append("")


def _procesar_titulo_md(limpia: str, salida: list[str]) -> None:
    titulo = re.sub(r"^#+\s*", "", limpia).strip()
    titulo = _limpiar_marcado_inline(titulo)
    if not titulo:
        return
    _anadir_parrafo_vacio(salida)
    salida.append(titulo)


def _limpiar_marcado_inline(texto: str) -> str:
    """Quita negrita/cursiva markdown residual para lectura en pygame."""
    previo = None
    while previo != texto:
        previo = texto
        texto = re.sub(r"\*\*([^*]+)\*\*", r"\1", texto)
        texto = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", texto)
    return texto


def _procesar_linea_texto(bruta: str, salida: list[str]) -> None:
    texto_linea = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", bruta)
    texto_linea = texto_linea.replace("`", "")
    texto_linea = _limpiar_marcado_inline(texto_linea)
    salida.append(texto_linea.strip())


def simplificar_changelog_para_ui(texto: str) -> str:
    """Quita tablas y marcado pesado; conserva títulos y párrafos legibles."""
    salida: list[str] = []
    en_bloque_codigo = False
    for linea in texto.splitlines():
        bruta = linea.rstrip()
        limpia = bruta.strip()
        if limpia.startswith("```"):
            en_bloque_codigo = not en_bloque_codigo
            continue
        if en_bloque_codigo:
            continue
        if not limpia:
            _anadir_parrafo_vacio(salida)
            continue
        if limpia.startswith("|"):
            continue
        if re.fullmatch(r"[-─—]{3,}", limpia):
            salida.append("")
            continue
        if limpia.startswith("#"):
            _procesar_titulo_md(limpia, salida)
            continue
        _procesar_linea_texto(bruta, salida)
    return "\n".join(salida).strip()


def _cargar_desde(
    resolver: Callable[[], Path | None],
    *,
    no_encontrado: str,
    error_lectura: str = "No se pudo leer el changelog en esta instalación.",
) -> str:
    path = resolver()
    if path is None:
        return no_encontrado
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return error_lectura
    return simplificar_changelog_para_ui(raw)


def cargar_changelog_proyecto() -> str:
    return _cargar_desde(
        resolver_changelog_proyecto,
        no_encontrado=(
            "No se encontró CHANGELOG_PROYECTO.md en esta instalación.\n\n"
            "Consulta el repositorio del proyecto para el historial técnico del TFG."
        ),
    )


def cargar_changelog_juego_grafico() -> str:
    return _cargar_desde(
        resolver_changelog_juego_grafico,
        no_encontrado=(
            "No se encontró CHANGELOG_JUEGO.md en esta instalación.\n\n"
            "Consulta el repositorio para ver las novedades del juego."
        ),
    )


def cargar_changelog_juego() -> str:
    """Changelog orientado al jugador."""
    return cargar_changelog_juego_grafico()
