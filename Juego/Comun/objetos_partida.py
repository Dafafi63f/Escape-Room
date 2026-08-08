#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogo unificado de powerups y bonificaciones de partida.

Powerups: objetos almacenables (bomba, 50/50, skip…) con efecto al usarlos.
Bonificaciones: refuerzo vital y amuleto arcade; efecto instantáneo al obtenerlas.
"""

from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from Comun.emojis_partida import EMOJI_AMULETO_PUNTOS, EMOJI_OBJETO_DESCONOCIDO, EMOJI_PURGA_MALDICION
from Comun.motor_nucleo import EstadoPartida

if TYPE_CHECKING:
    from Comun.modelos import Pregunta

LETRAS_OPCION = ("A", "B", "C", "D")

# --- Powerups ---
#
# Duración de efectos (resumen):
# - Una pregunta (se limpia al pasar de pregunta): 50/50, bomba, comodín, descarte,
#   +tiempo, tiempo lento, 2.ª oportunidad, doble o nada.
# - Inventario de sala (pantalla de puertas): reroll, limpieza, salto de sala.
# - Hasta consumirse en la pregunta actual: escudo (el próximo fallo).
# - Toda la puerta escape / bloque resistencia: niebla y cronómetros de puerta,
#   maldiciones y bloques temáticos en resistencia.
# - Resistencia: sello de purga elimina maldición activa.
# - Hasta usarlo: racha congelada (cuenta de skips), saltar/cambio.

POWERUPS_PREGUNTA: dict[str, tuple[str, str]] = {
    "fifty_fifty": ("50/50", "Quita 2 respuestas incorrectas"),
    "bomba": ("Bomba", "Destruyes una respuesta incorrecta"),
    "comodin": ("Comodín", "Quita 1 incorrecta al azar"),
    "descarte_inteligente": (
        "Descarte",
        "Quita 2 incorrectas del mismo perfil que la correcta",
    ),
    "skip": ("Saltar", "Siguiente pregunta sin perder vida (corta la racha)"),
    "tiempo_extra": ("+Tiempo", "Añade 20 s a esta pregunta"),
    "tiempo_lento": ("Tiempo lento", "El cronómetro va al 50 % en esta pregunta"),
    "escudo": ("Escudo", "El próximo fallo no cuesta vida ni corta la racha"),
    "segunda_oportunidad": (
        "2.ª oportunidad",
        "Si fallas, puedes responder otra vez sin perder vida",
    ),
    "doble_o_nada": ("Doble o nada", "×2 puntos si aciertas; si fallas, −1 vida extra"),
    "racha_congelada": (
        "Racha congelada",
        "El próximo Saltar no corta la racha",
    ),
    "cambio": ("Cambio", "Sustituye por una pregunta parecida (misma materia y tipo)"),
}

# Solo escape: inventario de sala/puerta (ids distintos a los de pregunta).
POWERUPS_SALA_ESCAPE: dict[str, tuple[str, str]] = {
    "reroll_puertas": (
        "Cambio de rumbo",
        "Sustituye todas las puertas de esta sala por otras nuevas.",
    ),
    "limpieza_maldiciones": (
        "Limpieza arcana",
        "Quita el rasgo maldito de todas las puertas de la sala.",
    ),
    "salto_sala": (
        "Atajo de sala",
        "Avanzas a la siguiente sala sin completar ninguna puerta.",
    ),
}

# Solo resistencia (no aparece en escape: allí se usa limpieza_maldiciones).
POWERUPS_RESISTENCIA_EXTRA: dict[str, tuple[str, str]] = {
    "sello_purga": (
        "Sello de purga",
        "Elimina la maldición activa.",
    ),
}

POWERUPS = {**POWERUPS_PREGUNTA, **POWERUPS_SALA_ESCAPE, **POWERUPS_RESISTENCIA_EXTRA}

POWERUPS_SOLO_SALA_ESCAPE = frozenset({
    "reroll_puertas",
    "limpieza_maldiciones",
    "salto_sala",
})

POWERUPS_SOLO_RESISTENCIA = frozenset(POWERUPS_RESISTENCIA_EXTRA.keys())

POWERUPS_LOOT = tuple(POWERUPS_PREGUNTA.keys()) + tuple(POWERUPS_RESISTENCIA_EXTRA.keys())
POWERUPS_LOOT_ESCAPE = tuple(POWERUPS_PREGUNTA.keys()) + tuple(POWERUPS_SOLO_SALA_ESCAPE)

# Botín de apuestas resistencia: sin objetos de cronómetro (solo en pregunta activa)
# ni doble o nada (ya es una apuesta del catálogo).
_POWERUPS_EXCLUIDOS_LOOT_APUESTA = frozenset({
    "tiempo_lento",
    "tiempo_extra",
    "doble_o_nada",
})
POWERUPS_LOOT_APUESTA = tuple(
    pid for pid in POWERUPS_LOOT if pid not in _POWERUPS_EXCLUIDOS_LOOT_APUESTA
)

IDS_POWERUP = frozenset(POWERUPS.keys())

# Saltar y Cambio: no ocupan el slot (resistencia y escape); en escape no se
# pueden usar si ya hay otro objeto activo en la misma pregunta.
POWERUPS_MULTI_USO_PREGUNTA = frozenset({"skip", "cambio"})

_AYUDAS_OPCIONES = frozenset(
    {"bomba", "fifty_fifty", "comodin", "descarte_inteligente"}
)

MENSAJE_POWERUP_YA_USADO = (
    "Solo puedes usar un objeto (salvo Saltar/Cambio) por pregunta."
)
MENSAJE_POWERUP_YA_USADO_ESCAPE = (
    "Solo puedes usar un objeto por pregunta (Saltar/Cambio pasan a otra)."
)

POWERUPS_INCOMPATIBLES_EN_PREGUNTA: dict[str, frozenset[str]] = {
    pid: _AYUDAS_OPCIONES - {pid} for pid in _AYUDAS_OPCIONES
}

EMOJI_POWERUP: dict[str, str] = {
    "fifty_fifty": "✂️",
    "bomba": "💣",
    "comodin": "🃏",
    "descarte_inteligente": "🧠",
    "skip": "⏭️",
    "tiempo_extra": "⏱️",
    "tiempo_lento": "🐢",
    "escudo": "🛡️",
    "reroll_puertas": "🌀",
    "limpieza_maldiciones": "✨",
    "salto_sala": "⏩",
    "sello_purga": EMOJI_PURGA_MALDICION,
    "segunda_oportunidad": "🔁",
    "doble_o_nada": "🎲",
    "racha_congelada": "❄️",
    "cambio": "🔄",
}

# Alternativas guardadas (no activas; cambiar EMOJI_POWERUP arriba si se adoptan).
ALTERNATIVAS_EMOJI_DESCARTE_INTELIGENTE: tuple[str, ...] = (
    "🎯",
    "🗑️",
    "🔍",
    "✂️",
)

_NUM_OPCION_RE = re.compile(r"\d")


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
        "Pts extra en tu próximo acierto (escala con la partida).",
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
    contenido_pack: tuple[tuple[str, int], ...] = ()
    n_pack_random: int = 0


@dataclass(frozen=True)
class OfertaTienda:
    """Artículo en tienda/oferta con precio variado para una visita."""

    articulo: ArticuloTienda
    precio_efectivo: int
    etiqueta_precio: str | None = None


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
    _art_powerup("comodin", 16),
    _art_powerup(
        "fifty_fifty",
        25,
        descripcion="Quita 2 incorrectas al azar (sustituye otras ayudas de opciones).",
    ),
    _art_powerup("descarte_inteligente", 28),
    _art_powerup("tiempo_extra", 22),
    _art_powerup("tiempo_lento", 24),
    _art_powerup("doble_o_nada", 35),
    _art_powerup("racha_congelada", 40, nivel_min_sala=4),
    _art_powerup("segunda_oportunidad", 42, nivel_min_sala=4),
    _art_powerup("cambio", 32),
    _art_powerup("skip", 38),
    _art_powerup("escudo", 48, nivel_min_sala=6),
    _art_powerup("reroll_puertas", 44, nivel_min_sala=4),
    _art_powerup("limpieza_maldiciones", 48, nivel_min_sala=8),
    _art_powerup("salto_sala", 55, nivel_min_sala=10),
    ArticuloTienda(
        id="pack_ayudas",
        nombre="Pack ayudas",
        descripcion="Bomba + Comodín.",
        precio=26,
        emoji="🎁",
        contenido_pack=(("bomba", 1), ("comodin", 1)),
    ),
    ArticuloTienda(
        id="pack_random_3",
        nombre="Pack sorpresa",
        descripcion="3 objetos al azar (pueden repetirse).",
        precio=48,
        emoji="🎲",
        nivel_min_sala=3,
        n_pack_random=3,
    ),
    ArticuloTienda(
        id="pack_supervivencia",
        nombre="Pack supervivencia",
        descripcion="Escudo + Tiempo extra.",
        precio=58,
        emoji="🎒",
        nivel_min_sala=6,
        contenido_pack=(("escudo", 1), ("tiempo_extra", 1)),
    ),
    _art_bonificacion("vida_refuerzo", 55, nivel_min_sala=4),
    _art_bonificacion("amuleto_puntos", 35, nivel_min_sala=4),
)

_IDS_PACK = frozenset(
    a.id for a in CATALOGO_ARTICULOS if a.contenido_pack or a.n_pack_random > 0
)

_ARTICULO_POR_ID: dict[str, ArticuloTienda] = {a.id: a for a in CATALOGO_ARTICULOS}


class PortadorBonus(Protocol):
    bonus_proximo_acierto: int


@dataclass
class EstadoInventarioEscape:
    inventario_pregunta: dict[str, int] = field(default_factory=dict)
    inventario_puerta: dict[str, int] = field(default_factory=dict)
    escudo_activo: bool = False
    proteccion_maldicion_puerta: bool = False
    tiempo_extra_seg: int = 0
    factor_velocidad_tiempo: float = 1.0
    segunda_oportunidad_activa: bool = False
    doble_o_nada_activo: bool = False
    skip_sin_cortar_racha: int = 0
    letras_ocultas_powerup: frozenset[str] = field(default_factory=frozenset)
    bonus_proximo_acierto: int = 0
    powerups_usados_en_pregunta: set[str] = field(default_factory=set)
    powerups_activados_en_puerta: set[str] = field(default_factory=set)

    def _bolsa_articulo(self, articulo_id: str) -> dict[str, int]:
        from Comun.powerups_puerta_escape import es_powerup_inventario_puerta_escape

        if es_powerup_inventario_puerta_escape(articulo_id):
            return self.inventario_puerta
        return self.inventario_pregunta

    def cantidad_pregunta(self, articulo_id: str) -> int:
        return max(0, self.inventario_pregunta.get(articulo_id, 0))

    def cantidad_puerta(self, articulo_id: str) -> int:
        return max(0, self.inventario_puerta.get(articulo_id, 0))

    def cantidad(self, articulo_id: str) -> int:
        return max(0, self._bolsa_articulo(articulo_id).get(articulo_id, 0))

    def items_pregunta(self) -> list[tuple[str, int]]:
        return [
            (aid, n)
            for aid, n in sorted(self.inventario_pregunta.items())
            if n > 0
        ]

    def items_puerta(self) -> list[tuple[str, int]]:
        return [
            (aid, n)
            for aid, n in sorted(self.inventario_puerta.items())
            if n > 0
        ]

    def tiene_items_puerta(self) -> bool:
        return any(n > 0 for n in self.inventario_puerta.values())

    def tiene_items_preparacion_puerta(self) -> bool:
        from Comun.powerups_puerta_escape import es_powerup_preparacion_puerta_escape

        return any(
            n > 0 and es_powerup_preparacion_puerta_escape(aid)
            for aid, n in self.inventario_puerta.items()
        )

    def inventario_total(self) -> dict[str, int]:
        total: dict[str, int] = dict(self.inventario_pregunta)
        for aid, n in self.inventario_puerta.items():
            if n > 0:
                total[aid] = total.get(aid, 0) + n
        return total

    @property
    def inventario(self) -> dict[str, int]:
        """Vista unificada (tests y pesos de loot)."""
        return self.inventario_total()

    def agregar(self, articulo_id: str, cantidad: int = 1) -> None:
        if cantidad <= 0:
            return
        bolsa = self._bolsa_articulo(articulo_id)
        bolsa[articulo_id] = max(0, bolsa.get(articulo_id, 0)) + cantidad

    def consumir(self, articulo_id: str) -> bool:
        bolsa = self._bolsa_articulo(articulo_id)
        n = max(0, bolsa.get(articulo_id, 0))
        if n <= 0:
            return False
        if n == 1:
            bolsa.pop(articulo_id, None)
        else:
            bolsa[articulo_id] = n - 1
        return True

    def reset_pregunta(self) -> None:
        self.letras_ocultas_powerup = frozenset()
        self.tiempo_extra_seg = 0
        self.factor_velocidad_tiempo = 1.0
        self.segunda_oportunidad_activa = False
        self.doble_o_nada_activo = False
        self.powerups_usados_en_pregunta.clear()

    def reiniciar_slot_pregunta(self) -> None:
        """Nueva pregunta en el mismo bloque (cambio): limpia ayudas de la anterior."""
        self.letras_ocultas_powerup = frozenset()
        self.tiempo_extra_seg = 0
        self.factor_velocidad_tiempo = 1.0
        self.segunda_oportunidad_activa = False
        self.doble_o_nada_activo = False
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


def es_pack(articulo_id: str) -> bool:
    return articulo_id in _IDS_PACK


def powerups_usados_slot(usados: set[str]) -> set[str]:
    return usados - POWERUPS_MULTI_USO_PREGUNTA


def slot_powerup_ocupado(usados: set[str]) -> bool:
    return bool(powerups_usados_slot(usados))


def segundos_efectivos_transcurridos(inicio: float, factor_velocidad: float) -> float:
    """factor < 1 hace que el reloj cuente más despacio (más margen real)."""
    return (time.monotonic() - inicio) * max(0.1, factor_velocidad)


def segundos_pregunta_restantes(
    inicio: float,
    limite: int | None,
    *,
    factor_velocidad: float = 1.0,
    pausa_seg: float = 0.0,
) -> int | None:
    if not limite:
        return None
    transcurrido = segundos_efectivos_transcurridos(inicio, factor_velocidad) - max(0.0, pausa_seg)
    return max(0, int(limite - transcurrido))


def tiempo_pregunta_agotado(
    inicio: float,
    limite: int | None,
    *,
    factor_velocidad: float = 1.0,
    pausa_seg: float = 0.0,
) -> bool:
    if not limite:
        return False
    transcurrido = segundos_efectivos_transcurridos(inicio, factor_velocidad) - max(0.0, pausa_seg)
    return transcurrido >= limite


def _incorrectas(p: Pregunta) -> list[str]:
    correcta = p.correcta if p.correcta in LETRAS_OPCION else ""
    return [letra for letra in LETRAS_OPCION if letra != correcta and p.opciones.get(letra)]


def puede_usar_powerup_en_pregunta(powerup_id: str, usados: set[str]) -> str | None:
    """Devuelve mensaje de error si el objeto no puede usarse en esta pregunta."""
    if powerup_id in POWERUPS_MULTI_USO_PREGUNTA:
        return None
    if slot_powerup_ocupado(usados):
        return MENSAJE_POWERUP_YA_USADO
    if powerup_id in usados:
        if powerup_id in POWERUPS:
            return f"Ya usaste {etiqueta_powerup(powerup_id)} en esta pregunta."
        return "Ya usaste este objeto en esta pregunta."
    incompatibles = POWERUPS_INCOMPATIBLES_EN_PREGUNTA.get(powerup_id, frozenset())
    for usado in powerups_usados_slot(usados):
        if usado in incompatibles:
            nom = etiqueta_powerup(powerup_id)
            otro = etiqueta_powerup(usado) if usado in POWERUPS else usado
            return f"No puedes combinar {nom} con {otro} en la misma pregunta."
    return None


def revocar_powerup_usado(usados: set[str], powerup_id: str) -> None:
    usados.discard(powerup_id)


def elegir_powerup_loot(
    inventario: dict[str, int],
    rng: random.Random,
    *,
    pool: tuple[str, ...] | None = None,
) -> str:
    """Powerup al azar con menos peso si ya hay muchos del mismo tipo en inventario."""
    candidatos = pool or POWERUPS_LOOT
    total = inventario if isinstance(inventario, dict) else inventario.inventario_total()
    pesos = [1.0 / (1.0 + 0.65 * max(0, total.get(pid, 0))) for pid in candidatos]
    return rng.choices(candidatos, weights=pesos, k=1)[0]


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


def letras_ocultas_comodin(p: Pregunta, rng: random.Random | None = None) -> frozenset[str]:
    return letras_ocultas_bomba(p, rng)


def _perfil_opcion(texto: str) -> str:
    t = texto.strip()
    if _NUM_OPCION_RE.search(t) or any(c in t for c in "+-*/=^"):
        return "numerica"
    if len(t) <= 24:
        return "breve"
    return "extensa"


def letras_ocultas_descarte_inteligente(
    p: Pregunta,
    rng: random.Random | None = None,
) -> frozenset[str]:
    rng = rng or random.Random()
    correcta = p.correcta if p.correcta in LETRAS_OPCION else ""
    perfil_ok = _perfil_opcion(p.opciones.get(correcta, ""))
    malas = [
        letra
        for letra in _incorrectas(p)
        if _perfil_opcion(p.opciones.get(letra, "")) == perfil_ok
    ]
    if len(malas) < 2:
        malas = _incorrectas(p)
    rng.shuffle(malas)
    return frozenset(malas[:2])


def resolver_contenido_pack(
    articulo_id: str,
    rng: random.Random,
    inventario: dict[str, int] | object | None = None,
    *,
    loot_pool: tuple[str, ...] | None = None,
) -> list[tuple[str, int]]:
    art = articulo_por_id(articulo_id)
    if art.n_pack_random > 0:
        if inventario is None:
            inv: dict[str, int] = {}
        elif isinstance(inventario, dict):
            inv = inventario
        else:
            inv = getattr(inventario, "inventario", {})
            if not isinstance(inv, dict):
                inv = {}
        return [
            (elegir_powerup_loot(inv, rng, pool=loot_pool), 1)
            for _ in range(art.n_pack_random)
        ]
    if art.contenido_pack:
        return list(art.contenido_pack)
    if es_powerup(articulo_id):
        return [(articulo_id, 1)]
    return []


def letras_ocultas_por_cantidad(
    p: Pregunta,
    cantidad: int,
    *,
    rng: random.Random,
) -> frozenset[str]:
    if cantidad <= 0:
        return frozenset()
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
    numero_pregunta: int | None = None,
    numero_sala: int | None = None,
    precio_pagado: int | None = None,
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
        from Comun.economia_partida import (
            bonus_amuleto_arcade,
            bonus_amuleto_tras_compra,
        )

        if precio_pagado is not None and precio_pagado > 0:
            portador.bonus_proximo_acierto = bonus_amuleto_tras_compra(
                precio_pagado,
                numero_pregunta=numero_pregunta,
                numero_sala=numero_sala,
            )
        else:
            portador.bonus_proximo_acierto = bonus_amuleto_arcade(
                numero_pregunta=numero_pregunta,
                numero_sala=numero_sala,
            )
    return None


def aplicar_loot(
    articulo_id: str,
    cantidad: int,
    estado: EstadoPartida,
    inventario: EstadoInventarioEscape,
    *,
    vidas_max: int | None = None,
    numero_pregunta: int | None = None,
    numero_sala: int | None = None,
) -> None:
    """Botín/recompensa: powerups al inventario; bonificaciones al instante."""
    if cantidad <= 0:
        return
    if es_bonificacion(articulo_id):
        for _ in range(cantidad):
            if bonificacion_aplicable(articulo_id, estado, vidas_max=vidas_max):
                aplicar_bonificacion(
                    articulo_id,
                    estado,
                    inventario,
                    vidas_max=vidas_max,
                    numero_pregunta=numero_pregunta,
                    numero_sala=numero_sala,
                )
        return
    inventario.agregar(articulo_id, cantidad)


def usar_objeto(
    articulo_id: str,
    inventario: EstadoInventarioEscape,
    pregunta: Pregunta,
    *,
    escape: bool = False,
) -> str | None:
    """Consume un powerup del inventario; devuelve mensaje de error o None."""
    if es_bonificacion(articulo_id):
        return "Las bonificaciones se aplican al obtenerlas."
    err_uso = _error_uso_powerup(articulo_id, inventario, escape=escape)
    if err_uso:
        return err_uso
    if not inventario.consumir(articulo_id):
        return "No tienes ese objeto."

    err_aplicar = _aplicar_efecto_powerup(articulo_id, inventario, pregunta)
    if err_aplicar:
        return err_aplicar
    _registrar_uso_powerup(articulo_id, inventario, escape=escape)
    return None


def _error_uso_powerup(
    articulo_id: str,
    inventario: EstadoInventarioEscape,
    *,
    escape: bool,
) -> str | None:
    if escape:
        from Comun.powerups_puerta_escape import puede_usar_powerup_en_pregunta_escape

        return puede_usar_powerup_en_pregunta_escape(
            articulo_id, inventario.powerups_usados_en_pregunta
        )
    return puede_usar_powerup_en_pregunta(
        articulo_id, inventario.powerups_usados_en_pregunta
    )


def _aplicar_efecto_powerup(
    articulo_id: str,
    inventario: EstadoInventarioEscape,
    pregunta: Pregunta,
) -> str | None:
    if articulo_id == "fifty_fifty":
        inventario.letras_ocultas_powerup = letras_ocultas_fifty_fifty(pregunta)
    elif articulo_id == "bomba":
        inventario.letras_ocultas_powerup = (
            inventario.letras_ocultas_powerup | letras_ocultas_bomba(pregunta)
        )
    elif articulo_id == "comodin":
        inventario.letras_ocultas_powerup = (
            inventario.letras_ocultas_powerup | letras_ocultas_comodin(pregunta)
        )
    elif articulo_id == "descarte_inteligente":
        inventario.letras_ocultas_powerup = letras_ocultas_descarte_inteligente(pregunta)
    elif articulo_id == "tiempo_extra":
        inventario.tiempo_extra_seg += 20
    elif articulo_id == "tiempo_lento":
        inventario.factor_velocidad_tiempo = 0.5
    elif articulo_id == "escudo":
        inventario.escudo_activo = True
    elif articulo_id == "sello_purga":
        inventario.proteccion_maldicion_puerta = True
    elif articulo_id == "segunda_oportunidad":
        inventario.segunda_oportunidad_activa = True
    elif articulo_id == "doble_o_nada":
        inventario.doble_o_nada_activo = True
    elif articulo_id == "racha_congelada":
        inventario.skip_sin_cortar_racha += 1
    elif articulo_id not in {"skip", "cambio"}:
        return f"Objeto desconocido: {articulo_id}"
    return None


def _registrar_uso_powerup(
    articulo_id: str,
    inventario: EstadoInventarioEscape,
    *,
    escape: bool,
) -> None:
    if escape:
        from Comun.powerups_puerta_escape import registrar_uso_powerup_escape

        registrar_uso_powerup_escape(inventario, articulo_id)
    elif articulo_id not in POWERUPS_MULTI_USO_PREGUNTA:
        inventario.powerups_usados_en_pregunta.add(articulo_id)
