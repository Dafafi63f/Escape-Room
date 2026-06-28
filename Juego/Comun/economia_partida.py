#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Economía arcade unificada: precios, tienda escape y ofertas de resistencia.

Compartido entre la tienda del escape room y los eventos sí/no de resistencia.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from Comun.motor_nucleo import EstadoPartida
from Comun.objetos_partida import (
    ArticuloTienda,
    CATALOGO_ARTICULOS,
    aplicar_bonificacion,
    articulo_por_id,
    articulo_tienda_por_id,
    bonificacion_aplicable,
    es_bonificacion,
    es_powerup,
)
from Comun.reglas_partida import sumar_puntos_arcade

if TYPE_CHECKING:
    from Comun.escape_room import PuertaEscape

ARTICULOS_POR_VISITA_TIENDA = 3
MAX_SLOTS_VACIOS_TIENDA = 1

# Tienda escape y ofertas resistencia: powerup > bonificación.
PESO_POWERUP = 1.0
PESO_BONIFICACION = 0.55

# Ofertas sí/no en resistencia sin artículo de catálogo (precio base propio).
PRECIO_BASE_VIDA_OFERTA_RESISTENCIA = 50
PRECIO_BASE_SORPRESA_RESISTENCIA = 28
PRECIO_BASE_PURGA_MALDICION_RESISTENCIA = 45

# En resistencia el precio sube con el progreso; en escape se usa siempre el base.
_INFLACION_MAX_PRECIO_RESISTENCIA = 1.0

ARTICULOS_COMPRA_RESISTENCIA = frozenset(
    {
        "fifty_fifty",
        "bomba",
        "skip",
        "tiempo_extra",
        "escudo",
        "cambio",
        "vida_refuerzo",
        "amuleto_puntos",
    }
)


def peso_articulo(articulo_id: str) -> float:
    if es_bonificacion(articulo_id):
        return PESO_BONIFICACION
    return PESO_POWERUP


def precio_base_articulo(articulo_id: str) -> int:
    """Precio base compartido (escape = resistencia al inicio de partida)."""
    return articulo_tienda_por_id(articulo_id).precio


def precio_resistencia_escalado(precio_base: int, numero_pregunta: int) -> int:
    """Escala el precio base según la pregunta (escape no usa esta función)."""
    from Comun.resistencia_motor import factor_progreso_resistencia

    mult = 1.0 + _INFLACION_MAX_PRECIO_RESISTENCIA * factor_progreso_resistencia(
        numero_pregunta
    )
    return max(1, int(round(precio_base * mult)))


def precio_resistencia_articulo(articulo_id: str, numero_pregunta: int) -> int:
    return precio_resistencia_escalado(
        precio_base_articulo(articulo_id), numero_pregunta
    )


def precio_resistencia_oferta(
    numero_pregunta: int,
    *,
    articulo_id: str | None = None,
    tipo: str | None = None,
) -> int:
    """Precio de una oferta sí/no en resistencia (compra u otros gastos en pts)."""
    if articulo_id is not None:
        return precio_resistencia_articulo(articulo_id, numero_pregunta)
    bases: dict[str, int] = {
        "vida": PRECIO_BASE_VIDA_OFERTA_RESISTENCIA,
        "amuleto": precio_base_articulo("amuleto_puntos"),
        "sorpresa": PRECIO_BASE_SORPRESA_RESISTENCIA,
        "purga_maldicion": PRECIO_BASE_PURGA_MALDICION_RESISTENCIA,
    }
    if tipo not in bases:
        raise ValueError(f"Tipo de oferta sin precio base: {tipo!r}")
    return precio_resistencia_escalado(bases[tipo], numero_pregunta)


def nivel_tienda_resistencia(numero_pregunta: int) -> int:
    return max(1, min(10, numero_pregunta // 5))


def articulos_tienda_para_sala(numero_sala: int) -> tuple[ArticuloTienda, ...]:
    return tuple(a for a in CATALOGO_ARTICULOS if a.nivel_min_sala <= numero_sala)


def precio_minimo_tienda_escape(numero_sala: int) -> int | None:
    """Precio del artículo más barato disponible en la sala (None si catálogo vacío)."""
    precios = [art.precio for art in articulos_tienda_para_sala(numero_sala)]
    return min(precios) if precios else None


def articulo_comprable_tienda_escape(
    articulo_id: str,
    estado: EstadoPartida,
    *,
    vidas_max: int | None = None,
    comprados_en_visita: set[str] | frozenset[str] | None = None,
) -> str | None:
    """None si se puede comprar ahora; mensaje de error en caso contrario."""
    if comprados_en_visita is not None and articulo_id in comprados_en_visita:
        return "Ya compraste este objeto en esta visita."
    art = articulo_tienda_por_id(articulo_id)
    if estado.puntos_arcade < art.precio:
        return f"Necesitas {art.precio} pts (tienes {estado.puntos_arcade})."
    if es_bonificacion(articulo_id) and not bonificacion_aplicable(
        articulo_id, estado, vidas_max=vidas_max
    ):
        return "Esta bonificación no aplica ahora."
    return None


def articulos_comprables_tienda_escape(
    numero_sala: int,
    estado: EstadoPartida,
    *,
    vidas_max: int | None = None,
) -> tuple[ArticuloTienda, ...]:
    return tuple(
        art
        for art in articulos_tienda_para_sala(numero_sala)
        if articulo_comprable_tienda_escape(art.id, estado, vidas_max=vidas_max) is None
    )


def puede_visitar_tienda_escape(
    numero_sala: int,
    estado: EstadoPartida,
    *,
    vidas_max: int | None = None,
) -> bool:
    """Hay al menos un artículo de la sala que el jugador puede pagar y usar."""
    if estado.puntos_arcade <= 0:
        return False
    return any(
        art.precio <= estado.puntos_arcade
        for art in articulos_comprables_tienda_escape(
            numero_sala, estado, vidas_max=vidas_max
        )
    )


def _elegir_slot_tienda(
    rng: random.Random,
    pool: list[ArticuloTienda],
    usados_ids: set[str],
    *,
    estado: EstadoPartida | None,
    vidas_max: int | None,
    vacios: int,
) -> tuple[ArticuloTienda | None, int]:
    disponibles = [a for a in pool if a.id not in usados_ids]
    if not disponibles:
        return None, vacios

    for _ in range(40):
        pesos = [peso_articulo(a.id) for a in disponibles]
        candidato = rng.choices(disponibles, weights=pesos, k=1)[0]

        if es_bonificacion(candidato.id) and estado is not None:
            if not bonificacion_aplicable(
                candidato.id, estado, vidas_max=vidas_max
            ):
                if vacios < MAX_SLOTS_VACIOS_TIENDA:
                    return None, vacios + 1
                solo_pw = [a for a in disponibles if es_powerup(a.id)]
                if not solo_pw:
                    return None, vacios
                disponibles = solo_pw
                continue

        usados_ids.add(candidato.id)
        return candidato, vacios

    return None, vacios


def seleccionar_articulos_tienda_visita(
    numero_sala: int,
    *,
    rng: random.Random,
    indice_visita: int = 0,
    estado: EstadoPartida | None = None,
    vidas_max: int | None = None,
) -> tuple[ArticuloTienda | None, ...]:
    """Tres slots por visita; al menos uno asequible si hay estado y puntos."""
    pool = list(articulos_tienda_para_sala(numero_sala))
    n = ARTICULOS_POR_VISITA_TIENDA
    if not pool:
        return (None,) * n

    pool_asequible: list[ArticuloTienda] = []
    if estado is not None:
        pool = [
            art
            for art in pool
            if articulo_comprable_tienda_escape(art.id, estado, vidas_max=vidas_max)
            is None
        ]
        pool_asequible = [art for art in pool if art.precio <= estado.puntos_arcade]
        if not pool_asequible:
            return (None,) * n

    elegidos: list[ArticuloTienda | None] = []
    usados_ids: set[str] = set()
    vacios = 0

    if pool_asequible:
        barato = min(pool_asequible, key=lambda art: art.precio)
        elegidos.append(barato)
        usados_ids.add(barato.id)
    else:
        primer, vacios = _elegir_slot_tienda(
            rng,
            pool,
            usados_ids,
            estado=estado,
            vidas_max=vidas_max,
            vacios=vacios,
        )
        elegidos.append(primer)
        if primer is not None:
            usados_ids.add(primer.id)

    while len(elegidos) < n:
        candidato, vacios = _elegir_slot_tienda(
            rng,
            pool,
            usados_ids,
            estado=estado,
            vidas_max=vidas_max,
            vacios=vacios,
        )
        elegidos.append(candidato)

    return tuple(elegidos)


def comprar_articulo(
    estado: EstadoPartida,
    inventario,
    articulo_id: str,
    *,
    comprados_en_visita: set[str] | frozenset[str] | None = None,
    vidas_max: int | None = None,
) -> str | None:
    """Resta puntos arcade; powerups al inventario, bonificaciones al instante."""
    art = articulo_por_id(articulo_id)
    if comprados_en_visita is not None and articulo_id in comprados_en_visita:
        return "Ya compraste este objeto en esta visita."
    if estado.puntos_arcade < art.precio:
        return f"Necesitas {art.precio} pts (tienes {estado.puntos_arcade})."
    if es_bonificacion(articulo_id):
        if not bonificacion_aplicable(articulo_id, estado, vidas_max=vidas_max):
            return "Esta bonificación no aplica ahora."
    estado.puntos_arcade, _ = sumar_puntos_arcade(estado.puntos_arcade, -art.precio)
    if es_bonificacion(articulo_id):
        return aplicar_bonificacion(
            articulo_id, estado, inventario, vidas_max=vidas_max
        )
    inventario.agregar(articulo_id)
    return None


def articulo_comprable_en_resistencia(
    articulo_id: str,
    *,
    numero_pregunta: int,
    estado: EstadoPartida,
    vidas_max: int,
) -> bool:
    """Artículo del catálogo disponible en oferta compra (solo si aplica ahora)."""
    art = articulo_por_id(articulo_id)
    if art.nivel_min_sala > nivel_tienda_resistencia(numero_pregunta):
        return False
    if es_bonificacion(articulo_id):
        return bonificacion_aplicable(articulo_id, estado, vidas_max=vidas_max)
    return es_powerup(articulo_id)


def articulo_comprable_resistencia(
    art: ArticuloTienda,
    *,
    numero_pregunta: int,
    estado: EstadoPartida,
    vidas_max: int,
) -> bool:
    if art.id not in ARTICULOS_COMPRA_RESISTENCIA:
        return False
    return articulo_comprable_en_resistencia(
        art.id,
        numero_pregunta=numero_pregunta,
        estado=estado,
        vidas_max=vidas_max,
    )


def elegir_articulo_compra_resistencia(
    rng: random.Random,
    numero_pregunta: int,
    estado: EstadoPartida,
    *,
    vidas_max: int,
) -> ArticuloTienda | None:
    pool = [
        art
        for art in CATALOGO_ARTICULOS
        if articulo_comprable_resistencia(
            art,
            numero_pregunta=numero_pregunta,
            estado=estado,
            vidas_max=vidas_max,
        )
    ]
    if not pool:
        return None
    pesos = [peso_articulo(art.id) for art in pool]
    return rng.choices(pool, weights=pesos, k=1)[0]


def efecto_compra_resistencia(
    articulo_id: str,
    estado: EstadoPartida,
    er,
    *,
    vidas_max: int | None = None,
) -> str | None:
    """Aplica compra en resistencia: powerup al inventario, bonificación al instante."""
    tope = vidas_max if vidas_max is not None else getattr(er, "vidas_max", None)
    if es_bonificacion(articulo_id):
        return aplicar_bonificacion(
            articulo_id, estado, er, vidas_max=tope
        )
    if not es_powerup(articulo_id):
        return f"Artículo desconocido: {articulo_id!r}"
    er.agregar_powerup(articulo_id)
    return None
