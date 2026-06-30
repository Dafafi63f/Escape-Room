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
    """``CHANGELOG_PROYECTO.md`` en ``Docs/``."""
    raiz = _raiz_repo()
    docs = _docs_dir()
    candidatos = [
        docs / FICHERO_CHANGELOG_PROYECTO,
        raiz / FICHERO_CHANGELOG_PROYECTO,
    ]
    return _primer_existente(candidatos)


def resolver_changelog_juego_grafico() -> Path | None:
    """``CHANGELOG_JUEGO.md`` en ``Docs/`` o ``Juego/`` (paquete mínimo)."""
    raiz = _raiz_repo()
    docs = _docs_dir()
    candidatos = [
        docs / FICHERO_CHANGELOG_JUEGO,
        juego_dir() / FICHERO_CHANGELOG_JUEGO,
        raiz / FICHERO_CHANGELOG_JUEGO,
    ]
    return _primer_existente(candidatos)


def resolver_changelog() -> Path | None:
    """Alias de ``resolver_changelog_proyecto``."""
    return resolver_changelog_proyecto()


_TITULOS_H1_OMITIR = frozenset({"novedades del juego"})
_PREFIJO_VIÑETA = "  • "
_SANGRIA_SECCION = "  "


def _anadir_parrafo_vacio(salida: list[str]) -> None:
    if salida and salida[-1] != "":
        salida.append("")


def _nivel_titulo_md(bruta: str) -> int:
    return len(bruta) - len(bruta.lstrip("#"))


def _procesar_titulo_md(bruta: str, salida: list[str]) -> None:
    nivel = _nivel_titulo_md(bruta)
    titulo = re.sub(r"^#+\s*", "", bruta.strip()).strip()
    titulo = _limpiar_marcado_inline(titulo)
    if not titulo:
        return
    if nivel == 1 and titulo.casefold() in _TITULOS_H1_OMITIR:
        return
    _anadir_parrafo_vacio(salida)
    if nivel >= 2:
        salida.append(f"--- {titulo} ---")
    else:
        salida.append(titulo)


def _limpiar_marcado_inline(texto: str) -> str:
    """Quita negrita/cursiva markdown residual para lectura en pygame."""
    previo = None
    while previo != texto:
        previo = texto
        texto = re.sub(r"\*\*([^*]+)\*\*", r"\1", texto)
        texto = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", texto)
    return texto


def _limpiar_texto_plano(bruta: str) -> str:
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", bruta)
    texto = texto.replace("`", "")
    texto = _limpiar_marcado_inline(texto)
    return texto.strip()


def _procesar_viñeta(limpia: str, salida: list[str]) -> bool:
    if not limpia.startswith("- "):
        return False
    cuerpo = _limpiar_texto_plano(limpia[2:])
    if cuerpo:
        salida.append(f"{_PREFIJO_VIÑETA}{cuerpo}")
    return True


def _recortar_referencia_proyecto(texto: str) -> str:
    partes = re.split(
        r"\.\s*El historial técnico del TFG\b",
        texto,
        maxsplit=1,
        flags=re.IGNORECASE,
    )
    principal = partes[0].strip()
    if not principal:
        return ""
    if not principal.endswith("."):
        principal += "."
    return principal


def _procesar_linea_texto(bruta: str, salida: list[str]) -> None:
    limpia = bruta.strip()
    if _procesar_viñeta(limpia, salida):
        return
    texto_linea = _recortar_referencia_proyecto(_limpiar_texto_plano(bruta))
    if texto_linea:
        salida.append(texto_linea)


def _es_nota_footer_desarrollo(limpia: str) -> bool:
    return limpia.casefold().startswith("al añadir algo")


def simplificar_changelog_para_ui(texto: str) -> str:
    """Quita tablas y marcado pesado; conserva títulos y párrafos legibles."""
    salida: list[str] = []
    en_bloque_codigo = False
    for linea in texto.splitlines():
        bruta = linea.rstrip()
        limpia = bruta.strip()
        if _es_nota_footer_desarrollo(limpia):
            break
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
            continue
        if limpia.startswith("#"):
            _procesar_titulo_md(bruta, salida)
            continue
        _procesar_linea_texto(bruta, salida)
    while salida and salida[-1] == "":
        salida.pop()
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
