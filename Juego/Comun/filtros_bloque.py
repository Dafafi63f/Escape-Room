#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Taxonomía compartida de filtros de bloque (resistencia y escape room).

🎯 indica un bloque de 3/5 preguntas con filtro distinto de materia única.
En escape, cada filtro amplio lleva además su icono de contenido (📕, 🗃️, 🎓…).
Los perfiles de dificultad son solo de escape; resistencia escala con el tiempo.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "TipoFiltroBloque",
    "clasificar_filtro_bloque",
    "clasificar_filtro_evento_escape",
    "kind_filtro_bloque",
    "requiere_icono_bloque_escape",
    "tipos_filtro_resistencia",
]


class TipoFiltroBloque(str, Enum):
    """Filtros posibles en bloques de 3/5 preguntas (sin contar jefe)."""

    MATERIA = "materia"
    TIPO_TEORIA = "tipo_teoria"
    TIPO_CALCULO = "tipo_calculo"
    GRUPO = "grupo"
    CURSO = "curso"
    SEMESTRE = "semestre"
    PERIODO = "periodo"


tipos_filtro_resistencia: frozenset[TipoFiltroBloque] = frozenset(TipoFiltroBloque)


def clasificar_filtro_bloque(
    *,
    materia: str | None = None,
    tipo: str | None = None,
    grupo: str | None = None,
    curso: str | None = None,
    semestre: str | None = None,
    es_jefe: bool = False,
) -> TipoFiltroBloque | None:
    """Clasifica un ``BloqueFiltroActivo`` de resistencia."""
    if es_jefe:
        return None
    if materia:
        return TipoFiltroBloque.MATERIA
    if tipo == "Teoria":
        return TipoFiltroBloque.TIPO_TEORIA
    if tipo == "Calculo":
        return TipoFiltroBloque.TIPO_CALCULO
    if grupo:
        return TipoFiltroBloque.GRUPO
    if curso and semestre:
        return TipoFiltroBloque.PERIODO
    if curso:
        return TipoFiltroBloque.CURSO
    if semestre:
        return TipoFiltroBloque.SEMESTRE
    return None


def clasificar_filtro_evento_escape(
    *,
    definicion_id: str,
    materia: str | None = None,
    grupo: str | None = None,
    curso: str | None = None,
    semestre: str | None = None,
    tipos_permitidos: frozenset[str] | None = None,
    usa_grupo: bool = False,
    ambito: str = "materia",
) -> TipoFiltroBloque:
    """Clasifica el filtro de contenido de una puerta escape."""
    if definicion_id == "puerta_grupo" or ambito == "grupo":
        return TipoFiltroBloque.GRUPO
    if definicion_id == "puerta_materia" or ambito == "materia":
        return TipoFiltroBloque.MATERIA
    if definicion_id == "puerta_periodo" or ambito == "periodo":
        return TipoFiltroBloque.PERIODO
    if definicion_id == "puerta_curso" or ambito == "curso":
        return TipoFiltroBloque.CURSO
    if definicion_id == "puerta_semestre" or ambito == "semestre":
        return TipoFiltroBloque.SEMESTRE
    if definicion_id == "puerta_tipo_teoria" or ambito == "tipo_teoria":
        return TipoFiltroBloque.TIPO_TEORIA
    if definicion_id == "puerta_tipo_calculo" or ambito == "tipo_calculo":
        return TipoFiltroBloque.TIPO_CALCULO
    if grupo or usa_grupo:
        return TipoFiltroBloque.GRUPO
    if curso and semestre:
        return TipoFiltroBloque.PERIODO
    if curso:
        return TipoFiltroBloque.CURSO
    if semestre:
        return TipoFiltroBloque.SEMESTRE
    if tipos_permitidos == frozenset({"Teoria"}):
        return TipoFiltroBloque.TIPO_TEORIA
    if tipos_permitidos == frozenset({"Calculo"}):
        return TipoFiltroBloque.TIPO_CALCULO
    if materia:
        return TipoFiltroBloque.MATERIA
    return TipoFiltroBloque.MATERIA


def kind_filtro_bloque(tipo: TipoFiltroBloque) -> str:
    """Clave para variedad de bloques vistos en resistencia."""
    if tipo == TipoFiltroBloque.TIPO_TEORIA:
        return "tipo:Teoria"
    if tipo == TipoFiltroBloque.TIPO_CALCULO:
        return "tipo:Calculo"
    return tipo.value


def requiere_icono_bloque_escape(tipo: TipoFiltroBloque) -> bool:
    """🎯 en carta escape solo si el filtro no es materia única."""
    return tipo != TipoFiltroBloque.MATERIA
