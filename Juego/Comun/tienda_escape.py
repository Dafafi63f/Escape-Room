#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tienda del escape room — fachada sobre ``objetos_partida`` y ``economia_partida``.

API pública del modo escape para la UI y los tests. Reexporta catálogo, compra,
inventario y helpers de puerta tienda. Los nombres ``CATALOGO_TIENDA_ESCAPE`` y
``ArticuloTiendaEscape`` son alias de dominio del catálogo unificado.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from Comun.economia_partida import (
    ARTICULOS_COMPRA_RESISTENCIA,
    ARTICULOS_POR_VISITA_TIENDA,
    MAX_SLOTS_VACIOS_TIENDA,
    PESO_BONIFICACION,
    PESO_POWERUP,
    PRECIO_BASE_PURGA_MALDICION_RESISTENCIA,
    PRECIO_BASE_SORPRESA_RESISTENCIA,
    PRECIO_BASE_VIDA_OFERTA_RESISTENCIA,
    articulo_comprable_en_resistencia,
    articulo_comprable_resistencia,
    articulo_comprable_tienda_escape,
    articulos_comprables_tienda_escape,
    articulos_tienda_para_sala,
    comprar_articulo,
    efecto_compra_resistencia,
    elegir_articulo_compra_resistencia,
    nivel_tienda_resistencia,
    peso_articulo,
    precio_base_articulo,
    precio_resistencia_articulo,
    precio_resistencia_escalado,
    precio_resistencia_oferta,
    precio_minimo_tienda_escape,
    puede_visitar_tienda_escape,
    seleccionar_articulos_tienda_visita,
    variar_precio_tienda,
    oferta_desde_articulo,
)
from Comun.objetos_partida import (
    ArticuloTienda,
    CATALOGO_ARTICULOS,
    IDS_BONIFICACION,
    IDS_POWERUP,
    OfertaTienda,
    EstadoInventarioEscape,
    aplicar_bonificacion,
    aplicar_loot,
    articulo_por_id,
    articulo_tienda_por_id,
    bonificacion_aplicable,
    descripcion_articulo,
    es_bonificacion,
    es_powerup,
    usar_objeto,
)

if TYPE_CHECKING:
    from Comun.escape_room import PuertaEscape

ArticuloTiendaEscape = ArticuloTienda
CATALOGO_TIENDA_ESCAPE = CATALOGO_ARTICULOS

ID_TIENDA_ESCAPE = "tienda"


def puerta_es_tienda(puerta: "PuertaEscape") -> bool:
    return ID_TIENDA_ESCAPE in puerta.modificadores.eventos_ids


def linea_detalle_tienda_puerta() -> str:
    return "Compra objetos (1 de cada tipo por visita) o continúa."
