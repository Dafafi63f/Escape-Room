#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Taxonomía compartida de filtros de bloque (resistencia y escape room).

Cinco tipos principales de puerta en escape:

1. **Materia** (📕 en carta) — subtipos en barra: perfiles de dificultad y/o tipo (🟢🔤…).
2. **Bloque** (🗃️ en carta) — subtipos en barra: grupo, curso, semestre, periodo (🧩🎓📋🧭).
3. **Reposo** (💤) — sin subtipos (id catálogo ``descanso``).
4. **Tienda** (🛒) — sin subtipos.
5. **Jefe** (👑) — sin subtipos; bloque largo sobre puerta bloque (grupo).

Solo materia y bloque admiten subtipos. Teoría/cálculo global no son tipo
principal: el filtro por tipo va como subtipo de puerta de materia.

En carta: iconos de contenido (materia/bloque) o pausa (reposo/tienda)
y rasgos combinables delante/detrás (niebla, botín…).
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "TipoFiltroBloque",
    "TipoPuertaPrincipalEscape",
    "clasificar_filtro_bloque",
    "clasificar_filtro_evento_escape",
    "es_filtro_subtipo_bloque",
    "familia_puerta_contenido_escape",
    "kind_filtro_bloque",
    "requiere_icono_bloque_escape",
    "tipos_filtro_resistencia",
]


class TipoFiltroBloque(str, Enum):
    """Filtros de pool en bloques (resistencia; en escape solo materia y bloque)."""

    MATERIA = "materia"
    TIPO_TEORIA = "tipo_teoria"
    TIPO_CALCULO = "tipo_calculo"
    GRUPO = "grupo"
    CURSO = "curso"
    SEMESTRE = "semestre"
    PERIODO = "periodo"


class TipoPuertaPrincipalEscape(str, Enum):
    """Los cinco tipos principales de puerta en escape."""

    MATERIA = "materia"
    BLOQUE = "bloque"
    REPOSO = "reposo"
    TIENDA = "tienda"
    JEFE = "jefe"


_SUBTIPOS_FILTRO_BLOQUE: frozenset[TipoFiltroBloque] = frozenset({
    TipoFiltroBloque.GRUPO,
    TipoFiltroBloque.CURSO,
    TipoFiltroBloque.SEMESTRE,
    TipoFiltroBloque.PERIODO,
})

tipos_filtro_resistencia: frozenset[TipoFiltroBloque] = frozenset(TipoFiltroBloque)


def es_filtro_subtipo_bloque(tipo: TipoFiltroBloque) -> bool:
    return tipo in _SUBTIPOS_FILTRO_BLOQUE


def familia_puerta_contenido_escape(tipo: TipoFiltroBloque) -> TipoPuertaPrincipalEscape:
    """Mapea un filtro de pool a materia o bloque (puertas con preguntas)."""
    if tipo == TipoFiltroBloque.MATERIA:
        return TipoPuertaPrincipalEscape.MATERIA
    if es_filtro_subtipo_bloque(tipo):
        return TipoPuertaPrincipalEscape.BLOQUE
    raise ValueError(
        f"Filtro {tipo!r} no es puerta de materia ni bloque en escape "
        f"(teoría/cálculo van como subtipo de materia)."
    )


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
    """Clasifica el filtro de contenido de una puerta escape (materia o bloque)."""
    del tipos_permitidos  # reserva de API; hoy el filtro no discrimina por tipo.
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
    if grupo or usa_grupo:
        return TipoFiltroBloque.GRUPO
    if curso and semestre:
        return TipoFiltroBloque.PERIODO
    if curso:
        return TipoFiltroBloque.CURSO
    if semestre:
        return TipoFiltroBloque.SEMESTRE
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
    """Sin icono de tamaño en barra: 3/5/10 van en el pie de la carta (👑 solo para 10)."""
    del tipo
    return False
