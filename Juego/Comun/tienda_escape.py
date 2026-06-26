#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tienda del escape room: economía en puntos arcade e inventario de objetos."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from Comun.modelos import Pregunta
from Comun.motor_nucleo import EstadoPartida
from Comun.resistencia_motor import (
    puede_usar_powerup_en_pregunta,
    descripcion_powerup,
    emoji_powerup,
    etiqueta_powerup,
    letras_ocultas_bomba,
    letras_ocultas_fifty_fifty,
)

if TYPE_CHECKING:
    from Comun.escape_room import PuertaEscape

MAX_STOCK_ARTICULO_ESCAPE = 2
ARTICULOS_POR_VISITA_TIENDA = 3
ID_TIENDA_ESCAPE = "tienda"


@dataclass(frozen=True)
class ArticuloTiendaEscape:
    id: str
    nombre: str
    descripcion: str
    precio: int
    emoji: str
    nivel_min_sala: int = 1


def _art_powerup(
    powerup_id: str,
    precio: int,
    *,
    nivel_min_sala: int = 1,
    descripcion: str | None = None,
) -> ArticuloTiendaEscape:
    return ArticuloTiendaEscape(
        id=powerup_id,
        nombre=etiqueta_powerup(powerup_id),
        descripcion=descripcion or descripcion_powerup(powerup_id),
        precio=precio,
        emoji=emoji_powerup(powerup_id),
        nivel_min_sala=nivel_min_sala,
    )


CATALOGO_TIENDA_ESCAPE: tuple[ArticuloTiendaEscape, ...] = (
    _art_powerup(
        "bomba",
        12,
        descripcion="Quita 1 incorrecta. Se acumula (tras 50/50 puede dejar solo la buena).",
    ),
    _art_powerup(
        "fifty_fifty",
        25,
        descripcion="Quita 2 incorrectas al azar (sustituye otras ayudas de opciones).",
    ),
    _art_powerup("tiempo_extra", 22),
    _art_powerup("cambio", 32),
    _art_powerup("skip", 38),
    _art_powerup("escudo", 48, nivel_min_sala=6),
    ArticuloTiendaEscape(
        id="vida_refuerzo",
        nombre="Refuerzo vital",
        descripcion="+1 vida al usar (hasta tu tope actual).",
        precio=55,
        emoji="❤️",
        nivel_min_sala=4,
    ),
    ArticuloTiendaEscape(
        id="amuleto_puntos",
        nombre="Amuleto arcade",
        descripcion="+20 pts en tu próximo acierto.",
        precio=35,
        emoji="✨",
        nivel_min_sala=4,
    ),
)

_ARTICULO_POR_ID: dict[str, ArticuloTiendaEscape] = {
    a.id: a for a in CATALOGO_TIENDA_ESCAPE
}


@dataclass
class EstadoInventarioEscape:
    inventario: dict[str, int] = field(default_factory=dict)
    escudo_activo: bool = False
    tiempo_extra_seg: int = 0
    letras_ocultas_powerup: frozenset[str] = field(default_factory=frozenset)
    bonus_proximo_acierto: int = 0
    powerups_usados_en_pregunta: set[str] = field(default_factory=set)

    def cantidad(self, articulo_id: str) -> int:
        return max(0, self.inventario.get(articulo_id, 0))

    def agregar(self, articulo_id: str, cantidad: int = 1) -> None:
        if cantidad <= 0:
            return
        self.inventario[articulo_id] = self.cantidad(articulo_id) + cantidad

    def consumir(self, articulo_id: str) -> bool:
        n = self.cantidad(articulo_id)
        if n <= 0:
            return False
        if n == 1:
            self.inventario.pop(articulo_id, None)
        else:
            self.inventario[articulo_id] = n - 1
        return True

    def reset_pregunta(self) -> None:
        self.letras_ocultas_powerup = frozenset()
        self.tiempo_extra_seg = 0
        self.powerups_usados_en_pregunta.clear()

    def reiniciar_slot_pregunta(self) -> None:
        """Nueva pregunta en el mismo bloque (cambio): limpia ayudas de la anterior."""
        self.letras_ocultas_powerup = frozenset()
        self.tiempo_extra_seg = 0
        self.powerups_usados_en_pregunta.clear()


def articulo_tienda_por_id(articulo_id: str) -> ArticuloTiendaEscape:
    if articulo_id not in _ARTICULO_POR_ID:
        raise KeyError(f"Artículo de tienda desconocido: {articulo_id!r}")
    return _ARTICULO_POR_ID[articulo_id]


def articulos_tienda_para_sala(numero_sala: int) -> tuple[ArticuloTiendaEscape, ...]:
    return tuple(
        a for a in CATALOGO_TIENDA_ESCAPE if a.nivel_min_sala <= numero_sala
    )


def seleccionar_articulos_tienda_visita(
    numero_sala: int,
    *,
    semilla: int,
    indice_visita: int = 0,
) -> tuple[ArticuloTiendaEscape, ...]:
    """Tres artículos distintos por visita, elegidos del catálogo vigente en la sala."""
    pool = list(articulos_tienda_para_sala(numero_sala))
    if not pool:
        return ()
    rng = random.Random(semilla + numero_sala * 7907 + indice_visita * 101)
    rng.shuffle(pool)
    n = min(ARTICULOS_POR_VISITA_TIENDA, len(pool))
    return tuple(pool[:n])


def puerta_es_tienda(puerta: PuertaEscape) -> bool:
    return ID_TIENDA_ESCAPE in puerta.modificadores.eventos_ids


def comprar_articulo_tienda(
    estado: EstadoPartida,
    inventario: EstadoInventarioEscape,
    articulo_id: str,
) -> str | None:
    """Resta puntos arcade y añade al inventario. Devuelve error o None."""
    art = articulo_tienda_por_id(articulo_id)
    if inventario.cantidad(articulo_id) >= MAX_STOCK_ARTICULO_ESCAPE:
        return f"Ya tienes el máximo ({MAX_STOCK_ARTICULO_ESCAPE}) de {art.nombre}."
    if estado.puntos_arcade < art.precio:
        return f"Necesitas {art.precio} pts (tienes {estado.puntos_arcade})."
    estado.puntos_arcade -= art.precio
    inventario.agregar(articulo_id)
    return None


def usar_objeto_escape(
    articulo_id: str,
    inventario: EstadoInventarioEscape,
    pregunta: Pregunta,
    *,
    estado: EstadoPartida | None = None,
    vidas_max: int | None = None,
) -> str | None:
    """Consume un objeto del inventario; devuelve mensaje de error o None."""
    err_uso = puede_usar_powerup_en_pregunta(
        articulo_id, inventario.powerups_usados_en_pregunta
    )
    if err_uso:
        return err_uso
    if not inventario.consumir(articulo_id):
        return "No tienes ese objeto."

    if articulo_id == "fifty_fifty":
        inventario.letras_ocultas_powerup = letras_ocultas_fifty_fifty(pregunta)
    elif articulo_id == "bomba":
        inventario.letras_ocultas_powerup = (
            inventario.letras_ocultas_powerup | letras_ocultas_bomba(pregunta)
        )
    elif articulo_id == "tiempo_extra":
        inventario.tiempo_extra_seg += 20
    elif articulo_id == "escudo":
        inventario.escudo_activo = True
    elif articulo_id == "amuleto_puntos":
        inventario.bonus_proximo_acierto = 20
    elif articulo_id == "vida_refuerzo":
        if estado is None or vidas_max is None:
            return "No se puede usar ahora."
        if estado.vidas_restantes is None:
            return "Este objeto no aplica en esta partida."
        if (estado.vidas_restantes or 0) >= vidas_max:
            inventario.agregar(articulo_id)
            return "Ya tienes el tope de vidas."
        estado.vidas_restantes = min(vidas_max, (estado.vidas_restantes or 0) + 1)
    elif articulo_id in {"skip", "cambio"}:
        pass
    else:
        return f"Objeto desconocido: {articulo_id}"
    inventario.powerups_usados_en_pregunta.add(articulo_id)
    return None


def linea_detalle_tienda_puerta() -> str:
    return "Compra objetos (máx. uno de cada) o continúa."


def descripcion_articulo_escape(articulo_id: str) -> str:
    return articulo_tienda_por_id(articulo_id).descripcion
