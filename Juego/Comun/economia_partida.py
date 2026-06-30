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
    OfertaTienda,
    aplicar_bonificacion,
    articulo_por_id,
    articulo_tienda_por_id,
    bonificacion_aplicable,
    es_bonificacion,
    es_pack,
    es_powerup,
    resolver_contenido_pack,
)
from Comun.reglas import sumar_puntos_arcade

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

# Amuleto arcade: bonus en el próximo acierto (escala con la partida).
BONUS_AMULETO_BASE = 20
_MULT_MAX_BONUS_AMULETO_RESISTENCIA = 3.0
_MULT_MAX_BONUS_AMULETO_ESCAPE = 2.5
_ROI_MIN_AMULETO_COMPRA = 1.3

ARTICULOS_COMPRA_RESISTENCIA = frozenset(
    {
        "fifty_fifty",
        "bomba",
        "comodin",
        "descarte_inteligente",
        "skip",
        "tiempo_extra",
        "tiempo_lento",
        "escudo",
        "sello_purga",
        "cambio",
        "segunda_oportunidad",
        "doble_o_nada",
        "racha_congelada",
        "pack_ayudas",
        "pack_random_3",
        "pack_supervivencia",
        "vida_refuerzo",
        "amuleto_puntos",
    }
)

# Variación de precio en tienda escape y ofertas compra (resistencia).
PROB_PRECIO_GRATIS_TIENDA = 0.10
PROB_PRECIO_DESCUENTO_TIENDA = 0.32
PROB_PRECIO_INFLACION_TIENDA = 0.18
_RANGO_DESCUENTO = (0.10, 0.30)
_RANGO_INFLACION = (0.10, 0.25)


def peso_articulo(articulo_id: str) -> float:
    if es_bonificacion(articulo_id):
        return PESO_BONIFICACION
    if es_pack(articulo_id):
        return PESO_POWERUP * 0.75
    return PESO_POWERUP


def variar_precio_tienda(
    rng: random.Random,
    precio_base: int,
    *,
    gratis_permitido: bool,
) -> tuple[int, str | None]:
    """Devuelve (precio efectivo, etiqueta opcional: Gratis, -20 %, +15 %)."""
    if precio_base <= 0:
        return 0, "Gratis"
    if gratis_permitido and rng.random() < PROB_PRECIO_GRATIS_TIENDA:
        return 0, "Gratis"
    roll = rng.random()
    if roll < PROB_PRECIO_DESCUENTO_TIENDA:
        desc = rng.uniform(*_RANGO_DESCUENTO)
        precio = max(1, int(round(precio_base * (1.0 - desc))))
        return precio, f"-{int(desc * 100)}%"
    if roll < PROB_PRECIO_DESCUENTO_TIENDA + PROB_PRECIO_INFLACION_TIENDA:
        inc = rng.uniform(*_RANGO_INFLACION)
        precio = int(round(precio_base * (1.0 + inc)))
        return precio, f"+{int(inc * 100)}%"
    return precio_base, None


def oferta_desde_articulo(
    rng: random.Random,
    articulo: ArticuloTienda,
    *,
    gratis_permitido: bool,
    precio_base: int | None = None,
) -> OfertaTienda:
    base = precio_base if precio_base is not None else articulo.precio
    precio_ef, etiqueta = variar_precio_tienda(
        rng, base, gratis_permitido=gratis_permitido
    )
    return OfertaTienda(
        articulo=articulo,
        precio_efectivo=precio_ef,
        etiqueta_precio=etiqueta,
    )


def precio_base_articulo(articulo_id: str) -> int:
    """Precio base compartido (escape = resistencia al inicio de partida)."""
    return articulo_tienda_por_id(articulo_id).precio


def _mult_bonus_amuleto_resistencia(numero_pregunta: int) -> float:
    from Comun.resistencia_motor import factor_progreso_resistencia

    t = factor_progreso_resistencia(numero_pregunta)
    return 1.0 + (_MULT_MAX_BONUS_AMULETO_RESISTENCIA - 1.0) * t


def _mult_bonus_amuleto_escape(numero_sala: int) -> float:
    t = min(1.0, max(0.0, (numero_sala - 1) / 29.0))
    return 1.0 + (_MULT_MAX_BONUS_AMULETO_ESCAPE - 1.0) * t


def bonus_amuleto_arcade(
    *,
    numero_pregunta: int | None = None,
    numero_sala: int | None = None,
) -> int:
    """Bonus de pts en el próximo acierto (loot, botín, etc.)."""
    if numero_pregunta is not None:
        mult = _mult_bonus_amuleto_resistencia(numero_pregunta)
    elif numero_sala is not None:
        mult = _mult_bonus_amuleto_escape(numero_sala)
    else:
        mult = 1.0
    return max(BONUS_AMULETO_BASE, int(round(BONUS_AMULETO_BASE * mult)))


def bonus_amuleto_tras_compra(
    precio_pagado: int,
    *,
    numero_pregunta: int | None = None,
    numero_sala: int | None = None,
) -> int:
    """Al comprar: al menos rentable frente al precio y escalado con la partida."""
    escalado = bonus_amuleto_arcade(
        numero_pregunta=numero_pregunta,
        numero_sala=numero_sala,
    )
    minimo = max(1, int(round(precio_pagado * _ROI_MIN_AMULETO_COMPRA)))
    return max(escalado, minimo)


def texto_bonus_amuleto(bonus: int) -> str:
    return f"+{bonus} pts en tu próximo acierto"


def puntos_penalizacion_escalados(base: int, numero_pregunta: int) -> int:
    """Penalización de pts en apuestas/riesgo (misma curva que precios en resistencia)."""
    if base <= 0:
        return 0
    from Comun.resistencia_motor import factor_progreso_resistencia

    mult = 1.0 + _INFLACION_MAX_PRECIO_RESISTENCIA * factor_progreso_resistencia(
        numero_pregunta
    )
    return max(base, int(round(base * mult)))


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
    precio_efectivo: int | None = None,
) -> str | None:
    """None si se puede comprar ahora; mensaje de error en caso contrario."""
    if comprados_en_visita is not None and articulo_id in comprados_en_visita:
        return "Ya compraste este objeto en esta visita."
    art = articulo_tienda_por_id(articulo_id)
    precio = art.precio if precio_efectivo is None else precio_efectivo
    if estado.puntos_arcade < precio:
        return f"Necesitas {precio} pts (tienes {estado.puntos_arcade})."
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
) -> tuple[OfertaTienda | None, ...]:
    """Tres slots por visita; precios con descuento, inflación o gratis (máx. 1)."""
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

    gratis_disponible = True
    ofertas: list[OfertaTienda | None] = []
    for art in elegidos:
        if art is None:
            ofertas.append(None)
            continue
        oferta = oferta_desde_articulo(
            rng, art, gratis_permitido=gratis_disponible
        )
        if oferta.etiqueta_precio == "Gratis":
            gratis_disponible = False
        ofertas.append(oferta)
    return tuple(ofertas)


def comprar_articulo(
    estado: EstadoPartida,
    inventario,
    articulo_id: str,
    *,
    comprados_en_visita: set[str] | frozenset[str] | None = None,
    vidas_max: int | None = None,
    precio_efectivo: int | None = None,
    rng: random.Random | None = None,
    numero_pregunta: int | None = None,
    numero_sala: int | None = None,
    loot_pool: tuple[str, ...] | None = None,
) -> str | None:
    """Resta puntos arcade; powerups al inventario, bonificaciones al instante."""
    art = articulo_por_id(articulo_id)
    precio = art.precio if precio_efectivo is None else precio_efectivo
    if comprados_en_visita is not None and articulo_id in comprados_en_visita:
        return "Ya compraste este objeto en esta visita."
    if estado.puntos_arcade < precio:
        return f"Necesitas {precio} pts (tienes {estado.puntos_arcade})."
    if es_bonificacion(articulo_id):
        if not bonificacion_aplicable(articulo_id, estado, vidas_max=vidas_max):
            return "Esta bonificación no aplica ahora."
    estado.puntos_arcade, _ = sumar_puntos_arcade(estado.puntos_arcade, -precio)
    if es_bonificacion(articulo_id):
        return aplicar_bonificacion(
            articulo_id,
            estado,
            inventario,
            vidas_max=vidas_max,
            numero_pregunta=numero_pregunta,
            numero_sala=numero_sala,
            precio_pagado=precio,
        )
    if es_pack(articulo_id):
        rng_pack = rng or random.Random()
        pool = loot_pool
        for pid, cant in resolver_contenido_pack(
            articulo_id, rng_pack, inventario, loot_pool=pool
        ):
            inventario.agregar(pid, cant)
        return None
    if es_powerup(articulo_id):
        inventario.agregar(articulo_id)
        return None
    return f"Artículo desconocido: {articulo_id!r}"


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
    return es_powerup(articulo_id) or es_pack(articulo_id)


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
    rng: random.Random | None = None,
    numero_pregunta: int | None = None,
    precio_pagado: int | None = None,
) -> str | None:
    """Aplica compra en resistencia: powerup al inventario, bonificación al instante."""
    tope = vidas_max if vidas_max is not None else getattr(er, "vidas_max", None)
    if es_bonificacion(articulo_id):
        if precio_pagado is None and numero_pregunta is not None:
            precio_pagado = precio_resistencia_articulo(articulo_id, numero_pregunta)
        return aplicar_bonificacion(
            articulo_id,
            estado,
            er,
            vidas_max=tope,
            numero_pregunta=numero_pregunta,
            precio_pagado=precio_pagado,
        )
    if es_pack(articulo_id):
        rng_pack = rng or random.Random()
        for pid, cant in resolver_contenido_pack(articulo_id, rng_pack, er.inventario):
            er.agregar_powerup(pid, cant)
        return None
    if not es_powerup(articulo_id):
        return f"Artículo desconocido: {articulo_id!r}"
    er.agregar_powerup(articulo_id)
    return None
