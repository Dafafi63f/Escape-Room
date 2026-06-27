#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogo común de eventos/desafíos (resistencia y escape room).

En escape room cada entrada del catálogo tiene un ``rol_escape``:

* **PUERTA** — rasgos combinables de la puerta (relámpago, niebla, tiempo…).
* **CONTENIDO** — filtro de preguntas (materia, grupo, dificultad, tipo).

Resistencia usa ``modificadores`` en tiempo de partida; el escape separa
puerta (juego) y evento (pool) a partir del mismo catálogo. Los eventos sí/no
de resistencia (decisión antes de la pregunta) también están en este módulo.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from enum import Enum
from typing import TYPE_CHECKING, Literal

from Comun.motor_nucleo import EstadoPartida
from Comun.reglas_partida import sumar_puntos_arcade

from Comun.emojis_escape import (
    CAPAS_ICONO_PROTEGIDO_ESCAPE,
    CapaIconoEscape,
    EMOJI_BOTIN_ESCAPE,
    MAX_ICONOS_CARTA_PUERTA,
    EMOJI_RECOMPENSA_VIDA,
    EMOJI_RECOMPENSA_VIDA_MAX,
    EMOJI_CRONO_BLOQUE,
    EMOJI_CRONO_DOBLE,
    EMOJI_CRONO_PREGUNTA,
    EMOJI_DESCANSO,
    EMOJI_TIENDA,
    EMOJI_DIF_BALANCEADO,
    EMOJI_DIF_DIFICIL,
    EMOJI_DIF_FACIL,
    EMOJI_DIF_MEDIA,
    EMOJI_DOBLE_PUNTOS,
    EMOJI_JEFE,
    EMOJI_MIX_MATERIA,
    EMOJI_NIEBLA_OPCIONES,
    EMOJI_PUERTA_GRUPO,
    EMOJI_PUERTA_MATERIA,
    EMOJI_TIPO_CALCULO,
    EMOJI_TIPO_TEORIA,
    EMOJI_TRIPLE_PUNTOS,
    TOOLTIP_DIF_BALANCEADO,
    TOOLTIP_DIF_DIFICIL,
    TOOLTIP_DIF_FACIL,
    TOOLTIP_DIF_MEDIA,
    TOOLTIP_MIX_MATERIA,
    TOOLTIP_PUERTA_GRUPO,
    TOOLTIP_PUERTA_MATERIA,
    TOOLTIP_BOTIN,
    TOOLTIP_BOTIN_DESCANSO,
    TOOLTIP_TIENDA,
    TOOLTIP_TIPO_CALCULO,
    TOOLTIP_TIPO_TEORIA,
    _IDS_PERFIL_MIX_MATERIA,
    capa_evento_escape,
)

if TYPE_CHECKING:
    from Comun.modelos import Pregunta
    from Comun.resistencia_motor import EstadoResistencia
    from Comun.resistencia_partida import EventoAleatorioResistencia
    from Comun.objetos_partida import ArticuloTienda


class AlcanceEvento(str, Enum):
    COMPARTIDO = "compartido"
    RESISTENCIA = "resistencia"
    ESCAPE = "escape"


class RolEscape(str, Enum):
    PUERTA = "puerta"
    CONTENIDO = "contenido"


@dataclass(frozen=True)
class ModificadoresDesafio:
    """Parámetros de juego (resistencia en vivo; rasgos de puerta en escape)."""

    n_preguntas: int = 1
    tiempo_pregunta_seg: int | None = None
    tiempo_puerta_seg: int | None = None
    dificultades_permitidas: frozenset[str] | None = None
    opciones_ocultas: int = 0
    multiplicador_puntos: int = 1
    delta_vidas_al_completar: int = 0
    delta_vidas_max_al_completar: int = 0
    sin_pregunta: bool = False
    powerup_al_completar: str | None = None


@dataclass(frozen=True)
class ParamsNiebla:
    """Opciones ocultas por niebla (solo respuestas; el enunciado no se recorta)."""

    opciones_ocultas: int


RASGOS_NIEBLA = frozenset({"niebla_opciones"})
_SALA_MIN_NIEBLA_OPCIONES = 18
_SALA_REF_NIEBLA: dict[str, int] = {
    "niebla_opciones": 20,
}
PREGUNTA_MIN_NIEBLA_RESISTENCIA = 25


def _opciones_ocultas_escape(numero_sala: int) -> int:
    if numero_sala < _SALA_MIN_NIEBLA_OPCIONES:
        return 0
    return 1


def params_niebla_escape(tipo: str, numero_sala: int) -> ParamsNiebla:
    """Intensidad de niebla en escape: como máximo 1 respuesta oculta."""
    if tipo == "niebla_opciones":
        return ParamsNiebla(_opciones_ocultas_escape(numero_sala))
    raise ValueError(f"Tipo de niebla desconocido: {tipo!r}")


def params_niebla_resistencia(tipo: str, numero_pregunta: int, intensidad: float) -> ParamsNiebla:
    """Niebla en resistencia: 1 respuesta oculta al azar (puede ser la correcta)."""
    del numero_pregunta, intensidad
    if tipo == "niebla_opciones":
        return ParamsNiebla(1)
    raise ValueError(f"Tipo de niebla desconocido: {tipo!r}")


@dataclass(frozen=True)
class ParamsTiempo:
    tiempo_pregunta_seg: int | None = None
    tiempo_puerta_seg: int | None = None


RASGOS_TIEMPO = frozenset({
    "cronometro_pregunta",
    "cronometro_bloque",
    "cronometro_doble",
    "relampago",
})
RASGOS_TIEMPO_PUERTA_ESCAPE = frozenset({
    "cronometro_pregunta",
    "cronometro_bloque",
    "cronometro_doble",
})
_SALA_MIN_TIEMPO_PREGUNTA = 4
_SALA_MIN_TIEMPO_BLOQUE = 5
_SALA_MIN_TIEMPO_DOBLE = 10
_SALA_REF_TIEMPO: dict[str, int] = {
    "cronometro_pregunta": 12,
    "cronometro_bloque": 10,
    "cronometro_doble": 12,
    "relampago": 25,
}


def _tiempo_pregunta_escape(numero_sala: int) -> int:
    if numero_sala <= 15:
        return 35
    if numero_sala <= 21:
        return 28
    if numero_sala <= 25:
        return 25
    return 20


def _tiempo_puerta_escape(numero_sala: int) -> int:
    if numero_sala <= 15:
        return 120
    if numero_sala <= 22:
        return 100
    if numero_sala <= 27:
        return 85
    return 70


def params_tiempo_escape(tipo: str, numero_sala: int) -> ParamsTiempo:
    """Límites de tiempo en escape según el tipo y la sala."""
    if tipo == "cronometro_pregunta":
        return ParamsTiempo(tiempo_pregunta_seg=_tiempo_pregunta_escape(numero_sala))
    if tipo == "cronometro_bloque":
        return ParamsTiempo(tiempo_puerta_seg=_tiempo_puerta_escape(numero_sala))
    if tipo == "cronometro_doble":
        return ParamsTiempo(
            tiempo_puerta_seg=_tiempo_puerta_escape(numero_sala) + 30,
            tiempo_pregunta_seg=max(20, _tiempo_pregunta_escape(numero_sala) - 7),
        )
    raise ValueError(f"Tipo de tiempo desconocido: {tipo!r}")


def params_tiempo_resistencia(tipo: str, numero_pregunta: int, intensidad: float) -> ParamsTiempo:
    """Límite por pregunta en resistencia (relámpago); más ajustado con progreso e intensidad."""
    from Comun.resistencia_motor import PREGUNTA_MIN_EVENTOS_ALEATORIOS

    if tipo != "relampago":
        raise ValueError(f"Tipo de tiempo desconocido: {tipo!r}")
    progreso = min(
        1.0,
        max(0.0, (numero_pregunta - PREGUNTA_MIN_EVENTOS_ALEATORIOS) / 120.0),
    )
    techo = max(6, int(round(11 - progreso * 5)))
    seg = max(3, int(techo - (techo - 3) * intensidad))
    return ParamsTiempo(tiempo_pregunta_seg=seg)


def _fusionar_tiempo(actual: int | None, nuevo: int | None) -> int | None:
    if nuevo is None:
        return actual
    if actual is None:
        return nuevo
    return min(actual, nuevo)


@dataclass(frozen=True)
class OpcionesContenidoEscape:
    """Cómo instanciar un evento de contenido (materia/grupo concretos en runtime)."""

    usa_grupo: bool = False
    usa_materia: bool = True
    tipos_permitidos: frozenset[str] | None = None


@dataclass(frozen=True)
class DefinicionEvento:
    id: str
    nombre: str
    descripcion: str
    emoji: str
    alcance: AlcanceEvento
    modificadores: ModificadoresDesafio
    rol_escape: RolEscape | None = None
    nivel_min_sala_escape: int = 1
    exclusivo_puerta_escape: bool = False
    contenido_escape: OpcionesContenidoEscape | None = None


@dataclass(frozen=True)
class ModificadoresPuerta:
    """Rasgos de juego combinados de una puerta escape (derivados del catálogo)."""

    tiempo_pregunta_seg: int | None = None
    tiempo_puerta_seg: int | None = None
    opciones_ocultas: int = 0
    multiplicador_puntos: int = 1
    sin_pregunta: bool = False
    delta_vidas_al_completar: int = 0
    delta_vidas_max_al_completar: int = 0
    rasgos: tuple[str, ...] = ()
    eventos_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class IconoEfectoPuerta:
    """Emoji + ayuda para la fila superior de una carta de puerta."""

    emoji: str
    tooltip: str
    capa: CapaIconoEscape


@dataclass(frozen=True)
class PerfilContenidoMateria:
    """Filtros de dificultad/tipo sobre la puerta de materia (no es un tipo de puerta aparte)."""

    id: str
    descripcion_filtro: str
    mod: ModificadoresDesafio
    opts: OpcionesContenidoEscape | None = None
    nivel_min_sala: int = 1


@dataclass(frozen=True)
class EventoContenidoInstanciado:
    """Evento de contenido con materia/grupo ya resueltos para una puerta."""

    definicion: DefinicionEvento
    materia: str | None = None
    grupo: str | None = None
    perfil_id: str | None = None

    @property
    def id(self) -> str:
        return self.definicion.id

    @property
    def nombre(self) -> str:
        return self.definicion.nombre

    @property
    def etiqueta_foco(self) -> str | None:
        """Materia o bloque temático concreto de esta puerta."""
        if self.materia:
            return self.materia
        if self.grupo:
            from Comun.config_historia import etiqueta_grupo_tematico

            return etiqueta_grupo_tematico(self.grupo)
        return None

    @property
    def descripcion(self) -> str:
        return self.definicion.descripcion

    @property
    def emoji(self) -> str:
        return self.definicion.emoji

    @property
    def dificultades_permitidas(self) -> frozenset[str] | None:
        return self.definicion.modificadores.dificultades_permitidas

    @property
    def tipos_permitidos(self) -> frozenset[str] | None:
        if self.contenido_escape is None:
            return None
        return self.contenido_escape.tipos_permitidos

    @property
    def contenido_escape(self) -> OpcionesContenidoEscape | None:
        return self.definicion.contenido_escape


def _c(
    id: str,
    nombre: str,
    descripcion: str,
    emoji: str,
    alcance: AlcanceEvento,
    mod: ModificadoresDesafio,
    *,
    rol_escape: RolEscape | None = None,
    nivel_min_sala_escape: int = 1,
    exclusivo_puerta_escape: bool = False,
    contenido_escape: OpcionesContenidoEscape | None = None,
) -> DefinicionEvento:
    return DefinicionEvento(
        id=id,
        nombre=nombre,
        descripcion=descripcion,
        emoji=emoji,
        alcance=alcance,
        modificadores=mod,
        rol_escape=rol_escape,
        nivel_min_sala_escape=nivel_min_sala_escape,
        exclusivo_puerta_escape=exclusivo_puerta_escape,
        contenido_escape=contenido_escape,
    )


def _def_botin_objeto_escape(
    evento_id: str,
    *,
    powerup_id: str,
    nivel_min_sala: int = 2,
    descripcion: str | None = None,
) -> DefinicionEvento:
    from Comun.resistencia_motor import descripcion_powerup, etiqueta_powerup

    premio = descripcion or descripcion_powerup(powerup_id) or etiqueta_powerup(powerup_id)
    return _c(
        evento_id,
        "Botín",
        f"Al superar la puerta sin fallar: {premio}.",
        EMOJI_BOTIN_ESCAPE,
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(powerup_al_completar=powerup_id),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=nivel_min_sala,
    )


_CATALOGO: tuple[DefinicionEvento, ...] = (
    # --- Contenido escape: tres tipos principales (materia, grupo; descanso es rasgo PUERTA) ---
    _c(
        "puerta_materia",
        "Puerta de materia",
        "Preguntas de una materia concreta del plan.",
        EMOJI_PUERTA_MATERIA,
        AlcanceEvento.COMPARTIDO,
        ModificadoresDesafio(),
        rol_escape=RolEscape.CONTENIDO,
        contenido_escape=OpcionesContenidoEscape(),
    ),
    _c(
        "puerta_grupo",
        "Puerta de grupo",
        "Preguntas de varias materias de un mismo bloque temático del plan.",
        EMOJI_PUERTA_GRUPO,
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(),
        rol_escape=RolEscape.CONTENIDO,
        nivel_min_sala_escape=6,
        contenido_escape=OpcionesContenidoEscape(usa_grupo=True, usa_materia=False),
    ),
    # --- Puerta escape (rasgos de juego combinables) ---
    _c(
        "descanso",
        "Descanso",
        "Sin preguntas; avanzas sin bloque de preguntas.",
        EMOJI_DESCANSO,
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(sin_pregunta=True),
        rol_escape=RolEscape.PUERTA,
        exclusivo_puerta_escape=True,
    ),
    _c(
        "tienda",
        "Tienda",
        "Sin preguntas; compra ayudas con tus puntos.",
        EMOJI_TIENDA,
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(sin_pregunta=True),
        rol_escape=RolEscape.PUERTA,
        exclusivo_puerta_escape=True,
        nivel_min_sala_escape=2,
    ),
    _c(
        "botin",
        "Botín",
        "Al superar la puerta sin fallar: +1 vida.",
        EMOJI_BOTIN_ESCAPE,
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(delta_vidas_al_completar=1),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=6,
    ),
    _c(
        "botin_corazon_max",
        "Botín corazón",
        "Al superar la puerta sin fallar: +1 al máximo de vidas.",
        EMOJI_BOTIN_ESCAPE,
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(delta_vidas_max_al_completar=1),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=12,
    ),
    _def_botin_objeto_escape("botin_bomba", powerup_id="bomba"),
    _def_botin_objeto_escape("botin_fifty_fifty", powerup_id="fifty_fifty"),
    _def_botin_objeto_escape("botin_tiempo_extra", powerup_id="tiempo_extra"),
    _def_botin_objeto_escape("botin_cambio", powerup_id="cambio"),
    _def_botin_objeto_escape("botin_skip", powerup_id="skip"),
    _def_botin_objeto_escape("botin_escudo", powerup_id="escudo", nivel_min_sala=6),
    _def_botin_objeto_escape(
        "botin_refuerzo",
        powerup_id="vida_refuerzo",
        nivel_min_sala=4,
        descripcion="+1 vida al superar (si hay hueco en el tope)",
    ),
    _def_botin_objeto_escape(
        "botin_amuleto",
        powerup_id="amuleto_puntos",
        nivel_min_sala=4,
        descripcion="+20 pts en tu próximo acierto",
    ),
    _c(
        "niebla_opciones",
        "Niebla en opciones",
        "Oculta 1 respuesta al azar (puede ser la correcta).",
        EMOJI_NIEBLA_OPCIONES,
        AlcanceEvento.COMPARTIDO,
        ModificadoresDesafio(),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=_SALA_MIN_NIEBLA_OPCIONES,
    ),
    _c(
        "relampago",
        "Relámpago",
        "Poco tiempo para responder; más ajustado según el progreso.",
        "⚡",
        AlcanceEvento.COMPARTIDO,
        ModificadoresDesafio(),
    ),
    _c(
        "cronometro_bloque",
        "Cronómetro de bloque",
        "Tiempo total para contestar toda la puerta; más ajustado en salas altas.",
        EMOJI_CRONO_BLOQUE,
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=_SALA_MIN_TIEMPO_BLOQUE,
    ),
    _c(
        "cronometro_pregunta",
        "Cronómetro",
        "Límite de tiempo en cada pregunta; más ajustado en salas altas.",
        EMOJI_CRONO_PREGUNTA,
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=_SALA_MIN_TIEMPO_PREGUNTA,
    ),
    _c(
        "cronometro_doble",
        "Doble cronómetro",
        "Tiempo total para la puerta y límite por pregunta.",
        EMOJI_CRONO_DOBLE,
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=_SALA_MIN_TIEMPO_DOBLE,
    ),
    _c(
        "doble_puntos",
        "Puntos dobles",
        "Cada acierto de la puerta vale ×2 en arcade.",
        EMOJI_DOBLE_PUNTOS,
        AlcanceEvento.COMPARTIDO,
        ModificadoresDesafio(multiplicador_puntos=2),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=8,
    ),
    _c(
        "triple_puntos",
        "Puntos triples",
        "El acierto vale el triple en arcade.",
        EMOJI_TRIPLE_PUNTOS,
        AlcanceEvento.RESISTENCIA,
        ModificadoresDesafio(multiplicador_puntos=3),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=24,
    ),
)

_POR_ID: dict[str, DefinicionEvento] = {e.id: e for e in _CATALOGO}

_PERFILES_MATERIA_ESCAPE: tuple[PerfilContenidoMateria, ...] = (
    PerfilContenidoMateria(
        "balanceado",
        "Cualquier dificultad.",
        ModificadoresDesafio(),
    ),
    PerfilContenidoMateria(
        "facil",
        "Solo preguntas fáciles.",
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Facil"})),
    ),
    PerfilContenidoMateria(
        "media",
        "Solo preguntas de dificultad media.",
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Media"})),
    ),
    PerfilContenidoMateria(
        "mix_facil_media",
        "Dificultad: fácil o media.",
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Facil", "Media"})),
    ),
    PerfilContenidoMateria(
        "mix_facil_dificil",
        "Dificultad: fácil o difícil.",
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Facil", "Dificil"})),
        nivel_min_sala=6,
    ),
    PerfilContenidoMateria(
        "mix_media_dificil",
        "Dificultad: media o difícil.",
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Media", "Dificil"})),
        nivel_min_sala=10,
    ),
    PerfilContenidoMateria(
        "dificil",
        "Solo preguntas difíciles.",
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Dificil"})),
        nivel_min_sala=18,
    ),
    PerfilContenidoMateria(
        "teoria",
        "Solo preguntas teóricas.",
        ModificadoresDesafio(),
        opts=OpcionesContenidoEscape(tipos_permitidos=frozenset({"Teoria"})),
        nivel_min_sala=8,
    ),
    PerfilContenidoMateria(
        "calculo",
        "Solo preguntas de cálculo.",
        ModificadoresDesafio(),
        opts=OpcionesContenidoEscape(tipos_permitidos=frozenset({"Calculo"})),
        nivel_min_sala=8,
    ),
)

_PERFIL_MATERIA_POR_ID: dict[str, PerfilContenidoMateria] = {
    p.id: p for p in _PERFILES_MATERIA_ESCAPE
}

_ALIAS_CONTENIDO_LEGACY: dict[str, str] = {
    "pregunta_unica": "balanceado",
    "solo_facil": "facil",
    "solo_media": "media",
    "mix_facil_media": "mix_facil_media",
    "mix": "mix_facil_media",
    "solo_dificil": "dificil",
    "mezcla_media_dificil": "mix_media_dificil",
    "solo_teoria": "teoria",
    "solo_calculo": "calculo",
    "repaso_teorico": "teoria",
    "calculo_exigente": "calculo",
    "bloque_grupo": "puerta_grupo",
}

_ALIAS_RESISTENCIA: dict[str, str] = {
    "relampago": "relampago",
    "opciones_ocultas": "niebla_opciones",
    "doble": "doble_puntos",
}

_MAX_RASGOS_PUERTA_COMBINADOS = max(1, MAX_ICONOS_CARTA_PUERTA - 3)
_PROB_BASE_DESCANSO_PUERTA = 0.06
_PROB_BASE_TIENDA_PUERTA = 0.03
_PITY_INCREMENT_DESCANSO_POR_SALA = 0.04
_PITY_INCREMENT_TIENDA_POR_SALA = 0.05
_PROB_PUERTA_ESPECIAL_MAX = 0.48
SALAS_HARD_PITY_DESCANSO_ESCAPE = 5
SALAS_HARD_PITY_TIENDA_ESCAPE = 10
_PROB_BOTIN_BASE = 0.14
RASGOS_BOTIN_VIDAS_ESCAPE = frozenset({"botin", "botin_corazon_max"})
_IDS_BOTIN_POWERUP_ESCAPE = (
    "botin_bomba",
    "botin_fifty_fifty",
    "botin_tiempo_extra",
    "botin_cambio",
    "botin_skip",
    "botin_escudo",
    "botin_refuerzo",
    "botin_amuleto",
)
RASGOS_BOTIN_POWERUP_ESCAPE = frozenset(_IDS_BOTIN_POWERUP_ESCAPE)
RASGOS_BOTIN_ESCAPE = RASGOS_BOTIN_VIDAS_ESCAPE | RASGOS_BOTIN_POWERUP_ESCAPE
RASGOS_RECOMPENSA_VIDAS_ESCAPE = RASGOS_BOTIN_VIDAS_ESCAPE
SALAS_HARD_PITY_BOTIN_ESCAPE = 3
RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE = frozenset({"descanso", "tienda"})
RASGOS_EXTRA_PUERTA_SIN_PREGUNTA_ESCAPE = RASGOS_BOTIN_ESCAPE  # solo descanso; ver extras_escape_para_pausa
_RASGOS_SOLO_RECOMPENSA = RASGOS_BOTIN_ESCAPE
RASGOS_NIEBLA_PUERTA_ESCAPE = frozenset({"niebla_opciones"})
RASGOS_MULTIPLICADOR_PUERTA_ESCAPE = frozenset({
    "doble_puntos",
    "triple_puntos",
})
_FAMILIAS_EXCLUSIVAS_PUERTA: tuple[frozenset[str], ...] = (
    RASGOS_TIEMPO_PUERTA_ESCAPE,
    RASGOS_MULTIPLICADOR_PUERTA_ESCAPE,
    RASGOS_NIEBLA_PUERTA_ESCAPE,
)


def extras_escape_para_pausa(pausa_id: str) -> frozenset[str]:
    """Rasgos combinables con una puerta sin preguntas (descanso admite botín; tienda, no)."""
    if pausa_id == "descanso":
        return RASGOS_BOTIN_ESCAPE
    return frozenset()


@dataclass
class PityPuertasEspecialesEscape:
    """Salas seguidas sin ver descanso, tienda o botín; sube la probabilidad por puerta."""

    salas_sin_descanso: int = 0
    salas_sin_tienda: int = 0
    salas_sin_botin: int = 0


def prob_puerta_especial_con_pity(
    *,
    prob_base: float,
    salas_sin_ver: int,
    incremento_por_sala: float,
    prob_max: float = _PROB_PUERTA_ESPECIAL_MAX,
) -> float:
    if salas_sin_ver <= 0:
        return prob_base
    return min(prob_max, prob_base + salas_sin_ver * incremento_por_sala)


def debe_garantizar_descanso_escape(
    pity: PityPuertasEspecialesEscape,
    numero_sala: int,
) -> bool:
    """Hard pity: en la sala N, si aún no hubo descanso, se fuerza uno."""
    return (
        numero_sala >= SALAS_HARD_PITY_DESCANSO_ESCAPE
        and pity.salas_sin_descanso >= SALAS_HARD_PITY_DESCANSO_ESCAPE - 1
    )


def debe_garantizar_tienda_escape(
    pity: PityPuertasEspecialesEscape,
    numero_sala: int,
) -> bool:
    """Hard pity: en la sala N, si aún no hubo tienda, se fuerza una."""
    min_sala = evento_por_id("tienda").nivel_min_sala_escape
    if numero_sala < SALAS_HARD_PITY_TIENDA_ESCAPE:
        return False
    umbral_sin = SALAS_HARD_PITY_TIENDA_ESCAPE - min_sala
    return pity.salas_sin_tienda >= umbral_sin


def debe_garantizar_botin_escape(
    pity: PityPuertasEspecialesEscape,
    numero_sala: int,
) -> bool:
    """Hard pity: cada 3 salas sin botín, se fuerza uno en una puerta normal."""
    min_sala = min(
        evento_por_id(eid).nivel_min_sala_escape for eid in RASGOS_BOTIN_ESCAPE
    )
    if numero_sala < min_sala:
        return False
    return pity.salas_sin_botin >= SALAS_HARD_PITY_BOTIN_ESCAPE - 1


def elegir_botin_para_sala(
    numero_sala: int,
    rng: random.Random,
) -> DefinicionEvento | None:
    """Elige un botín (vida u objeto) elegible para la sala."""
    disponibles = [
        evento_por_id(eid)
        for eid in sorted(RASGOS_BOTIN_ESCAPE)
        if evento_por_id(eid).nivel_min_sala_escape <= numero_sala
    ]
    if not disponibles:
        return None
    return rng.choice(disponibles)


def _sala_tiene_botin(puertas: tuple) -> bool:
    for puerta in puertas:
        mods = puerta.modificadores if hasattr(puerta, "modificadores") else puerta
        if any(eid in RASGOS_BOTIN_ESCAPE for eid in mods.eventos_ids):
            return True
    return False


def actualizar_pity_tras_sala(
    pity: PityPuertasEspecialesEscape,
    puertas: tuple,
    *,
    numero_sala: int,
    estado=None,
    vidas_max: int | None = None,
) -> PityPuertasEspecialesEscape:
    """Tras generar una sala: resetea el pity del tipo que salió o acumula +1."""

    def _ids(puerta) -> tuple[str, ...]:
        mods = puerta.modificadores if hasattr(puerta, "modificadores") else puerta
        return mods.eventos_ids

    hubo_descanso = any("descanso" in _ids(p) for p in puertas)
    hubo_tienda = any("tienda" in _ids(p) for p in puertas)
    hubo_botin = _sala_tiene_botin(puertas)
    tienda_elegible = numero_sala >= evento_por_id("tienda").nivel_min_sala_escape
    salas_sin_tienda = pity.salas_sin_tienda
    if hubo_tienda:
        salas_sin_tienda = 0
    elif tienda_elegible:
        salas_sin_tienda = pity.salas_sin_tienda + 1
        if estado is not None and numero_sala >= SALAS_HARD_PITY_TIENDA_ESCAPE:
            from Comun.tienda_escape import puede_visitar_tienda_escape

            if not puede_visitar_tienda_escape(
                numero_sala, estado, vidas_max=vidas_max
            ):
                umbral = SALAS_HARD_PITY_TIENDA_ESCAPE - evento_por_id(
                    "tienda"
                ).nivel_min_sala_escape
                if pity.salas_sin_tienda >= umbral:
                    salas_sin_tienda = max(salas_sin_tienda, umbral)
    return PityPuertasEspecialesEscape(
        salas_sin_descanso=0 if hubo_descanso else pity.salas_sin_descanso + 1,
        salas_sin_tienda=salas_sin_tienda,
        salas_sin_botin=0 if hubo_botin else pity.salas_sin_botin + 1,
    )


def _rasgos_pausa_generados(
    pausa: DefinicionEvento,
    *,
    numero_sala: int,
    rng: random.Random,
) -> tuple[DefinicionEvento, ...]:
    rasgos: list[DefinicionEvento] = [pausa]
    extras_permitidos = extras_escape_para_pausa(pausa.id)
    if extras_permitidos:
        prob_botin = _PROB_BOTIN_BASE + min(0.03, (numero_sala - 1) * 0.001)
        if rng.random() < prob_botin:
            botin = elegir_botin_para_sala(numero_sala, rng)
            if botin is not None and botin.id in extras_permitidos:
                rasgos.append(botin)
    return tuple(rasgos)


def _intentar_modificadores_pausa_especial(
    *,
    numero_sala: int,
    rng: random.Random,
    pausas_usadas: frozenset[str],
    pity: PityPuertasEspecialesEscape | None,
    estado=None,
    vidas_max: int | None = None,
) -> ModificadoresPuerta | None:
    """Tira descanso y tienda por separado (pity independiente); descanso primero."""
    p = pity or PityPuertasEspecialesEscape()
    extra_sala = min(0.025, (numero_sala - 1) * 0.0015)
    descanso_ev = evento_por_id("descanso")
    tienda_ev = evento_por_id("tienda")

    if "descanso" not in pausas_usadas:
        prob_descanso = prob_puerta_especial_con_pity(
            prob_base=_PROB_BASE_DESCANSO_PUERTA + extra_sala,
            salas_sin_ver=p.salas_sin_descanso,
            incremento_por_sala=_PITY_INCREMENT_DESCANSO_POR_SALA,
        )
        if rng.random() < prob_descanso:
            return combinar_modificadores_puerta(
                _rasgos_pausa_generados(descanso_ev, numero_sala=numero_sala, rng=rng),
                numero_sala=numero_sala,
            )

    if (
        "tienda" not in pausas_usadas
        and numero_sala >= tienda_ev.nivel_min_sala_escape
    ):
        tienda_viable = True
        if estado is not None:
            from Comun.tienda_escape import puede_visitar_tienda_escape

            tienda_viable = puede_visitar_tienda_escape(
                numero_sala, estado, vidas_max=vidas_max
            )
        if tienda_viable:
            prob_tienda = prob_puerta_especial_con_pity(
                prob_base=_PROB_BASE_TIENDA_PUERTA,
                salas_sin_ver=p.salas_sin_tienda,
                incremento_por_sala=_PITY_INCREMENT_TIENDA_POR_SALA,
            )
            if rng.random() < prob_tienda:
                return combinar_modificadores_puerta(
                    _rasgos_pausa_generados(tienda_ev, numero_sala=numero_sala, rng=rng),
                    numero_sala=numero_sala,
                )
    return None


def perfiles_materia_escape_para_sala(numero_sala: int) -> tuple[PerfilContenidoMateria, ...]:
    return tuple(p for p in _PERFILES_MATERIA_ESCAPE if p.nivel_min_sala <= numero_sala)


def perfil_materia_por_id(perfil_id: str) -> PerfilContenidoMateria:
    if perfil_id not in _PERFIL_MATERIA_POR_ID:
        raise KeyError(f"Perfil de materia desconocido: {perfil_id!r}")
    return _PERFIL_MATERIA_POR_ID[perfil_id]


def definicion_materia_con_perfil(perfil: PerfilContenidoMateria) -> DefinicionEvento:
    base = _POR_ID["puerta_materia"]
    opts = perfil.opts or base.contenido_escape or OpcionesContenidoEscape()
    desc = f"{base.descripcion} {perfil.descripcion_filtro}".strip()
    return replace(
        base,
        descripcion=desc,
        modificadores=perfil.mod,
        contenido_escape=opts,
    )


def definicion_grupo_con_perfil(perfil: PerfilContenidoMateria) -> DefinicionEvento:
    base = _POR_ID["puerta_grupo"]
    opts_base = base.contenido_escape or OpcionesContenidoEscape(
        usa_grupo=True, usa_materia=False
    )
    if perfil.opts:
        opts = replace(
            opts_base,
            tipos_permitidos=perfil.opts.tipos_permitidos,
        )
    else:
        opts = opts_base
    desc = f"{base.descripcion} {perfil.descripcion_filtro}".strip()
    return replace(
        base,
        descripcion=desc,
        modificadores=perfil.mod,
        contenido_escape=opts,
    )


def elegir_plantillas_contenido_escape(
    cantidad: int,
    numero_sala: int,
    rng: random.Random,
) -> tuple[tuple[DefinicionEvento, str | None], ...]:
    """Elige plantillas de contenido: puerta de materia (con perfil) o puerta de grupo."""
    if cantidad <= 0:
        return ()
    perfiles = list(perfiles_materia_escape_para_sala(numero_sala))
    rng.shuffle(perfiles)
    grupo_disponible = (
        _POR_ID["puerta_grupo"].nivel_min_sala_escape <= numero_sala
    )
    elegidas: list[tuple[DefinicionEvento, str | None]] = []
    grupo_asignado = False
    for i in range(cantidad):
        usar_grupo = (
            grupo_disponible
            and not grupo_asignado
            and (i == cantidad - 1 or rng.random() < 0.34)
        )
        if usar_grupo:
            if perfiles:
                perfil = perfiles.pop(0)
            else:
                perfil = rng.choice(perfiles_materia_escape_para_sala(numero_sala))
            elegidas.append((definicion_grupo_con_perfil(perfil), perfil.id))
            grupo_asignado = True
            continue
        if perfiles:
            perfil = perfiles.pop(0)
        else:
            perfil = rng.choice(perfiles_materia_escape_para_sala(numero_sala))
        elegidas.append((definicion_materia_con_perfil(perfil), perfil.id))
    rng.shuffle(elegidas)
    return tuple(elegidas[:cantidad])


def elegir_eventos_contenido_escape(
    plantillas: tuple[DefinicionEvento, ...],
    cantidad: int,
    rng: random.Random,
) -> tuple[DefinicionEvento, ...]:
    """Elige eventos de contenido distintos cuando el pool lo permite."""
    if not plantillas or cantidad <= 0:
        return ()
    lista = list(plantillas)
    rng.shuffle(lista)
    if len(lista) >= cantidad:
        return tuple(rng.sample(lista, cantidad))
    elegidas = list(lista)
    while len(elegidas) < cantidad:
        elegidas.append(rng.choice(lista))
    return tuple(elegidas[:cantidad])


def materias_distintas_puertas(
    materias_pool: tuple[str, ...],
    cantidad: int,
    rng: random.Random,
) -> tuple[str, ...]:
    if not materias_pool:
        return ()
    if len(materias_pool) >= cantidad:
        return tuple(rng.sample(materias_pool, cantidad))
    elegidas = list(materias_pool)
    rng.shuffle(elegidas)
    while len(elegidas) < cantidad:
        elegidas.append(rng.choice(materias_pool))
    return tuple(elegidas[:cantidad])


def catalogo_eventos() -> tuple[DefinicionEvento, ...]:
    return _CATALOGO


def evento_por_id(evento_id: str) -> DefinicionEvento:
    clave = _ALIAS_RESISTENCIA.get(evento_id, evento_id)
    if clave in _ALIAS_CONTENIDO_LEGACY:
        destino = _ALIAS_CONTENIDO_LEGACY[clave]
        if destino == "puerta_grupo":
            return _POR_ID["puerta_grupo"]
        return definicion_materia_con_perfil(perfil_materia_por_id(destino))
    if clave == "respiro":
        return _POR_ID["botin"]
    if clave not in _POR_ID:
        raise KeyError(f"Evento desconocido: {evento_id!r}")
    return _POR_ID[clave]


def eventos_para_resistencia() -> tuple[DefinicionEvento, ...]:
    return tuple(
        e
        for e in _CATALOGO
        if e.alcance in {AlcanceEvento.COMPARTIDO, AlcanceEvento.RESISTENCIA}
    )


def eventos_para_escape() -> tuple[DefinicionEvento, ...]:
    """Todas las entradas del catálogo usadas en escape (puerta o contenido)."""
    return tuple(e for e in _CATALOGO if e.rol_escape is not None)


def eventos_puerta_escape_para_sala(numero_sala: int) -> tuple[DefinicionEvento, ...]:
    return tuple(
        e
        for e in _CATALOGO
        if e.rol_escape == RolEscape.PUERTA and e.nivel_min_sala_escape <= numero_sala
    )


def eventos_contenido_escape_para_sala(numero_sala: int) -> tuple[DefinicionEvento, ...]:
    return tuple(
        e
        for e in _CATALOGO
        if e.rol_escape == RolEscape.CONTENIDO and e.nivel_min_sala_escape <= numero_sala
    )


def evento_sin_pregunta_escape(
    modificadores: ModificadoresPuerta,
) -> DefinicionEvento | None:
    """Tipo de puerta sin preguntas (descanso, tienda, …)."""
    for eid in modificadores.eventos_ids:
        if eid in RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE:
            return evento_por_id(eid)
    return None


def _indices_familias_rasgo_puerta(event_id: str) -> frozenset[int]:
    return frozenset(
        i for i, familia in enumerate(_FAMILIAS_EXCLUSIVAS_PUERTA) if event_id in familia
    )


def _compatible_con_rasgos_puerta(
    candidato: DefinicionEvento,
    elegidos: tuple[DefinicionEvento, ...],
) -> bool:
    """Un rasgo no puede repetir familia exclusiva con otro ya elegido."""
    if candidato.exclusivo_puerta_escape:
        permitidos = extras_escape_para_pausa(candidato.id)
        return all(e.id in permitidos for e in elegidos)
    if any(e.exclusivo_puerta_escape for e in elegidos):
        pausa = next(e for e in elegidos if e.exclusivo_puerta_escape)
        return candidato.id in extras_escape_para_pausa(pausa.id)
    familias_c = _indices_familias_rasgo_puerta(candidato.id)
    if not familias_c:
        return True
    for ev in elegidos:
        if familias_c & _indices_familias_rasgo_puerta(ev.id):
            return False
    return True


def _filtrar_rasgos_puerta_compatibles(
    rasgos: tuple[DefinicionEvento, ...],
) -> tuple[DefinicionEvento, ...]:
    """Conserva el orden; en pausa solo el tipo y, si aplica, botines (descanso)."""
    if not rasgos:
        return ()
    pausa = next((r for r in rasgos if r.exclusivo_puerta_escape), None)
    if pausa is not None:
        extras = tuple(
            r for r in rasgos if r.id in extras_escape_para_pausa(pausa.id)
        )
        return (pausa, *extras)
    elegidos: list[DefinicionEvento] = []
    for ev in rasgos:
        if _compatible_con_rasgos_puerta(ev, tuple(elegidos)):
            elegidos.append(ev)
    return tuple(elegidos)


def _modificadores_puerta_sin_pregunta(
    pausa: DefinicionEvento,
    recompensas: tuple[DefinicionEvento, ...],
) -> ModificadoresPuerta:
    """Puerta sin preguntas; admite botines de entrada y/o de salida."""
    etiquetas = [pausa.nombre, *(r.nombre for r in recompensas)]
    eventos_ids = (pausa.id, *(r.id for r in recompensas))
    delta = sum(r.modificadores.delta_vidas_al_completar for r in recompensas)
    delta_max = sum(r.modificadores.delta_vidas_max_al_completar for r in recompensas)
    return ModificadoresPuerta(
        sin_pregunta=True,
        delta_vidas_al_completar=delta,
        delta_vidas_max_al_completar=delta_max,
        rasgos=tuple(etiquetas),
        eventos_ids=eventos_ids,
    )


def _aplicar_tiempo_a_modificadores(
    ev: DefinicionEvento,
    *,
    numero_sala: int | None,
    tiempo_preg: int | None,
    tiempo_puerta: int | None,
) -> tuple[int | None, int | None]:
    if ev.id not in RASGOS_TIEMPO:
        m = ev.modificadores
        return (
            _fusionar_tiempo(tiempo_preg, m.tiempo_pregunta_seg),
            _fusionar_tiempo(tiempo_puerta, m.tiempo_puerta_seg),
        )
    sala = numero_sala if numero_sala is not None else _SALA_REF_TIEMPO[ev.id]
    p = params_tiempo_escape(ev.id, sala)
    return (
        _fusionar_tiempo(tiempo_preg, p.tiempo_pregunta_seg),
        _fusionar_tiempo(tiempo_puerta, p.tiempo_puerta_seg),
    )


def _aplicar_niebla_a_modificadores(
    ev: DefinicionEvento,
    *,
    numero_sala: int | None,
    opciones: int,
) -> int:
    if ev.id not in RASGOS_NIEBLA:
        m = ev.modificadores
        return max(opciones, m.opciones_ocultas)
    sala = numero_sala if numero_sala is not None else _SALA_REF_NIEBLA[ev.id]
    p = params_niebla_escape(ev.id, sala)
    return max(opciones, p.opciones_ocultas)


def combinar_modificadores_puerta(
    rasgos: tuple[DefinicionEvento, ...],
    *,
    numero_sala: int | None = None,
) -> ModificadoresPuerta:
    """Combina rasgos de puerta del catálogo común."""
    rasgos = _filtrar_rasgos_puerta_compatibles(rasgos)
    if not rasgos:
        return ModificadoresPuerta(rasgos=("Clásica",))
    if any(r.exclusivo_puerta_escape for r in rasgos):
        pausa = next(r for r in rasgos if r.exclusivo_puerta_escape)
        recompensas = tuple(
            r for r in rasgos if r.id in extras_escape_para_pausa(pausa.id)
        )
        return _modificadores_puerta_sin_pregunta(pausa, recompensas)

    tiempo_preg: int | None = None
    tiempo_puerta: int | None = None
    opciones = 0
    mult = 1
    delta_vidas = 0
    delta_vidas_max = 0
    etiquetas: list[str] = []

    for ev in rasgos:
        m = ev.modificadores
        tiempo_preg, tiempo_puerta = _aplicar_tiempo_a_modificadores(
            ev,
            numero_sala=numero_sala,
            tiempo_preg=tiempo_preg,
            tiempo_puerta=tiempo_puerta,
        )
        opciones = _aplicar_niebla_a_modificadores(
            ev,
            numero_sala=numero_sala,
            opciones=opciones,
        )
        mult = max(mult, m.multiplicador_puntos)
        delta_vidas += m.delta_vidas_al_completar
        delta_vidas_max += m.delta_vidas_max_al_completar
        etiquetas.append(ev.nombre)

    return ModificadoresPuerta(
        tiempo_pregunta_seg=tiempo_preg,
        tiempo_puerta_seg=tiempo_puerta,
        opciones_ocultas=opciones,
        multiplicador_puntos=mult,
        delta_vidas_al_completar=delta_vidas,
        delta_vidas_max_al_completar=delta_vidas_max,
        rasgos=tuple(etiquetas),
        eventos_ids=tuple(e.id for e in rasgos),
    )


def _modificadores_desde_evento(
    ev: DefinicionEvento,
    *,
    etiquetas: tuple[str, ...] | None = None,
) -> ModificadoresPuerta:
    m = ev.modificadores
    return ModificadoresPuerta(
        tiempo_pregunta_seg=m.tiempo_pregunta_seg,
        tiempo_puerta_seg=m.tiempo_puerta_seg,
        opciones_ocultas=m.opciones_ocultas,
        multiplicador_puntos=m.multiplicador_puntos,
        sin_pregunta=m.sin_pregunta,
        delta_vidas_al_completar=m.delta_vidas_al_completar,
        delta_vidas_max_al_completar=m.delta_vidas_max_al_completar,
        rasgos=etiquetas or (ev.nombre,),
        eventos_ids=(ev.id,),
    )


def _elegir_desafios_puerta(
    desafios: list[DefinicionEvento],
    cantidad: int,
    rng: random.Random,
) -> list[DefinicionEvento]:
    """Elige rasgos de puerta sin combinar miembros de la misma familia exclusiva."""
    if cantidad <= 0 or not desafios:
        return []
    pool = list(desafios)
    rng.shuffle(pool)
    elegidos: list[DefinicionEvento] = []
    for ev in pool:
        if len(elegidos) >= cantidad:
            break
        if _compatible_con_rasgos_puerta(ev, tuple(elegidos)):
            elegidos.append(ev)
    return elegidos


def generar_modificadores_puerta(
    *,
    numero_sala: int,
    semilla: int,
    indice_puerta: int,
    pausas_usadas: frozenset[str] = frozenset(),
    pity: PityPuertasEspecialesEscape | None = None,
    estado=None,
    vidas_max: int | None = None,
) -> ModificadoresPuerta:
    rng = random.Random(semilla + indice_puerta * 8831 + numero_sala * 97)
    pausa = _intentar_modificadores_pausa_especial(
        numero_sala=numero_sala,
        rng=rng,
        pausas_usadas=pausas_usadas,
        pity=pity,
        estado=estado,
        vidas_max=vidas_max,
    )
    if pausa is not None:
        return pausa

    disponibles = [
        e for e in eventos_puerta_escape_para_sala(numero_sala) if not e.exclusivo_puerta_escape
    ]
    recompensas = [e for e in disponibles if e.id in RASGOS_BOTIN_ESCAPE]
    desafios = [
        e for e in disponibles
        if e.id not in RASGOS_BOTIN_ESCAPE
    ]
    min_rasgos = 0
    prob_rasgo = 0.42 + min(0.45, (numero_sala - 1) * 0.012)
    if rng.random() < prob_rasgo:
        min_rasgos = 1
    if numero_sala >= 12 and rng.random() < 0.28:
        min_rasgos = max(min_rasgos, 2)

    max_rasgos = min(_MAX_RASGOS_PUERTA_COMBINADOS, len(desafios))
    if max_rasgos <= 0 and not recompensas:
        return combinar_modificadores_puerta((), numero_sala=numero_sala)
    n_extra = rng.randint(min(min_rasgos, max_rasgos), max_rasgos) if max_rasgos else 0
    elegidos = _elegir_desafios_puerta(desafios, n_extra, rng)
    if recompensas and rng.random() < _PROB_BOTIN_BASE + min(0.03, (numero_sala - 1) * 0.001):
        botin = elegir_botin_para_sala(numero_sala, rng)
        if botin is not None:
            elegidos.append(botin)
    return combinar_modificadores_puerta(tuple(elegidos), numero_sala=numero_sala)


def grupos_del_pool(pool: list[Pregunta]) -> tuple[str, ...]:
    return tuple(sorted({p.grupo for p in pool if p.grupo}))


def instanciar_evento_contenido(
    plantilla: DefinicionEvento,
    *,
    materias_pool: tuple[str, ...],
    grupos_pool: tuple[str, ...],
    semilla: int,
    indice_puerta: int,
    materia_preferida: str | None = None,
    perfil_id: str | None = None,
) -> EventoContenidoInstanciado:
    if plantilla.rol_escape != RolEscape.CONTENIDO:
        raise ValueError(f"El evento {plantilla.id!r} no es de contenido escape.")
    opts = plantilla.contenido_escape or OpcionesContenidoEscape()
    rng = random.Random(semilla + indice_puerta * 4177)
    materia: str | None = None
    grupo: str | None = None

    if opts.usa_grupo and grupos_pool:
        grupo = rng.choice(grupos_pool)
    elif opts.usa_materia and materias_pool:
        if materia_preferida and materia_preferida in materias_pool:
            materia = materia_preferida
        else:
            materia = materias_pool[indice_puerta % len(materias_pool)]

    return EventoContenidoInstanciado(
        definicion=plantilla,
        materia=materia,
        grupo=grupo,
        perfil_id=perfil_id,
    )


def linea_recompensa_pie_carta(texto: str, *, emoji: str = "") -> str:
    """Pie de carta de puerta; emoji opcional al inicio (recompensa concreta)."""
    if emoji:
        return f"{emoji} Recompensa: {texto}"
    return f"Recompensa: {texto}"


def _emoji_recompensa_botin_carta(m: ModificadoresDesafio) -> str:
    """Emoji del premio concreto (arriba en la carta va siempre 🎁)."""
    if m.powerup_al_completar:
        from Comun.objetos_partida import BONIFICACIONES, emoji_powerup

        pid = m.powerup_al_completar
        if pid in BONIFICACIONES:
            return BONIFICACIONES[pid][2]
        return emoji_powerup(pid)
    if m.delta_vidas_max_al_completar > 0:
        return EMOJI_RECOMPENSA_VIDA_MAX
    if m.delta_vidas_al_completar > 0:
        return EMOJI_RECOMPENSA_VIDA
    return EMOJI_BOTIN_ESCAPE


def _linea_recompensa_botin_carta(
    evento_id: str,
    *,
    vidas_max_tope: int,
    vidas_max_absoluto: int,
    sin_pregunta: bool = False,
) -> str:
    """Línea breve para el pie de la carta (+ cantidad, emoji del premio)."""
    m = evento_por_id(evento_id).modificadores
    emoji = _emoji_recompensa_botin_carta(m)
    if m.powerup_al_completar:
        from Comun.resistencia_motor import etiqueta_powerup

        nom = etiqueta_powerup(m.powerup_al_completar)
        if sin_pregunta:
            return linea_recompensa_pie_carta(nom, emoji=emoji)
        return linea_recompensa_pie_carta(f"{nom} al superar", emoji=emoji)
    if m.delta_vidas_max_al_completar > 0:
        n = m.delta_vidas_max_al_completar
        txt = "1" if n == 1 else str(n)
        return linea_recompensa_pie_carta(
            f"+{txt} al máximo (hasta {vidas_max_absoluto})",
            emoji=emoji,
        )
    if m.delta_vidas_al_completar > 0:
        n = m.delta_vidas_al_completar
        txt = "1 vida" if n == 1 else f"{n} vidas"
        if sin_pregunta:
            return linea_recompensa_pie_carta(
                f"+{txt} (tope {vidas_max_tope})", emoji=emoji
            )
        return linea_recompensa_pie_carta(
            f"+{txt} al superar (tope {vidas_max_tope})", emoji=emoji
        )
    return ""


def lineas_botin_puerta(
    modificadores: ModificadoresPuerta,
    *,
    vidas_max_tope: int | None = None,
    vidas_max_absoluto: int = 9,
    sin_pregunta: bool | None = None,
) -> tuple[str, ...]:
    """Líneas de recompensa botín para el pie de la carta."""
    tope = vidas_max_tope if vidas_max_tope is not None else 3
    es_descanso = modificadores.sin_pregunta if sin_pregunta is None else sin_pregunta
    lineas: list[str] = []
    for eid in modificadores.eventos_ids:
        if eid not in RASGOS_BOTIN_ESCAPE:
            continue
        linea = _linea_recompensa_botin_carta(
            eid,
            vidas_max_tope=tope,
            vidas_max_absoluto=vidas_max_absoluto,
            sin_pregunta=es_descanso,
        )
        if linea:
            lineas.append(linea)
    return tuple(lineas)


def _iconos_botin_puerta(modificadores: ModificadoresPuerta) -> tuple[IconoEfectoPuerta, ...]:
    tooltip = (
        TOOLTIP_BOTIN_DESCANSO
        if modificadores.sin_pregunta
        else TOOLTIP_BOTIN
    )
    iconos: list[IconoEfectoPuerta] = []
    for eid in modificadores.eventos_ids:
        if eid not in RASGOS_BOTIN_ESCAPE:
            continue
        ev = evento_por_id(eid)
        m = ev.modificadores
        if m.powerup_al_completar:
            iconos.append(
                IconoEfectoPuerta(
                    emoji=EMOJI_BOTIN_ESCAPE,
                    tooltip=ev.descripcion,
                    capa=CapaIconoEscape.BOTIN,
                )
            )
            continue
        if m.delta_vidas_al_completar <= 0 and m.delta_vidas_max_al_completar <= 0:
            continue
        iconos.append(
            IconoEfectoPuerta(
                emoji=EMOJI_BOTIN_ESCAPE,
                tooltip=tooltip,
                capa=CapaIconoEscape.BOTIN,
            )
        )
    return tuple(iconos)


def _icono_jefe_puerta(delta_jefe: int) -> IconoEfectoPuerta | None:
    if delta_jefe <= 0:
        return None
    txt = "1 vida" if delta_jefe == 1 else f"{delta_jefe} vidas"
    return IconoEfectoPuerta(
        emoji=EMOJI_JEFE,
        tooltip=(
            "Puerta jefe: bloque largo solo con preguntas difíciles. "
            f"Al superarla sin fallar: +{txt} (tope actual de vidas)."
        ),
        capa=CapaIconoEscape.JEFE,
    )


def texto_modificadores_puerta(
    modificadores: ModificadoresPuerta,
    *,
    n_preguntas: int,
) -> str:
    lineas: list[str] = []
    if modificadores.sin_pregunta:
        ev = evento_sin_pregunta_escape(modificadores)
        if ev is not None:
            lineas.append(f"{ev.emoji} {ev.nombre} — {ev.descripcion}")
        else:
            lineas.append(f"{EMOJI_DESCANSO} Sin preguntas en esta puerta.")
        lineas.extend(lineas_botin_puerta(modificadores))
        return "\n".join(lineas)
    lineas.extend(lineas_botin_puerta(modificadores))
    lineas.append(linea_bloque_preguntas_puerta(n_preguntas))
    if modificadores.rasgos:
        lineas.append(" · ".join(modificadores.rasgos))
    if modificadores.tiempo_puerta_seg:
        lineas.append(f"Tiempo de puerta: {modificadores.tiempo_puerta_seg} s")
    if modificadores.tiempo_pregunta_seg:
        lineas.append(f"Tiempo por pregunta: {modificadores.tiempo_pregunta_seg} s")
    if modificadores.opciones_ocultas:
        lineas.append(f"{modificadores.opciones_ocultas} opción(es) oculta(s)")
    if modificadores.multiplicador_puntos > 1:
        lineas.append(f"×{modificadores.multiplicador_puntos} puntos")
    return "\n".join(lineas)


def texto_evento_contenido(evento: EventoContenidoInstanciado) -> str:
    from Comun.config_historia import etiqueta_grupo_tematico

    lineas = [f"{evento.emoji} {evento.nombre}", evento.descripcion]
    if evento.materia:
        lineas.append(f"Materia: {evento.materia}")
    if evento.grupo:
        lineas.append(etiqueta_grupo_tematico(evento.grupo))
    return "\n".join(lineas)


def emoji_tipo_puerta_escape(evento: EventoContenidoInstanciado) -> str:
    """Icono de la capa «tipo de puerta» (materia o grupo)."""
    opts = evento.contenido_escape
    if opts and opts.usa_grupo:
        return EMOJI_PUERTA_GRUPO
    return EMOJI_PUERTA_MATERIA


def _icono_capa_dificultad_contenido(
    evento: EventoContenidoInstanciado,
) -> IconoEfectoPuerta | None:
    """Capa dificultad: un icono si el perfil filtra dificultad (materia o grupo)."""
    capa = CapaIconoEscape.DIFICULTAD
    perfil = evento.perfil_id
    if perfil in _IDS_PERFIL_MIX_MATERIA:
        return IconoEfectoPuerta(EMOJI_MIX_MATERIA, TOOLTIP_MIX_MATERIA, capa)
    if perfil == "facil":
        return IconoEfectoPuerta(EMOJI_DIF_FACIL, TOOLTIP_DIF_FACIL, capa)
    if perfil == "media":
        return IconoEfectoPuerta(EMOJI_DIF_MEDIA, TOOLTIP_DIF_MEDIA, capa)
    if perfil == "dificil":
        return IconoEfectoPuerta(EMOJI_DIF_DIFICIL, TOOLTIP_DIF_DIFICIL, capa)
    difs = evento.dificultades_permitidas
    if difs and len(difs) == 1:
        d = next(iter(difs))
        if d == "Facil":
            return IconoEfectoPuerta(EMOJI_DIF_FACIL, TOOLTIP_DIF_FACIL, capa)
        if d == "Media":
            return IconoEfectoPuerta(EMOJI_DIF_MEDIA, TOOLTIP_DIF_MEDIA, capa)
        if d == "Dificil":
            return IconoEfectoPuerta(EMOJI_DIF_DIFICIL, TOOLTIP_DIF_DIFICIL, capa)
    return IconoEfectoPuerta(EMOJI_DIF_BALANCEADO, TOOLTIP_DIF_BALANCEADO, capa)


def _icono_capa_tipo_pregunta(
    evento: EventoContenidoInstanciado,
) -> IconoEfectoPuerta | None:
    """Capa tipo de pregunta (🔤 teoría, 🔢 cálculo); solo si el perfil filtra tipo."""
    capa = CapaIconoEscape.TIPO_PREGUNTA
    perfil = evento.perfil_id
    if perfil == "teoria":
        return IconoEfectoPuerta(EMOJI_TIPO_TEORIA, TOOLTIP_TIPO_TEORIA, capa)
    if perfil == "calculo":
        return IconoEfectoPuerta(EMOJI_TIPO_CALCULO, TOOLTIP_TIPO_CALCULO, capa)
    tipos = evento.tipos_permitidos
    if tipos == frozenset({"Teoria"}):
        return IconoEfectoPuerta(EMOJI_TIPO_TEORIA, TOOLTIP_TIPO_TEORIA, capa)
    if tipos == frozenset({"Calculo"}):
        return IconoEfectoPuerta(EMOJI_TIPO_CALCULO, TOOLTIP_TIPO_CALCULO, capa)
    return None


def iconos_contenido_puerta(evento: EventoContenidoInstanciado) -> tuple[IconoEfectoPuerta, ...]:
    """Capas de contenido: tipo de puerta + dificultad + tipo de pregunta (tooltips fijos)."""
    opts = evento.contenido_escape
    iconos: list[IconoEfectoPuerta] = []
    if opts and opts.usa_grupo:
        iconos.append(
            IconoEfectoPuerta(
                EMOJI_PUERTA_GRUPO,
                TOOLTIP_PUERTA_GRUPO,
                CapaIconoEscape.TIPO_PUERTA,
            )
        )
    else:
        iconos.append(
            IconoEfectoPuerta(
                EMOJI_PUERTA_MATERIA,
                TOOLTIP_PUERTA_MATERIA,
                CapaIconoEscape.TIPO_PUERTA,
            )
        )
    dif = _icono_capa_dificultad_contenido(evento)
    if dif is not None:
        iconos.append(dif)
    tipo = _icono_capa_tipo_pregunta(evento)
    if tipo is not None:
        iconos.append(tipo)
    return tuple(iconos)


def tooltip_efecto_rasgo_puerta(
    evento_id: str,
    *,
    modificadores: ModificadoresPuerta | None = None,
) -> str:
    """Ayuda breve del icono: solo mecánica de juego, sin nombre ni descripción del catálogo."""
    ev = evento_por_id(evento_id)
    m = ev.modificadores
    partes: list[str] = []
    if m.sin_pregunta:
        if evento_id == "tienda":
            return TOOLTIP_TIENDA
        partes.append("Sin preguntas en esta puerta.")
        if m.delta_vidas_al_completar:
            partes.append(f"Recuperas {m.delta_vidas_al_completar} vida.")
        return " ".join(partes)
    if evento_id in RASGOS_TIEMPO_PUERTA_ESCAPE and modificadores is not None:
        if evento_id in {"cronometro_bloque", "cronometro_doble"} and modificadores.tiempo_puerta_seg:
            partes.append(f"{modificadores.tiempo_puerta_seg} s para toda la puerta.")
        if evento_id in {"cronometro_pregunta", "cronometro_doble"} and modificadores.tiempo_pregunta_seg:
            partes.append(f"{modificadores.tiempo_pregunta_seg} s por pregunta.")
    else:
        if m.tiempo_puerta_seg is not None:
            partes.append(f"{m.tiempo_puerta_seg} s para toda la puerta.")
        if m.tiempo_pregunta_seg is not None:
            partes.append(f"{m.tiempo_pregunta_seg} s por pregunta.")
    if evento_id in RASGOS_NIEBLA and modificadores is not None:
        if modificadores.opciones_ocultas:
            partes.append("1 respuesta oculta al azar.")
    else:
        if m.opciones_ocultas:
            partes.append("1 respuesta oculta al azar.")
    if m.multiplicador_puntos > 1:
        partes.append(
            f"×{m.multiplicador_puntos} puntos en cada acierto de esta puerta."
        )
    return " ".join(partes) if partes else ev.descripcion


def linea_bloque_preguntas_puerta(n_preguntas: int) -> str:
    if n_preguntas == 1:
        return "1 pregunta en esta puerta."
    return f"{n_preguntas} preguntas seguidas en esta puerta."


def tooltip_recompensa_completar(
    bonus,
    *,
    es_jefe: bool = False,
) -> str:
    """Ayuda del icono de recompensa al superar la puerta."""
    if bonus.delta_vidas <= 0:
        return ""
    if es_jefe:
        n = bonus.delta_vidas
        txt = "1 vida" if n == 1 else f"{n} vidas"
        return (
            "Puerta jefe: bloque largo solo con preguntas difíciles. "
            f"Al superarla sin fallar: +{txt} (tope actual de vidas)."
        )
    n = bonus.delta_vidas
    txt = "1 vida" if n == 1 else f"{n} vidas"
    return f"Al superar la puerta sin fallar: +{txt} (tope actual de vidas)."


def ids_pool_resistencia_aleatorio() -> tuple[str, ...]:
    return ("relampago", "opciones_ocultas", "doble")


def ids_eventos_buenos_resistencia() -> tuple[str, ...]:
    return ("doble",)


def ids_eventos_malos_resistencia() -> tuple[str, ...]:
    return ("relampago", "opciones_ocultas")


_NIEBLA_MALOS_RESISTENCIA = frozenset({"opciones_ocultas"})

FAMILIA_MALO_RESISTENCIA: dict[str, str] = {
    "relampago": "tiempo",
    "opciones_ocultas": "niebla",
}


def familia_malo_resistencia(kind: str) -> str | None:
    if kind in FAMILIA_MALO_RESISTENCIA:
        return FAMILIA_MALO_RESISTENCIA[kind]
    clave = _ALIAS_RESISTENCIA.get(kind, kind)
    return FAMILIA_MALO_RESISTENCIA.get(clave)


def malos_resistencia_vigentes(
    numero_pregunta: int,
    *,
    tiempo_baseline: int | None,
    opciones_baseline: int,
) -> tuple[str, ...]:
    """Malos aleatorios que aún aportan algo respecto a la escalada base."""
    tiene_opc = opciones_baseline > 0
    vigentes: list[str] = []
    for kind in ids_eventos_malos_resistencia_para(numero_pregunta):
        if kind == "relampago" and tiempo_baseline is not None:
            continue
        if kind == "opciones_ocultas" and tiene_opc:
            continue
        vigentes.append(kind)
    return tuple(vigentes)


def elegir_malos_resistencia_exclusivos(
    kinds: tuple[str, ...] | list[str],
    cantidad: int,
    rng: random.Random,
    *,
    pesos: dict[str, float] | None = None,
) -> tuple[str, ...]:
    """Como en escape: a lo sumo un evento de tiempo y uno de niebla por pregunta."""
    if cantidad <= 0 or not kinds:
        return ()
    pool = list(kinds)
    if pesos:
        pool.sort(
            key=lambda k: pesos.get(k, 1.0) * (0.25 + rng.random()),
            reverse=True,
        )
    else:
        rng.shuffle(pool)
    elegidos: list[str] = []
    familias: set[str] = set()
    for kind in pool:
        if len(elegidos) >= cantidad:
            break
        familia = familia_malo_resistencia(kind)
        if familia is not None and familia in familias:
            continue
        elegidos.append(kind)
        if familia is not None:
            familias.add(familia)
    return tuple(elegidos)


def niebla_disponible_resistencia(numero_pregunta: int) -> bool:
    return numero_pregunta >= PREGUNTA_MIN_NIEBLA_RESISTENCIA


def ids_eventos_malos_resistencia_para(numero_pregunta: int) -> tuple[str, ...]:
    todos = ids_eventos_malos_resistencia()
    if niebla_disponible_resistencia(numero_pregunta):
        return todos
    return tuple(k for k in todos if k not in _NIEBLA_MALOS_RESISTENCIA)


def evento_resistencia_aleatorio(
    kind: str,
    intensidad: float,
    *,
    numero_pregunta: int = PREGUNTA_MIN_NIEBLA_RESISTENCIA,
) -> EventoAleatorioResistencia:
    from Comun.resistencia_partida import EventoAleatorioResistencia

    clave = _ALIAS_RESISTENCIA.get(kind, kind)
    base = evento_por_id(clave)
    mod = base.modificadores

    tiempo = None
    if clave in RASGOS_TIEMPO:
        tiempo = params_tiempo_resistencia(clave, numero_pregunta, intensidad).tiempo_pregunta_seg
    opciones_ocultas = 0
    if clave in RASGOS_NIEBLA:
        opciones_ocultas = params_niebla_resistencia(
            clave, numero_pregunta, intensidad
        ).opciones_ocultas
    mult = mod.multiplicador_puntos
    if clave == "doble_puntos":
        mult = 2 if intensidad < 0.75 else 3

    etiqueta = base.nombre
    if clave == "relampago" and tiempo is not None:
        etiqueta = f"Relámpago: {tiempo} s por pregunta"
    elif clave == "niebla_opciones":
        etiqueta = "Niebla: 1 respuesta oculta"
    elif clave == "doble_puntos":
        etiqueta = "Doble puntos" if mult == 2 else "Triple puntos"

    return EventoAleatorioResistencia(
        etiqueta=etiqueta,
        tiempo_pregunta=tiempo,
        multiplicador_puntos=mult if mult > 1 else None,
        opciones_ocultas=opciones_ocultas or None,
    )


def emoji_evento_id(evento_id: str) -> str:
    return evento_por_id(evento_id).emoji


def descripcion_evento_id(evento_id: str) -> str:
    ev = evento_por_id(evento_id)
    return f"{ev.nombre}: {ev.descripcion}"


def _capa_rasgo_puerta(evento_id: str) -> CapaIconoEscape:
    capa = capa_evento_escape(evento_id)
    if capa is not None:
        return capa
    return CapaIconoEscape.TIEMPO


_PRIORIDAD_RECORTE_ICONO: dict[CapaIconoEscape, int] = {
    CapaIconoEscape.TIPO_PREGUNTA: 0,
    CapaIconoEscape.PUNTOS: 1,
    CapaIconoEscape.NIEBLA: 2,
    CapaIconoEscape.TIEMPO: 3,
    CapaIconoEscape.JEFE: 4,
}


def acotar_iconos_carta_puerta(
    iconos: list[IconoEfectoPuerta],
    *,
    semilla: int = 0,
    max_iconos: int = MAX_ICONOS_CARTA_PUERTA,
) -> tuple[IconoEfectoPuerta, ...]:
    """Recorta al límite quitando primero iconos opcionales de menor prioridad."""
    if len(iconos) <= max_iconos:
        return tuple(iconos)

    rng = random.Random(semilla)
    opcionales = [
        (i, ic)
        for i, ic in enumerate(iconos)
        if ic.capa not in CAPAS_ICONO_PROTEGIDO_ESCAPE
    ]
    quitar_n = len(iconos) - max_iconos
    opcionales.sort(
        key=lambda par: (
            _PRIORIDAD_RECORTE_ICONO.get(par[1].capa, 99),
            rng.random(),
        )
    )
    eliminar = {i for i, _ in opcionales[: min(quitar_n, len(opcionales))]}
    return tuple(ic for i, ic in enumerate(iconos) if i not in eliminar)


def iconos_efecto_puerta(
    *,
    evento: EventoContenidoInstanciado,
    modificadores: ModificadoresPuerta,
    n_preguntas: int,
    delta_jefe: int = 0,
    semilla: int = 0,
) -> tuple[IconoEfectoPuerta, ...]:
    """Rasgos → jefe → contenido → botín; como máximo ``MAX_ICONOS_CARTA_PUERTA``."""
    iconos: list[IconoEfectoPuerta] = []

    for eid in modificadores.eventos_ids:
        if eid in _RASGOS_SOLO_RECOMPENSA:
            continue
        ev = evento_por_id(eid)
        iconos.append(
            IconoEfectoPuerta(
                emoji=ev.emoji,
                tooltip=tooltip_efecto_rasgo_puerta(eid, modificadores=modificadores),
                capa=_capa_rasgo_puerta(eid),
            )
        )

    jefe = _icono_jefe_puerta(delta_jefe)
    if jefe is not None:
        iconos.append(jefe)

    if not modificadores.sin_pregunta and n_preguntas > 0:
        iconos.extend(iconos_contenido_puerta(evento))

    iconos.extend(_iconos_botin_puerta(modificadores))

    return acotar_iconos_carta_puerta(iconos, semilla=semilla)


# --- Eventos sí/no (resistencia) ---


@dataclass(frozen=True)
class RecompensaApuesta:
    mult_puntos: int = 1
    delta_vidas: int = 0
    powerup_id: str | None = None
    cantidad_powerup: int = 1
    powerup_aleatorio: bool = False


@dataclass(frozen=True)
class CosteApuesta:
    """Penalización si fallas la pregunta con riesgo activo."""

    vidas_fallo: int = 1
    puntos_perdidos: int = 0
    pierde_powerup_aleatorio: bool = False
    pierde_todos_objetos: bool = False
    fin_partida: bool = False


@dataclass(frozen=True)
class ApuestaRiesgo:
    etiqueta: str
    recompensa: RecompensaApuesta
    coste: CosteApuesta


APUESTAS_DISPONIBLES: tuple[ApuestaRiesgo, ...] = (
    ApuestaRiesgo(
        "Doble o nada",
        RecompensaApuesta(mult_puntos=2),
        CosteApuesta(vidas_fallo=2),
    ),
    ApuestaRiesgo(
        "Triple arriesgado",
        RecompensaApuesta(mult_puntos=3),
        CosteApuesta(vidas_fallo=2),
    ),
    ApuestaRiesgo(
        "Cuádruple audaz",
        RecompensaApuesta(mult_puntos=4),
        CosteApuesta(vidas_fallo=3),
    ),
    ApuestaRiesgo(
        "Todo o nada",
        RecompensaApuesta(mult_puntos=5),
        CosteApuesta(vidas_fallo=3),
    ),
    ApuestaRiesgo(
        "Botín seguro",
        RecompensaApuesta(powerup_aleatorio=True),
        CosteApuesta(vidas_fallo=1),
    ),
    ApuestaRiesgo(
        "Vida de la suerte",
        RecompensaApuesta(delta_vidas=1),
        CosteApuesta(puntos_perdidos=35),
    ),
    ApuestaRiesgo(
        "Cofre arriesgado",
        RecompensaApuesta(mult_puntos=2, powerup_aleatorio=True),
        CosteApuesta(pierde_powerup_aleatorio=True),
    ),
    ApuestaRiesgo(
        "Escudo de oro",
        RecompensaApuesta(powerup_id="escudo"),
        CosteApuesta(vidas_fallo=2, puntos_perdidos=20),
    ),
    ApuestaRiesgo(
        "Impulso doble",
        RecompensaApuesta(mult_puntos=2, delta_vidas=1),
        CosteApuesta(pierde_powerup_aleatorio=True, vidas_fallo=1),
    ),
    ApuestaRiesgo(
        "Ruleta roja",
        RecompensaApuesta(mult_puntos=3),
        CosteApuesta(pierde_todos_objetos=True, vidas_fallo=1),
    ),
    ApuestaRiesgo(
        "Última carta",
        RecompensaApuesta(mult_puntos=4),
        CosteApuesta(fin_partida=True),
    ),
    ApuestaRiesgo(
        "Riesgo mortal",
        RecompensaApuesta(mult_puntos=3, powerup_aleatorio=True),
        CosteApuesta(fin_partida=True),
    ),
)

TipoEventoSiNo = Literal[
    "riesgo_pregunta",
    "compra",
    "vida",
    "amuleto",
    "sorpresa",
    "purga_maldicion",
]

PREGUNTA_MIN_EVENTO_SI_NO = 6
PREGUNTA_MIN_RIESGO_PREGUNTA = 8
FACTOR_PROB_EVENTO_SI_NO = 0.34
PITY_INC_EVENTO_SI_NO = 0.03
PITY_MAX_BOOST_EVENTO_SI_NO = 0.28

def _economia():
    from Comun import economia_partida as economia

    return economia


def _objetos():
    from Comun import objetos_partida as objetos

    return objetos

_PESO_TIPO_EVENTO: dict[TipoEventoSiNo, float] = {
    "riesgo_pregunta": 1.15,
    "compra": 1.0,
    "vida": 0.55,
    "amuleto": 0.55,
    "sorpresa": 0.55,
    "purga_maldicion": 1.2,
}


@dataclass(frozen=True)
class EventoSiNo:
    """Variante concreta de un evento sí/no (riesgo en pregunta o gasto en pts)."""

    tipo: TipoEventoSiNo
    titulo: str
    descripcion_si: str
    precio: int = 0
    riesgo: ApuestaRiesgo | None = None
    articulo_id: str | None = None

    @property
    def requiere_puntos(self) -> bool:
        return self.precio > 0

    @property
    def es_riesgo_en_pregunta(self) -> bool:
        return self.riesgo is not None


def _motor_resistencia():
    from Comun import resistencia_motor as motor

    return motor


def _riesgo_pregunta_score(riesgo: ApuestaRiesgo) -> float:
    r = riesgo.recompensa
    c = riesgo.coste
    score = (c.vidas_fallo - 1) * 1.25
    score += c.puntos_perdidos / 30.0
    if c.pierde_powerup_aleatorio:
        score += 1.0
    if c.pierde_todos_objetos:
        score += 2.0
    if c.fin_partida:
        score += 5.0
    score -= (r.mult_puntos - 1) * 0.35
    score -= r.delta_vidas * 0.9
    if r.powerup_id or r.powerup_aleatorio:
        score -= 0.7
    return max(0.4, score)


def elegir_riesgo_pregunta(rng: random.Random, numero_pregunta: int) -> ApuestaRiesgo:
    """Elige un perfil de riesgo; al avanzar la partida pesan más los arriesgados."""
    motor = _motor_resistencia()
    t = motor.factor_progreso_resistencia(numero_pregunta)
    centro = 1.0 + t * 4.5
    pesos = [
        1.0 / (0.6 + abs(_riesgo_pregunta_score(ap) - centro))
        for ap in APUESTAS_DISPONIBLES
    ]
    return rng.choices(APUESTAS_DISPONIBLES, weights=pesos, k=1)[0]


def texto_recompensa_riesgo_pregunta(recompensa: RecompensaApuesta) -> str:
    motor = _motor_resistencia()
    partes: list[str] = []
    if recompensa.mult_puntos > 1:
        partes.append(f"×{recompensa.mult_puntos} puntos")
    if recompensa.delta_vidas > 0:
        n = recompensa.delta_vidas
        partes.append(f"+{n} vida" + ("s" if n > 1 else ""))
    if recompensa.powerup_id:
        nom = motor.etiqueta_powerup(recompensa.powerup_id)
        if recompensa.cantidad_powerup > 1:
            partes.append(f"{recompensa.cantidad_powerup}× {nom}")
        else:
            partes.append(f"objeto {nom}")
    elif recompensa.powerup_aleatorio:
        partes.append("un objeto al azar")
    return ", ".join(partes) if partes else "sin bonus extra"


def texto_coste_riesgo_pregunta(coste: CosteApuesta) -> str:
    if coste.fin_partida:
        return "la partida termina al instante"
    partes: list[str] = []
    vida_txt: str | None = None
    if coste.vidas_fallo > 1:
        vida_txt = f"pierdes {coste.vidas_fallo} vidas"
    elif coste.vidas_fallo == 1:
        vida_txt = "pierdes 1 vida"
    if coste.pierde_todos_objetos:
        if vida_txt:
            partes.append(f"{vida_txt} y todos tus objetos")
        else:
            partes.append("pierdes todos tus objetos")
    elif vida_txt:
        partes.append(vida_txt)
    if coste.puntos_perdidos > 0:
        partes.append(f"−{coste.puntos_perdidos} puntos")
    if coste.pierde_powerup_aleatorio:
        partes.append("pierdes un objeto al azar")
    return "; ".join(partes)


def formatear_aviso_apuesta(riesgo: ApuestaRiesgo) -> str:
    recomp = texto_recompensa_riesgo_pregunta(riesgo.recompensa)
    coste = texto_coste_riesgo_pregunta(riesgo.coste)
    texto = f"{riesgo.etiqueta}: si aciertas, {recomp}; si fallas, {coste}."
    return _motor_resistencia().prefijar_emoji(texto, "🎰")


def _emoji_evento_si_no(evento: EventoSiNo) -> str:
    from Comun.emojis_partida import emoji_evento_si_no

    return emoji_evento_si_no(evento)


def _acortar_frase_riesgo(texto: str) -> str:
    limpio = texto.strip()
    sustituciones = {
        "un objeto al azar": "objeto",
        "pierdes 1 vida": "1 vida",
        "pierdes 1 vida y todos tus objetos": "1 vida y todos tus objetos",
        "pierdes un objeto al azar": "1 objeto",
        "pierdes todos tus objetos": "todos tus objetos",
    }
    return sustituciones.get(limpio, limpio)


def _resumen_efecto_evento_si_no(evento: EventoSiNo) -> str:
    if evento.es_riesgo_en_pregunta:
        descripcion = evento.descripcion_si
        if "; si fallas, " in descripcion:
            ok, fallo = descripcion.removeprefix("si aciertas, ").split("; si fallas, ", 1)
            from Comun.emojis_partida import EMOJI_RIESGO_ACIERTO, EMOJI_RIESGO_FALLO

            return (
                f"{EMOJI_RIESGO_ACIERTO} {_acortar_frase_riesgo(ok)} · "
                f"{EMOJI_RIESGO_FALLO} {_acortar_frase_riesgo(fallo)}"
            )
        return descripcion
    resumenes: dict[TipoEventoSiNo, str] = {
        "vida": "+1 vida",
        "amuleto": "+20 pts en próximo acierto",
        "sorpresa": "objeto al azar",
        "purga_maldicion": "quitar maldición",
    }
    if evento.tipo == "compra":
        return evento.titulo.lower()
    return resumenes.get(evento.tipo, evento.descripcion_si)


def titulo_popup_evento_si_no(evento: EventoSiNo) -> str:
    """Nombre concreto del evento (p. ej. «Amuleto arcade»), no «Oferta» genérico."""
    return evento.titulo


def formatear_aviso_evento_si_no(evento: EventoSiNo) -> str:
    motor = _motor_resistencia()
    resumen = _resumen_efecto_evento_si_no(evento)
    if evento.requiere_puntos:
        cuerpo = f"{evento.precio} pts — {resumen}"
    else:
        cuerpo = resumen
    return motor.prefijar_emoji(cuerpo, _emoji_evento_si_no(evento))


def _nivel_tienda_resistencia(numero_pregunta: int) -> int:
    return _economia().nivel_tienda_resistencia(numero_pregunta)


def _articulo_comprable_resistencia(
    art: ArticuloTienda,
    *,
    numero_pregunta: int,
    estado: EstadoPartida,
    er: EstadoResistencia,
) -> bool:
    return _economia().articulo_comprable_resistencia(
        art,
        numero_pregunta=numero_pregunta,
        estado=estado,
        vidas_max=er.vidas_max,
    )


def _elegir_articulo_compra(
    rng: random.Random,
    numero_pregunta: int,
    er: EstadoResistencia,
    estado: EstadoPartida,
) -> ArticuloTienda | None:
    return _economia().elegir_articulo_compra_resistencia(
        rng,
        numero_pregunta,
        estado,
        vidas_max=er.vidas_max,
    )


def _evento_riesgo_pregunta(
    numero_pregunta: int,
    er: EstadoResistencia,
) -> EventoSiNo | None:
    if numero_pregunta < PREGUNTA_MIN_RIESGO_PREGUNTA:
        return None
    if er.maldicion is not None:
        return None
    motor = _motor_resistencia()
    rng = motor.rng_partida(er, numero_pregunta * 53 + 4049)
    riesgo = elegir_riesgo_pregunta(rng, numero_pregunta)
    recomp = texto_recompensa_riesgo_pregunta(riesgo.recompensa)
    coste = texto_coste_riesgo_pregunta(riesgo.coste)
    return EventoSiNo(
        tipo="riesgo_pregunta",
        titulo=riesgo.etiqueta,
        descripcion_si=f"si aciertas, {recomp}; si fallas, {coste}",
        precio=0,
        riesgo=riesgo,
    )


def _evento_compra(
    rng: random.Random,
    numero_pregunta: int,
    er: EstadoResistencia,
    estado: EstadoPartida,
) -> EventoSiNo | None:
    art = _elegir_articulo_compra(rng, numero_pregunta, er, estado)
    if art is None:
        return None
    return EventoSiNo(
        tipo="compra",
        titulo=art.nombre,
        descripcion_si=f"compras {art.nombre.lower()}",
        precio=_economia().precio_resistencia_articulo(art.id, numero_pregunta),
        articulo_id=art.id,
    )


def _candidatos_evento_si_no(
    numero_pregunta: int,
    er: EstadoResistencia,
    estado: EstadoPartida,
) -> list[EventoSiNo]:
    motor = _motor_resistencia()
    rng = motor.rng_partida(er, numero_pregunta * 53 + 4049)
    candidatos: list[EventoSiNo] = []

    if er.apuesta_activa is None:
        evento_riesgo = _evento_riesgo_pregunta(numero_pregunta, er)
        if evento_riesgo is not None:
            candidatos.append(evento_riesgo)

    compra = _evento_compra(rng, numero_pregunta, er, estado)
    if compra is not None:
        candidatos.append(compra)

    vidas = estado.vidas_restantes
    if (
        vidas is not None
        and vidas < er.vidas_max
        and numero_pregunta >= PREGUNTA_MIN_EVENTO_SI_NO
    ):
        candidatos.append(
            EventoSiNo(
                tipo="vida",
                titulo="Refuerzo vital",
                descripcion_si="+1 vida",
                precio=_economia().precio_resistencia_oferta(
                    numero_pregunta, tipo="vida"
                ),
            )
        )

    if numero_pregunta >= PREGUNTA_MIN_EVENTO_SI_NO:
        candidatos.append(
            EventoSiNo(
                tipo="amuleto",
                titulo="Amuleto arcade",
                descripcion_si="+20 pts en próximo acierto",
                precio=_economia().precio_resistencia_oferta(
                    numero_pregunta, tipo="amuleto"
                ),
            )
        )

    if numero_pregunta >= PREGUNTA_MIN_EVENTO_SI_NO:
        candidatos.append(
            EventoSiNo(
                tipo="sorpresa",
                titulo="Caja misteriosa",
                descripcion_si="objeto al azar",
                precio=_economia().precio_resistencia_oferta(
                    numero_pregunta, tipo="sorpresa"
                ),
            )
        )

    if er.maldicion is not None:
        candidatos.append(
            EventoSiNo(
                tipo="purga_maldicion",
                titulo="Purga arcana",
                descripcion_si=f"quitar {er.maldicion.etiqueta.lower()}",
                precio=_economia().precio_resistencia_oferta(
                    numero_pregunta, tipo="purga_maldicion"
                ),
            )
        )

    if er.maldicion is not None:
        candidatos = [c for c in candidatos if c.tipo != "riesgo_pregunta"]

    return candidatos


def elegir_evento_si_no(
    numero_pregunta: int,
    er: EstadoResistencia,
    estado: EstadoPartida,
) -> EventoSiNo | None:
    """Como máximo un evento sí/no por turno."""
    if numero_pregunta < PREGUNTA_MIN_EVENTO_SI_NO:
        return None
    if er.apuesta_activa is not None:
        return None

    candidatos = _candidatos_evento_si_no(numero_pregunta, er, estado)
    if not candidatos:
        er.preguntas_sin_evento_si_no += 1
        return None

    motor = _motor_resistencia()
    rng = motor.rng_partida(er, numero_pregunta * 61 + 9127)
    prob_base = (
        motor.probabilidad_buena_resistencia(numero_pregunta) * FACTOR_PROB_EVENTO_SI_NO
    )
    boost = min(
        PITY_MAX_BOOST_EVENTO_SI_NO,
        er.preguntas_sin_evento_si_no * PITY_INC_EVENTO_SI_NO,
    )
    if rng.random() > prob_base + boost:
        er.preguntas_sin_evento_si_no += 1
        return None

    pesos = [_PESO_TIPO_EVENTO.get(c.tipo, 1.0) for c in candidatos]
    elegido = rng.choices(candidatos, weights=pesos, k=1)[0]
    er.preguntas_sin_evento_si_no = 0
    return elegido


def _aplicar_sorpresa_resistencia(
    er: EstadoResistencia,
    estado: EstadoPartida,
    *,
    numero_pregunta: int,
) -> None:
    """Caja misteriosa: powerup al inventario o bonificación instantánea aplicable."""
    economia = _economia()
    objetos = _objetos()
    motor = _motor_resistencia()
    rng = motor.rng_partida(er, numero_pregunta * 19 + 7701)
    bonifs = [
        bid
        for bid in objetos.IDS_BONIFICACION
        if objetos.bonificacion_aplicable(
            bid, estado, vidas_max=er.vidas_max
        )
    ]
    if bonifs and rng.random() < economia.PESO_BONIFICACION / (
        economia.PESO_POWERUP + economia.PESO_BONIFICACION
    ):
        bid = rng.choice(bonifs)
        economia.efecto_compra_resistencia(
            bid, estado, er, vidas_max=er.vidas_max
        )
        return
    pid = rng.choice(motor.POWERUPS_LOOT)
    er.agregar_powerup(pid, 1)


def puede_aceptar_evento_si_no(
    evento: EventoSiNo,
    estado: EstadoPartida,
    er: EstadoResistencia,
) -> str | None:
    if evento.precio > 0 and estado.puntos_arcade < evento.precio:
        return (
            f"Necesitas {evento.precio} pts (tienes {estado.puntos_arcade})."
        )

    if evento.es_riesgo_en_pregunta:
        return None

    if evento.tipo == "compra":
        if not evento.articulo_id:
            return "Evento no válido."
        objetos = _objetos()
        if objetos.es_bonificacion(evento.articulo_id):
            if not objetos.bonificacion_aplicable(
                evento.articulo_id, estado, vidas_max=er.vidas_max
            ):
                return "Esta bonificación no aplica ahora."
        return None

    if evento.tipo == "vida":
        vidas = estado.vidas_restantes
        if vidas is None:
            return "No aplica en esta partida."
        if vidas >= er.vidas_max:
            return "Ya tienes el tope de vidas."
        return None

    if evento.tipo == "amuleto":
        return None

    if evento.tipo == "purga_maldicion":
        if er.maldicion is None:
            return "No hay maldición activa."
        return None

    if evento.tipo == "sorpresa":
        return None

    return "Evento desconocido."


def aceptar_evento_si_no(
    evento: EventoSiNo,
    estado: EstadoPartida,
    er: EstadoResistencia,
    *,
    numero_pregunta: int,
) -> str | None:
    """Aplica el evento aceptado. Devuelve mensaje de error o None."""
    err = puede_aceptar_evento_si_no(evento, estado, er)
    if err:
        return err

    if evento.precio > 0:
        estado.puntos_arcade, _ = sumar_puntos_arcade(estado.puntos_arcade, -evento.precio)

    motor = _motor_resistencia()
    if evento.es_riesgo_en_pregunta:
        er.apuesta_activa = evento.riesgo
    elif evento.tipo == "compra" and evento.articulo_id:
        err = _economia().efecto_compra_resistencia(
            evento.articulo_id,
            estado,
            er,
            vidas_max=er.vidas_max,
        )
        if err:
            return err
    elif evento.tipo == "vida":
        if estado.vidas_restantes is not None:
            estado.vidas_restantes = min(
                er.vidas_max,
                (estado.vidas_restantes or 0) + 1,
            )
    elif evento.tipo == "amuleto":
        er.bonus_proximo_acierto = 20
    elif evento.tipo == "sorpresa":
        _aplicar_sorpresa_resistencia(er, estado, numero_pregunta=numero_pregunta)
    elif evento.tipo == "purga_maldicion":
        er.maldicion = None
        er.objetos_bloqueados = False

    return None


def mensaje_exito_evento_si_no(evento: EventoSiNo) -> str | None:
    if evento.es_riesgo_en_pregunta:
        return None
    motor = _motor_resistencia()
    if evento.tipo == "compra" and evento.articulo_id:
        nom = _objetos().articulo_por_id(evento.articulo_id).nombre
        return f"Compraste {nom}."
    if evento.tipo == "vida":
        return "Refuerzo vital: +1 vida."
    if evento.tipo == "amuleto":
        return "Amuleto activado: +20 pts en tu próximo acierto."
    if evento.tipo == "sorpresa":
        return "Caja misteriosa abierta."
    if evento.tipo == "purga_maldicion":
        return "Maldición purgada."
    return None
