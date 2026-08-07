#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modelo unificado de maldiciones (escape y resistencia).

**Resistencia** — una sola ``MaldicionActiva`` a la vez:

| Tipo | ``modo_fin`` | Efecto / reto | Si fallas pregunta | Si fallas el reto |
|------|--------------|---------------|--------------------|-------------------|
| Sin objetos, puntos mitad… | ``duracion`` | Empeora el turno | −1 vida | — |
| Mortal (``fatal``) | ``mortal`` | — | **Fin de partida** | — |
| Desafío tiempo | ``desafio`` | X aciertos en Y s | −1 vida | **Fin de partida** |

Relámpago y niebla en opciones son **solo eventos de escalada** (``relampago``, ``opciones_ocultas``),
no maldiciones. Las de duración expiran tras N preguntas o con ``sello_purga`` / Purga arcana.

**Escape** — una sola maldición por puerta (rasgo ``puerta_maldita``; no ``MaldicionActiva``):

| Tipo | Rasgo | Efecto | Si fallas pregunta |
|------|-------|--------|--------------------|
| Mortal | ``puerta_maldita`` | — | **Fin de partida** |

Los cronómetros (``cronometro_pregunta``, ``cronometro_bloque``, ``cronometro_doble``) son
desafíos de tiempo normales, no maldiciones. Pueden combinarse con ``puerta_maldita``
en la misma puerta. Niebla y relámpago son desafíos normales. Limpieza:
``limpieza_maldiciones`` (solo quita ``puerta_maldita``).

| Resistencia | Escape |
|-------------|--------|
| ``fatal`` | ``puerta_maldita`` |
| ``desafio_tiempo`` | — (solo resistencia) |
| Limpieza con ítem | ``limpieza_maldiciones`` |

En escape, agotar un cronómetro de puerta cuenta como fallo (−vida y abandonas); solo
``puerta_maldita`` convierte ese fallo en fin de partida.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from Comun.escape_room import PuertaEscape
    from Comun.pity_variedad_resistencia import PityVariedadResistencia
    from Comun.resistencia_motor import MaldicionActiva

PREGUNTA_MIN_MALDICION_DESAFIO_TIEMPO_RESISTENCIA = 120
# Ninguna maldición por racha de fallos antes de esta pregunta (alineado con eventos/jefe).
PREGUNTA_MIN_MALDICION_RESISTENCIA = 15
# Tras tantas preguntas sin maldición, la siguiente oportunidad válida la fuerza.
PREGUNTA_HARD_PITY_MALDICION_RESISTENCIA = 48

_PITY_INC_GATE_MALDICION = 0.014
_PROB_GATE_MAX_BOOST_MALDICION = 0.36
_PITY_INC_MALDICION_ID = 0.26
_PESO_BASE_MALDICION_ID = 1.0


class ModoFinMaldicion(str, Enum):
    """Cómo termina la maldición sin ítem de purga."""

    DURACION = "duracion"
    DESAFIO = "desafio"
    MORTAL = "mortal"


@dataclass
class DesafioMaldicionTiempo:
    """X aciertos en Y segundos; fin de partida si expira (maldición desafío)."""

    aciertos_objetivo: int
    tiempo_limite_seg: int
    aciertos_logrados: int = 0
    inicio_monotonic: float = field(default_factory=time.monotonic)
    segundos_pausados: float = 0.0
    _pausa_desde: float | None = field(default=None, repr=False)

    def pausar(self) -> None:
        if self._pausa_desde is None:
            self._pausa_desde = time.monotonic()

    def reanudar(self) -> None:
        if self._pausa_desde is not None:
            self.segundos_pausados += time.monotonic() - self._pausa_desde
            self._pausa_desde = None

    def _segundos_pausados_efectivos(self) -> float:
        pausa = self.segundos_pausados
        if self._pausa_desde is not None:
            pausa += time.monotonic() - self._pausa_desde
        return pausa

    def tiempo_restante_seg(self) -> int:
        transcurrido = (
            time.monotonic() - self.inicio_monotonic - self._segundos_pausados_efectivos()
        )
        rest = int(self.tiempo_limite_seg - transcurrido)
        return max(0, rest)

    def completado(self) -> bool:
        return self.aciertos_logrados >= self.aciertos_objetivo

    def expirado(self) -> bool:
        return not self.completado() and self.tiempo_restante_seg() <= 0


# Alias histórico (tests y imports antiguos).
DesafioBloqueTiempoResistencia = DesafioMaldicionTiempo


@dataclass(frozen=True)
class EfectoMaldicion:
    multiplicador_puntos: float = 1.0
    fin_partida_si_fallo: bool = False
    bloquea_objetos: bool = False


@dataclass(frozen=True)
class PlantillaMaldicionResistencia:
    id: str
    etiqueta: str
    emoji: str
    efecto: EfectoMaldicion
    duracion_min: int = 1
    duracion_max: int = 2
    modo_fin: ModoFinMaldicion = ModoFinMaldicion.DURACION
    pregunta_min: int = 1


_PLANTILLA_DESAFIO_TIEMPO = PlantillaMaldicionResistencia(
    id="desafio_tiempo",
    etiqueta="Maldición: desafío de tiempo",
    emoji="⏲️",
    efecto=EfectoMaldicion(),
    modo_fin=ModoFinMaldicion.DESAFIO,
    pregunta_min=PREGUNTA_MIN_MALDICION_DESAFIO_TIEMPO_RESISTENCIA,
)

_MALDICIONES_RESISTENCIA: tuple[PlantillaMaldicionResistencia, ...] = (
    PlantillaMaldicionResistencia(
        id="sin_objetos",
        etiqueta="Maldición: no puedes usar objetos",
        emoji="⛔",
        efecto=EfectoMaldicion(bloquea_objetos=True),
        duracion_min=1,
        duracion_max=2,
        pregunta_min=PREGUNTA_MIN_MALDICION_RESISTENCIA,
    ),
    PlantillaMaldicionResistencia(
        id="puntos_mitad",
        etiqueta="Maldición: puntos al 50 %",
        emoji="📉",
        efecto=EfectoMaldicion(multiplicador_puntos=0.5),
        duracion_min=2,
        duracion_max=3,
        pregunta_min=20,
    ),
    PlantillaMaldicionResistencia(
        id="fatal",
        etiqueta="Maldición mortal: un fallo acaba la partida",
        emoji="💀",
        efecto=EfectoMaldicion(fin_partida_si_fallo=True),
        duracion_min=1,
        duracion_max=2,
        modo_fin=ModoFinMaldicion.MORTAL,
        pregunta_min=35,
    ),
    _PLANTILLA_DESAFIO_TIEMPO,
)


class _MaldicionConDuracion(Protocol):
    id: str
    etiqueta: str
    modo_fin: ModoFinMaldicion
    preguntas_restantes: int
    multiplicador_puntos: float
    fin_partida_si_fallo: bool
    desafio: DesafioMaldicionTiempo | None


_IDS_PITY_MALDICION_RESISTENCIA: tuple[str, ...] = tuple(p.id for p in _MALDICIONES_RESISTENCIA)


@dataclass
class PityMaldicionesResistencia:
    """Preguntas sin maldición; sube prob. global y peso de tipos no vistos."""

    preguntas_sin_maldicion: int = 0
    preguntas_sin_por_id: dict[str, int] = field(default_factory=dict)
    ultima_pregunta_actualizada: int = 0


def debe_forzar_maldicion_resistencia(
    pity: PityMaldicionesResistencia,
    numero_pregunta: int,
    *,
    pity_variedad: PityVariedadResistencia | None = None,
) -> bool:
    if numero_pregunta < PREGUNTA_MIN_MALDICION_RESISTENCIA:
        return False
    from Comun.pity_variedad_resistencia import (
        PREGUNTA_SOFT_PITY_MALDICION_RESISTENCIA,
        preguntas_hard_pity_maldicion_resistencia,
    )

    umbral = preguntas_hard_pity_maldicion_resistencia(pity_variedad)
    if pity.preguntas_sin_maldicion >= umbral:
        return True
    return (
        numero_pregunta >= PREGUNTA_SOFT_PITY_MALDICION_RESISTENCIA
        and pity.preguntas_sin_maldicion >= PREGUNTA_SOFT_PITY_MALDICION_RESISTENCIA
    )


def probabilidad_activar_maldicion_fallo_resistencia(
    numero_pregunta: int,
    pity: PityMaldicionesResistencia,
    *,
    prob_base: float,
    pity_variedad: PityVariedadResistencia | None = None,
) -> float:
    if numero_pregunta < PREGUNTA_MIN_MALDICION_RESISTENCIA:
        return 0.0
    if debe_forzar_maldicion_resistencia(
        pity, numero_pregunta, pity_variedad=pity_variedad
    ):
        return 1.0
    from Comun.resistencia_partida import prob_gate_evento_resistencia_con_pity

    return prob_gate_evento_resistencia_con_pity(
        prob_base=prob_base,
        preguntas_sin_ver=pity.preguntas_sin_maldicion,
        incremento_por_pregunta=_PITY_INC_GATE_MALDICION,
        max_boost=_PROB_GATE_MAX_BOOST_MALDICION,
    )


def probabilidad_activar_maldicion_desafio_resistencia(
    numero_pregunta: int,
    pity: PityMaldicionesResistencia,
    *,
    prob_base: float,
    pity_variedad: PityVariedadResistencia | None = None,
) -> float:
    if numero_pregunta < PREGUNTA_MIN_MALDICION_DESAFIO_TIEMPO_RESISTENCIA:
        return 0.0
    if prob_base <= 0.0:
        return 0.0
    if debe_forzar_maldicion_resistencia(
        pity, numero_pregunta, pity_variedad=pity_variedad
    ):
        return 1.0
    from Comun.resistencia_partida import prob_gate_evento_resistencia_con_pity

    prob = prob_gate_evento_resistencia_con_pity(
        prob_base=prob_base,
        preguntas_sin_ver=pity.preguntas_sin_maldicion,
        incremento_por_pregunta=_PITY_INC_GATE_MALDICION,
        max_boost=_PROB_GATE_MAX_BOOST_MALDICION,
    )
    return min(0.98, prob)


def actualizar_pity_maldiciones_resistencia(
    pity: PityMaldicionesResistencia,
    *,
    numero_pregunta: int,
    maldicion_id_activada: str | None = None,
    maldicion_vigente: bool = False,
) -> None:
    """Tras una pregunta: resetea si hubo maldición nueva o sigue activa."""
    if numero_pregunta <= pity.ultima_pregunta_actualizada:
        return
    pity.ultima_pregunta_actualizada = numero_pregunta
    if maldicion_id_activada:
        pity.preguntas_sin_maldicion = 0
        for mid in _IDS_PITY_MALDICION_RESISTENCIA:
            if mid == maldicion_id_activada:
                pity.preguntas_sin_por_id[mid] = 0
            else:
                pity.preguntas_sin_por_id[mid] = pity.preguntas_sin_por_id.get(mid, 0) + 1
    elif maldicion_vigente:
        return
    else:
        pity.preguntas_sin_maldicion += 1
        for mid in _IDS_PITY_MALDICION_RESISTENCIA:
            pity.preguntas_sin_por_id[mid] = pity.preguntas_sin_por_id.get(mid, 0) + 1


def elegir_plantilla_maldicion_resistencia(
    candidatas: list[PlantillaMaldicionResistencia],
    pity: PityMaldicionesResistencia,
    rng: random.Random,
) -> PlantillaMaldicionResistencia:
    if len(candidatas) == 1:
        return candidatas[0]
    pesos = [
        _PESO_BASE_MALDICION_ID
        + pity.preguntas_sin_por_id.get(p.id, 0) * _PITY_INC_MALDICION_ID
        for p in candidatas
    ]
    return rng.choices(candidatas, weights=pesos, k=1)[0]


def plantillas_maldicion_resistencia(
    numero_pregunta: int,
    *,
    incluir_desafio_tiempo: bool = False,
) -> list[PlantillaMaldicionResistencia]:
    candidatas = [
        p
        for p in _MALDICIONES_RESISTENCIA
        if numero_pregunta >= p.pregunta_min
        and (incluir_desafio_tiempo or p.modo_fin != ModoFinMaldicion.DESAFIO)
    ]
    return candidatas


def instanciar_maldicion_resistencia(
    plantilla: PlantillaMaldicionResistencia,
    rng: random.Random,
) -> MaldicionActiva:
    from Comun.resistencia_motor import MaldicionActiva

    duracion = rng.randint(plantilla.duracion_min, plantilla.duracion_max)
    return MaldicionActiva(
        id=plantilla.id,
        etiqueta=plantilla.etiqueta,
        modo_fin=plantilla.modo_fin,
        preguntas_restantes=duracion,
        multiplicador_puntos=plantilla.efecto.multiplicador_puntos,
        fin_partida_si_fallo=plantilla.efecto.fin_partida_si_fallo,
    )


def params_maldicion_desafio_tiempo(numero_pregunta: int) -> tuple[int, int]:
    """(aciertos necesarios, segundos) según progreso de la partida."""
    from Comun.resistencia_motor import factor_progreso_resistencia

    t = factor_progreso_resistencia(numero_pregunta)
    if t < 0.75:
        return (3, 90)
    if t < 0.9:
        return (4, 75)
    return (5, 60)


def instanciar_maldicion_desafio_tiempo(numero_pregunta: int) -> MaldicionActiva:
    from Comun.resistencia_motor import MaldicionActiva

    aciertos, segundos = params_maldicion_desafio_tiempo(numero_pregunta)
    plantilla = _PLANTILLA_DESAFIO_TIEMPO
    return MaldicionActiva(
        id=plantilla.id,
        etiqueta=plantilla.etiqueta,
        modo_fin=ModoFinMaldicion.DESAFIO,
        preguntas_restantes=0,
        desafio=DesafioMaldicionTiempo(
            aciertos_objetivo=aciertos,
            tiempo_limite_seg=segundos,
        ),
    )


def plantilla_maldicion_resistencia(maldicion_id: str) -> PlantillaMaldicionResistencia | None:
    for plantilla in _MALDICIONES_RESISTENCIA:
        if plantilla.id == maldicion_id:
            return plantilla
    return None


def maldicion_tiene_desafio_tiempo(maldicion: _MaldicionConDuracion | None) -> bool:
    return (
        maldicion is not None
        and maldicion.modo_fin == ModoFinMaldicion.DESAFIO
        and maldicion.desafio is not None
    )


def desafio_maldicion_activo(maldicion: _MaldicionConDuracion | None) -> DesafioMaldicionTiempo | None:
    if maldicion is None or not maldicion_tiene_desafio_tiempo(maldicion):
        return None
    return maldicion.desafio


def maldicion_desafio_expirada(maldicion: _MaldicionConDuracion | None) -> bool:
    desafio = desafio_maldicion_activo(maldicion)
    return desafio is not None and desafio.expirado()


def texto_segmento_maldicion_desafio(maldicion: _MaldicionConDuracion | None) -> str | None:
    desafio = desafio_maldicion_activo(maldicion)
    if desafio is None:
        return None
    return f"{desafio.aciertos_logrados}/{desafio.aciertos_objetivo} {desafio.tiempo_restante_seg()}s"


def formatear_aviso_maldicion_desafio(desafio: DesafioMaldicionTiempo) -> str:
    from Comun.resistencia_motor import prefijar_emoji

    n = desafio.aciertos_objetivo
    seg = desafio.tiempo_limite_seg
    texto = (
        f"Maldición: consigue {n} acierto"
        f"{'s' if n != 1 else ''} en {seg} s o pierdes la partida."
    )
    return prefijar_emoji(texto, "⏲️")


def tick_maldicion_desafio_tras_acierto(
    maldicion: _MaldicionConDuracion,
    *,
    acierto: bool,
) -> list[str]:
    """Tras un acierto en resistencia: avanza el desafío o lo completa."""
    from Comun.resistencia_motor import prefijar_emoji

    desafio = desafio_maldicion_activo(maldicion)
    if desafio is None or not acierto:
        return []
    desafio.aciertos_logrados += 1
    if not desafio.completado():
        return []
    return [prefijar_emoji("Desafío de maldición superado.", "✅")]


def mensaje_fin_partida_maldicion_desafio() -> str:
    from Comun.resistencia_motor import prefijar_emoji

    return prefijar_emoji("Maldición de tiempo: tiempo agotado.", "⏲️")


def multiplicador_puntos_maldicion(maldicion: _MaldicionConDuracion | None) -> float:
    if maldicion is None:
        return 1.0
    return max(0.0, min(1.0, maldicion.multiplicador_puntos))


def maldicion_es_fatal(maldicion: _MaldicionConDuracion | None) -> bool:
    """Fallo en pregunta → fin de partida (solo ``fatal``)."""
    return maldicion is not None and maldicion.fin_partida_si_fallo


def maldicion_usa_duracion_preguntas(maldicion: _MaldicionConDuracion | None) -> bool:
    if maldicion is None:
        return False
    return maldicion.modo_fin in (ModoFinMaldicion.DURACION, ModoFinMaldicion.MORTAL)


def maldicion_bloquea_objetos_activa(er) -> bool:
    if er.maldicion is None:
        return False
    plantilla = plantilla_maldicion_resistencia(er.maldicion.id)
    return plantilla is not None and plantilla.efecto.bloquea_objetos


def objetos_bloqueados_efectivo_resistencia(er) -> bool:
    """True si la maldición u otro efecto impide usar el inventario de pregunta."""
    return bool(er.objetos_bloqueados) or maldicion_bloquea_objetos_activa(er)


def reaplicar_efectos_maldicion_persistente(er) -> None:
    """Tras ``reset_pregunta``: restaura flags de maldición que duran varias preguntas."""
    if er.maldicion is None:
        return
    plantilla = plantilla_maldicion_resistencia(er.maldicion.id)
    if plantilla is None:
        return
    if plantilla.efecto.bloquea_objetos:
        er.objetos_bloqueados = True


def limpiar_efectos_maldicion_resistencia(er) -> None:
    """Restaura flags temporales tras purgar o expirar una maldición."""
    er.objetos_bloqueados = False


def mensaje_fallo_maldicion_fatal() -> str:
    return " Maldición mortal: fin de partida."


def puerta_maldicion_fatal_escape(puerta: PuertaEscape | None) -> bool:
    if puerta is None:
        return False
    return bool(puerta.modificadores.fin_partida_si_fallo)


def puerta_tiene_cronometro_puerta_escape(puerta: PuertaEscape | None) -> bool:
    """True si la puerta lleva tiempo total de bloque (no es maldición)."""
    if puerta is None:
        return False
    from Comun.eventos_partida import RASGOS_TIEMPO_PUERTA_ESCAPE

    return bool(
        puerta.modificadores.tiempo_puerta_seg
        and any(
            eid in {"cronometro_bloque", "cronometro_doble"}
            for eid in puerta.modificadores.eventos_ids
        )
    )


def puerta_tiene_maldicion_escape(puerta: PuertaEscape | None) -> bool:
    """True si la puerta lleva ``puerta_maldita`` (única maldición en escape)."""
    return puerta_maldicion_fatal_escape(puerta)


# Alias legado: el cronómetro de puerta no es maldición.
puerta_maldicion_desafio_tiempo_escape = puerta_tiene_cronometro_puerta_escape


__all__ = [
    "DesafioBloqueTiempoResistencia",
    "DesafioMaldicionTiempo",
    "EfectoMaldicion",
    "ModoFinMaldicion",
    "PREGUNTA_MIN_MALDICION_DESAFIO_TIEMPO_RESISTENCIA",
    "PREGUNTA_MIN_MALDICION_RESISTENCIA",
    "PREGUNTA_HARD_PITY_MALDICION_RESISTENCIA",
    "PityMaldicionesResistencia",
    "PlantillaMaldicionResistencia",
    "actualizar_pity_maldiciones_resistencia",
    "debe_forzar_maldicion_resistencia",
    "elegir_plantilla_maldicion_resistencia",
    "probabilidad_activar_maldicion_desafio_resistencia",
    "probabilidad_activar_maldicion_fallo_resistencia",
    "desafio_maldicion_activo",
    "formatear_aviso_maldicion_desafio",
    "instanciar_maldicion_desafio_tiempo",
    "instanciar_maldicion_resistencia",
    "limpiar_efectos_maldicion_resistencia",
    "maldicion_desafio_expirada",
    "maldicion_es_fatal",
    "maldicion_tiene_desafio_tiempo",
    "maldicion_usa_duracion_preguntas",
    "mensaje_fin_partida_maldicion_desafio",
    "mensaje_fallo_maldicion_fatal",
    "maldicion_bloquea_objetos_activa",
    "multiplicador_puntos_maldicion",
    "objetos_bloqueados_efectivo_resistencia",
    "reaplicar_efectos_maldicion_persistente",
    "params_maldicion_desafio_tiempo",
    "plantilla_maldicion_resistencia",
    "plantillas_maldicion_resistencia",
    "puerta_maldicion_desafio_tiempo_escape",
    "puerta_maldicion_fatal_escape",
    "puerta_tiene_cronometro_puerta_escape",
    "puerta_tiene_maldicion_escape",
    "texto_segmento_maldicion_desafio",
    "tick_maldicion_desafio_tras_acierto",
]
