#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogo unificado de powerups y bonificaciones de partida.

Powerups: objetos almacenables (bomba, 50/50, skip…) con efecto al usarlos.
Bonificaciones: refuerzo vital y amuleto arcade; efecto instantáneo al obtenerlas.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Protocol

from Comun.emojis_partida import EMOJI_AMULETO_PUNTOS, EMOJI_OBJETO_DESCONOCIDO
from Comun.motor_nucleo import EstadoPartida

LETRAS_OPCION = ("A", "B", "C", "D")

# --- Powerups ---

POWERUPS: dict[str, tuple[str, str]] = {
    "fifty_fifty": ("50/50", "Quita 2 respuestas incorrectas"),
    "bomba": ("Bomba", "Destruyes una respuesta incorrecta"),
    "skip": ("Saltar", "Siguiente pregunta sin perder vida (corta la racha)"),
    "tiempo_extra": ("+Tiempo", "Añade 20 s a esta pregunta"),
    "escudo": ("Escudo", "El próximo fallo no cuesta vida ni corta la racha"),
    "cambio": ("Cambio", "Sustituye por una pregunta parecida (misma materia y tipo)"),
}

POWERUPS_LOOT = tuple(POWERUPS.keys())

IDS_POWERUP = frozenset(POWERUPS.keys())

MENSAJE_POWERUP_YA_USADO = "Solo puedes usar un objeto por pregunta."

POWERUPS_INCOMPATIBLES_EN_PREGUNTA: dict[str, frozenset[str]] = {
    "bomba": frozenset({"fifty_fifty"}),
    "fifty_fifty": frozenset({"bomba"}),
}

EMOJI_POWERUP: dict[str, str] = {
    "fifty_fifty": "✂️",
    "bomba": "💣",
    "skip": "⏭️",
    "tiempo_extra": "⏱️",
    "escudo": "🛡️",
    "cambio": "🔄",
}


def etiqueta_powerup(powerup_id: str) -> str:
    return POWERUPS.get(powerup_id, (powerup_id, powerup_id))[0]


def descripcion_powerup(powerup_id: str) -> str:
    return POWERUPS.get(powerup_id, (powerup_id, ""))[1]


def emoji_powerup(powerup_id: str) -> str:
    return EMOJI_POWERUP.get(powerup_id, EMOJI_OBJETO_DESCONOCIDO)

# --- Bonificaciones (mismos ids que en catálogo) ---

BONIFICACIONES: dict[str, tuple[str, str, str]] = {
    "vida_refuerzo": (
        "Refuerzo vital",
        "+1 vida al obtenerla (hasta tu tope actual).",
        "❤️",
    ),
    "amuleto_puntos": (
        "Amuleto arcade",
        "+20 pts en tu próximo acierto (al obtenerla).",
        EMOJI_AMULETO_PUNTOS,
    ),
}

IDS_BONIFICACION = frozenset(BONIFICACIONES.keys())


@dataclass(frozen=True)
class ArticuloTienda:
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
) -> ArticuloTienda:
    return ArticuloTienda(
        id=powerup_id,
        nombre=etiqueta_powerup(powerup_id),
        descripcion=descripcion or descripcion_powerup(powerup_id),
        precio=precio,
        emoji=emoji_powerup(powerup_id),
        nivel_min_sala=nivel_min_sala,
    )


def _art_bonificacion(bonificacion_id: str, precio: int, *, nivel_min_sala: int = 1) -> ArticuloTienda:
    nombre, descripcion, emoji = BONIFICACIONES[bonificacion_id]
    return ArticuloTienda(
        id=bonificacion_id,
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        emoji=emoji,
        nivel_min_sala=nivel_min_sala,
    )


CATALOGO_ARTICULOS: tuple[ArticuloTienda, ...] = (
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
    _art_bonificacion("vida_refuerzo", 55, nivel_min_sala=4),
    _art_bonificacion("amuleto_puntos", 35, nivel_min_sala=4),
)

_ARTICULO_POR_ID: dict[str, ArticuloTienda] = {a.id: a for a in CATALOGO_ARTICULOS}


class PortadorBonus(Protocol):
    bonus_proximo_acierto: int


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


def articulo_por_id(articulo_id: str) -> ArticuloTienda:
    if articulo_id not in _ARTICULO_POR_ID:
        raise KeyError(f"Artículo desconocido: {articulo_id!r}")
    return _ARTICULO_POR_ID[articulo_id]


def articulo_tienda_por_id(articulo_id: str) -> ArticuloTienda:
    return articulo_por_id(articulo_id)


def es_bonificacion(articulo_id: str) -> bool:
    return articulo_id in IDS_BONIFICACION


def es_powerup(articulo_id: str) -> bool:
    return articulo_id in IDS_POWERUP


def _incorrectas(p: Pregunta) -> list[str]:
    correcta = p.correcta if p.correcta in LETRAS_OPCION else ""
    return [letra for letra in LETRAS_OPCION if letra != correcta and p.opciones.get(letra)]


def puede_usar_powerup_en_pregunta(powerup_id: str, usados: set[str]) -> str | None:
    """Devuelve mensaje de error si el objeto no puede usarse en esta pregunta."""
    if powerup_id in usados:
        if powerup_id in POWERUPS:
            return f"Ya usaste {etiqueta_powerup(powerup_id)} en esta pregunta."
        return "Ya usaste este objeto en esta pregunta."
    incompatibles = POWERUPS_INCOMPATIBLES_EN_PREGUNTA.get(powerup_id, frozenset())
    for usado in usados:
        if usado in incompatibles:
            nom = etiqueta_powerup(powerup_id)
            otro = etiqueta_powerup(usado) if usado in POWERUPS else usado
            return f"No puedes combinar {nom} con {otro} en la misma pregunta."
    return None


def revocar_powerup_usado(usados: set[str], powerup_id: str) -> None:
    usados.discard(powerup_id)


def descripcion_articulo(articulo_id: str) -> str:
    return articulo_por_id(articulo_id).descripcion


def letras_ocultas_fifty_fifty(p: Pregunta, rng: random.Random | None = None) -> frozenset[str]:
    rng = rng or random.Random()
    malas = _incorrectas(p)
    rng.shuffle(malas)
    return frozenset(malas[:2])


def letras_ocultas_bomba(p: Pregunta, rng: random.Random | None = None) -> frozenset[str]:
    rng = rng or random.Random()
    malas = _incorrectas(p)
    if not malas:
        return frozenset()
    return frozenset({rng.choice(malas)})


def letras_ocultas_por_cantidad(
    p: Pregunta,
    cantidad: int,
    *,
    semilla: int,
) -> frozenset[str]:
    if cantidad <= 0:
        return frozenset()
    rng = random.Random(semilla * 31 + len(p.texto))
    malas = _incorrectas(p)
    rng.shuffle(malas)
    return frozenset(malas[: min(cantidad, len(malas))])


def bonificacion_aplicable(
    articulo_id: str,
    estado: EstadoPartida,
    *,
    vidas_max: int | None = None,
) -> bool:
    """True si la bonificación tendría efecto al obtenerla ahora."""
    if not es_bonificacion(articulo_id):
        return True
    if articulo_id == "vida_refuerzo":
        if estado.vidas_restantes is None or vidas_max is None:
            return False
        return (estado.vidas_restantes or 0) < vidas_max
    if articulo_id == "amuleto_puntos":
        return True
    return False


def aplicar_bonificacion(
    articulo_id: str,
    estado: EstadoPartida,
    portador: PortadorBonus,
    *,
    vidas_max: int | None = None,
) -> str | None:
    """Aplica una bonificación al instante. Devuelve mensaje de error o None."""
    if not es_bonificacion(articulo_id):
        return f"No es una bonificación: {articulo_id!r}"
    if not bonificacion_aplicable(articulo_id, estado, vidas_max=vidas_max):
        return "Esta bonificación no aplica ahora."
    if articulo_id == "vida_refuerzo":
        if estado.vidas_restantes is None or vidas_max is None:
            return "Esta bonificación no aplica en esta partida."
        estado.vidas_restantes = min(vidas_max, (estado.vidas_restantes or 0) + 1)
    elif articulo_id == "amuleto_puntos":
        portador.bonus_proximo_acierto = 20
    return None


def aplicar_loot(
    articulo_id: str,
    cantidad: int,
    estado: EstadoPartida,
    inventario: EstadoInventarioEscape,
    *,
    vidas_max: int | None = None,
) -> None:
    """Botín/recompensa: powerups al inventario; bonificaciones al instante."""
    if cantidad <= 0:
        return
    if es_bonificacion(articulo_id):
        for _ in range(cantidad):
            if bonificacion_aplicable(articulo_id, estado, vidas_max=vidas_max):
                aplicar_bonificacion(articulo_id, estado, inventario, vidas_max=vidas_max)
        return
    inventario.agregar(articulo_id, cantidad)


def usar_objeto(
    articulo_id: str,
    inventario: EstadoInventarioEscape,
    pregunta: Pregunta,
) -> str | None:
    """Consume un powerup del inventario; devuelve mensaje de error o None."""
    if es_bonificacion(articulo_id):
        return "Las bonificaciones se aplican al obtenerlas."
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
    elif articulo_id in {"skip", "cambio"}:
        pass
    else:
        return f"Objeto desconocido: {articulo_id}"
    inventario.powerups_usados_en_pregunta.add(articulo_id)
    return None
