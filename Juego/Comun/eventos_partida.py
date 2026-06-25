#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Catálogo común de eventos/desafíos (resistencia y escape room).

En escape room cada entrada del catálogo tiene un ``rol_escape``:

* **PUERTA** — rasgos combinables de la puerta (relámpago, niebla, tiempo…).
* **CONTENIDO** — filtro de preguntas (materia, grupo, dificultad, tipo).

Resistencia sigue usando ``modificadores`` en tiempo de partida; el escape separa
puerta (juego) y evento (pool) a partir del mismo catálogo.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Comun.modelos import Pregunta
    from Comun.resistencia_partida import EventoAleatorioResistencia


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
    fraccion_enunciado: float = 1.0
    multiplicador_puntos: int = 1
    delta_vidas_al_completar: int = 0
    sin_pregunta: bool = False


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
    fraccion_enunciado: float = 1.0
    opciones_ocultas: int = 0
    multiplicador_puntos: int = 1
    sin_pregunta: bool = False
    delta_vidas_al_completar: int = 0
    rasgos: tuple[str, ...] = ()
    eventos_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class IconoEfectoPuerta:
    """Emoji + ayuda para la fila superior de una carta de puerta."""

    emoji: str
    tooltip: str


@dataclass(frozen=True)
class EventoContenidoInstanciado:
    """Evento de contenido con materia/grupo ya resueltos para una puerta."""

    definicion: DefinicionEvento
    materia: str | None = None
    grupo: str | None = None

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


_CATALOGO: tuple[DefinicionEvento, ...] = (
    # --- Contenido escape (materia, grupo, dificultad, tipo) ---
    _c(
        "pregunta_unica",
        "Balanceado",
        "Preguntas de una materia concreta; cualquier dificultad.",
        "⚖️",
        AlcanceEvento.COMPARTIDO,
        ModificadoresDesafio(),
        rol_escape=RolEscape.CONTENIDO,
        contenido_escape=OpcionesContenidoEscape(),
    ),
    _c(
        "solo_facil",
        "Repaso fácil",
        "Solo preguntas fáciles de la materia.",
        "🟢",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Facil"})),
        rol_escape=RolEscape.CONTENIDO,
        contenido_escape=OpcionesContenidoEscape(),
    ),
    _c(
        "solo_media",
        "Repaso medio",
        "Solo preguntas de dificultad media.",
        "🟡",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Media"})),
        rol_escape=RolEscape.CONTENIDO,
        contenido_escape=OpcionesContenidoEscape(),
    ),
    _c(
        "mix_facil_media",
        "Mix suave",
        "Preguntas fáciles o medias de la materia.",
        "🔀",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Facil", "Media"})),
        rol_escape=RolEscape.CONTENIDO,
        contenido_escape=OpcionesContenidoEscape(),
    ),
    _c(
        "solo_dificil",
        "Expertos",
        "Solo preguntas difíciles.",
        "🔴",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Dificil"})),
        rol_escape=RolEscape.CONTENIDO,
        nivel_min_sala_escape=18,
        contenido_escape=OpcionesContenidoEscape(),
    ),
    _c(
        "mezcla_media_dificil",
        "Mix exigente",
        "Preguntas medias o difíciles.",
        "🟠",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Media", "Dificil"})),
        rol_escape=RolEscape.CONTENIDO,
        nivel_min_sala_escape=10,
        contenido_escape=OpcionesContenidoEscape(),
    ),
    _c(
        "bloque_grupo",
        "Bloque temático",
        "Preguntas de varias materias de un mismo bloque temático del plan.",
        "🧩",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(),
        rol_escape=RolEscape.CONTENIDO,
        nivel_min_sala_escape=6,
        contenido_escape=OpcionesContenidoEscape(usa_grupo=True, usa_materia=False),
    ),
    _c(
        "solo_teoria",
        "Solo teoría",
        "Preguntas teóricas de la materia.",
        "📐",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(),
        rol_escape=RolEscape.CONTENIDO,
        nivel_min_sala_escape=8,
        contenido_escape=OpcionesContenidoEscape(tipos_permitidos=frozenset({"Teoria"})),
    ),
    _c(
        "solo_calculo",
        "Solo cálculo",
        "Preguntas de cálculo de la materia.",
        "🔢",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(),
        rol_escape=RolEscape.CONTENIDO,
        nivel_min_sala_escape=8,
        contenido_escape=OpcionesContenidoEscape(tipos_permitidos=frozenset({"Calculo"})),
    ),
    _c(
        "repaso_teorico",
        "Repaso teórico",
        "Teoría fácil o media de la materia.",
        "📚",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Facil", "Media"})),
        rol_escape=RolEscape.CONTENIDO,
        nivel_min_sala_escape=5,
        contenido_escape=OpcionesContenidoEscape(
            tipos_permitidos=frozenset({"Teoria"}),
        ),
    ),
    _c(
        "calculo_exigente",
        "Cálculo exigente",
        "Cálculo medio o difícil.",
        "🧮",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(dificultades_permitidas=frozenset({"Media", "Dificil"})),
        rol_escape=RolEscape.CONTENIDO,
        nivel_min_sala_escape=12,
        contenido_escape=OpcionesContenidoEscape(
            tipos_permitidos=frozenset({"Calculo"}),
        ),
    ),
    # --- Puerta escape (rasgos de juego combinables) ---
    _c(
        "descanso",
        "Descanso",
        "Sin preguntas; solo un respiro sin recompensa.",
        "💤",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(sin_pregunta=True),
        rol_escape=RolEscape.PUERTA,
        exclusivo_puerta_escape=True,
    ),
    _c(
        "respiro",
        "Respiro",
        "Sin preguntas; recuperas 1 vida (máx. 4).",
        "💚",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(sin_pregunta=True, delta_vidas_al_completar=1),
        rol_escape=RolEscape.PUERTA,
        exclusivo_puerta_escape=True,
    ),
    _c(
        "botin",
        "Botín",
        "Al superar la puerta: +1 vida (máx. 4).",
        "❤️",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(delta_vidas_al_completar=1),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=6,
    ),
    _c(
        "bruma_leve",
        "Bruma leve",
        "Se ve la mayor parte del enunciado.",
        "🌁",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(fraccion_enunciado=0.72),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=12,
    ),
    _c(
        "cadena_rapida",
        "Cadena rápida",
        "Una opción incorrecta oculta en cada pregunta.",
        "🔗",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(opciones_ocultas=1),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=20,
    ),
    _c(
        "arriesgado",
        "Arriesgado",
        "Doble puntos en cada acierto de la puerta.",
        "🎯",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(multiplicador_puntos=2),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=14,
    ),
    _c(
        "relampago",
        "Relámpago",
        "Poco tiempo para responder.",
        "⚡",
        AlcanceEvento.COMPARTIDO,
        ModificadoresDesafio(tiempo_pregunta_seg=12),
    ),
    _c(
        "relampago_duro",
        "Relámpago intenso",
        "Tiempo muy ajustado.",
        "⚡",
        AlcanceEvento.RESISTENCIA,
        ModificadoresDesafio(tiempo_pregunta_seg=6),
    ),
    _c(
        "niebla_enunciado",
        "Niebla en el enunciado",
        "Solo se ve parte del enunciado.",
        "🌫️",
        AlcanceEvento.COMPARTIDO,
        ModificadoresDesafio(fraccion_enunciado=0.45),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=16,
    ),
    _c(
        "niebla_opciones",
        "Niebla en opciones",
        "Una respuesta incorrecta está oculta.",
        "🌫️",
        AlcanceEvento.COMPARTIDO,
        ModificadoresDesafio(opciones_ocultas=1),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=18,
    ),
    _c(
        "niebla_completa",
        "Niebla total",
        "Enunciado parcial y una opción oculta.",
        "🌫️",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(fraccion_enunciado=0.5, opciones_ocultas=1),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=22,
    ),
    _c(
        "niebla_total",
        "Niebla densa",
        "Enunciado muy recortado y dos opciones ocultas.",
        "🌫️",
        AlcanceEvento.RESISTENCIA,
        ModificadoresDesafio(fraccion_enunciado=0.35, opciones_ocultas=2),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=26,
    ),
    _c(
        "cronometro_bloque",
        "Cronómetro de bloque",
        "Tiempo total para contestar toda la puerta.",
        "⏰",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(tiempo_puerta_seg=120),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=5,
    ),
    _c(
        "cronometro_pregunta",
        "Cronómetro",
        "Límite de tiempo en cada pregunta de la puerta.",
        "⏱️",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(tiempo_pregunta_seg=35),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=4,
    ),
    _c(
        "cronometro_doble",
        "Doble cronómetro",
        "Tiempo total para la puerta y límite por pregunta.",
        "⏲️",
        AlcanceEvento.ESCAPE,
        ModificadoresDesafio(tiempo_puerta_seg=150, tiempo_pregunta_seg=28),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=10,
    ),
    _c(
        "doble_puntos",
        "Puntos dobles",
        "Cada acierto de la puerta vale ×2 en arcade.",
        "✨",
        AlcanceEvento.COMPARTIDO,
        ModificadoresDesafio(multiplicador_puntos=2),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=8,
    ),
    _c(
        "triple_puntos",
        "Puntos triples",
        "El acierto vale el triple en arcade.",
        "💫",
        AlcanceEvento.RESISTENCIA,
        ModificadoresDesafio(multiplicador_puntos=3),
        rol_escape=RolEscape.PUERTA,
        nivel_min_sala_escape=24,
    ),
)

_POR_ID: dict[str, DefinicionEvento] = {e.id: e for e in _CATALOGO}

_ALIAS_RESISTENCIA: dict[str, str] = {
    "relampago": "relampago",
    "opciones_ocultas": "niebla_opciones",
    "enunciado_oculto": "niebla_enunciado",
    "doble": "doble_puntos",
}

_MAX_RASGOS_PUERTA_COMBINADOS = 2
_PROB_DESCANSO_BASE = 0.06
_PROB_BOTIN_BASE = 0.07
RASGOS_TIEMPO_PUERTA_ESCAPE = frozenset({
    "cronometro_bloque",
    "cronometro_pregunta",
    "cronometro_doble",
})
RASGOS_MULTIPLICADOR_PUERTA_ESCAPE = frozenset({
    "arriesgado",
    "doble_puntos",
    "triple_puntos",
})
RASGOS_ENUNCIADO_PUERTA_ESCAPE = frozenset({
    "bruma_leve",
    "niebla_enunciado",
    "niebla_completa",
    "niebla_total",
})
RASGOS_OPCIONES_PUERTA_ESCAPE = frozenset({
    "cadena_rapida",
    "niebla_opciones",
    "niebla_completa",
    "niebla_total",
})
_FAMILIAS_EXCLUSIVAS_PUERTA: tuple[frozenset[str], ...] = (
    RASGOS_TIEMPO_PUERTA_ESCAPE,
    RASGOS_MULTIPLICADOR_PUERTA_ESCAPE,
    RASGOS_ENUNCIADO_PUERTA_ESCAPE,
    RASGOS_OPCIONES_PUERTA_ESCAPE,
)
RASGOS_RECOMPENSA_VIDAS_ESCAPE = frozenset({"botin"})
RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE = frozenset({"descanso", "respiro"})
RASGOS_EXTRA_PUERTA_SIN_PREGUNTA_ESCAPE = frozenset({"botin"})
_RASGOS_SOLO_RECOMPENSA = frozenset({"botin"})
_PESO_PUERTA_SIN_PREGUNTA: dict[str, int] = {
    "descanso": 7,
    "respiro": 3,
}


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


# Compatibilidad con código previo.
eventos_escape_para_sala = eventos_contenido_escape_para_sala


def evento_sin_pregunta_escape(
    modificadores: ModificadoresPuerta,
) -> DefinicionEvento | None:
    """Tipo de puerta sin preguntas (descanso, respiro, …)."""
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
        return all(e.id in RASGOS_EXTRA_PUERTA_SIN_PREGUNTA_ESCAPE for e in elegidos)
    if any(e.exclusivo_puerta_escape for e in elegidos):
        return candidato.id in RASGOS_EXTRA_PUERTA_SIN_PREGUNTA_ESCAPE
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
    """Conserva el orden; en pausa solo descanso/respiro y, opcionalmente, botín."""
    if not rasgos:
        return ()
    pausa = next((r for r in rasgos if r.exclusivo_puerta_escape), None)
    if pausa is not None:
        botin = next((r for r in rasgos if r.id in RASGOS_EXTRA_PUERTA_SIN_PREGUNTA_ESCAPE), None)
        return (pausa, botin) if botin is not None else (pausa,)
    elegidos: list[DefinicionEvento] = []
    for ev in rasgos:
        if _compatible_con_rasgos_puerta(ev, tuple(elegidos)):
            elegidos.append(ev)
    return tuple(elegidos)


def _modificadores_puerta_sin_pregunta(
    pausa: DefinicionEvento,
    recompensas: tuple[DefinicionEvento, ...],
) -> ModificadoresPuerta:
    """Puerta sin preguntas; solo admite botín como rasgo adicional."""
    extra = recompensas[:1]
    etiquetas = [pausa.nombre, *(r.nombre for r in extra)]
    eventos_ids = (pausa.id, *(r.id for r in extra))
    delta = pausa.modificadores.delta_vidas_al_completar + sum(
        r.modificadores.delta_vidas_al_completar for r in extra
    )
    return ModificadoresPuerta(
        sin_pregunta=True,
        delta_vidas_al_completar=delta,
        rasgos=tuple(etiquetas),
        eventos_ids=eventos_ids,
    )


def combinar_modificadores_puerta(
    rasgos: tuple[DefinicionEvento, ...],
) -> ModificadoresPuerta:
    """Combina rasgos de puerta del catálogo común."""
    rasgos = _filtrar_rasgos_puerta_compatibles(rasgos)
    if not rasgos:
        return ModificadoresPuerta(rasgos=("Clásica",))
    if any(r.exclusivo_puerta_escape for r in rasgos):
        pausa = next(r for r in rasgos if r.exclusivo_puerta_escape)
        recompensas = tuple(r for r in rasgos if r.id in RASGOS_RECOMPENSA_VIDAS_ESCAPE)
        return _modificadores_puerta_sin_pregunta(pausa, recompensas)

    tiempo_preg: int | None = None
    tiempo_puerta: int | None = None
    fraccion = 1.0
    opciones = 0
    mult = 1
    delta_vidas = 0
    etiquetas: list[str] = []

    for ev in rasgos:
        m = ev.modificadores
        if m.tiempo_pregunta_seg is not None:
            tiempo_preg = (
                m.tiempo_pregunta_seg
                if tiempo_preg is None
                else min(tiempo_preg, m.tiempo_pregunta_seg)
            )
        if m.tiempo_puerta_seg is not None:
            tiempo_puerta = (
                m.tiempo_puerta_seg
                if tiempo_puerta is None
                else min(tiempo_puerta, m.tiempo_puerta_seg)
            )
        fraccion = min(fraccion, m.fraccion_enunciado)
        opciones = max(opciones, m.opciones_ocultas)
        mult = max(mult, m.multiplicador_puntos)
        delta_vidas += m.delta_vidas_al_completar
        etiquetas.append(ev.nombre)

    return ModificadoresPuerta(
        tiempo_pregunta_seg=tiempo_preg,
        tiempo_puerta_seg=tiempo_puerta,
        fraccion_enunciado=fraccion,
        opciones_ocultas=opciones,
        multiplicador_puntos=mult,
        delta_vidas_al_completar=delta_vidas,
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
        fraccion_enunciado=m.fraccion_enunciado,
        opciones_ocultas=m.opciones_ocultas,
        multiplicador_puntos=m.multiplicador_puntos,
        sin_pregunta=m.sin_pregunta,
        delta_vidas_al_completar=m.delta_vidas_al_completar,
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
) -> ModificadoresPuerta:
    rng = random.Random(semilla + indice_puerta * 8831 + numero_sala * 97)
    disponibles = [
        e for e in eventos_puerta_escape_para_sala(numero_sala) if not e.exclusivo_puerta_escape
    ]
    recompensas = [e for e in disponibles if e.id in RASGOS_RECOMPENSA_VIDAS_ESCAPE]
    desafios = [e for e in disponibles if e.id not in RASGOS_RECOMPENSA_VIDAS_ESCAPE]
    prob_descanso = _PROB_DESCANSO_BASE + min(0.04, (numero_sala - 1) * 0.002)
    puertas_pausa = [
        e for e in eventos_puerta_escape_para_sala(numero_sala) if e.exclusivo_puerta_escape
    ]
    if puertas_pausa and rng.random() < prob_descanso:
        disponibles_pausa = [e for e in puertas_pausa if e.id not in pausas_usadas]
        if disponibles_pausa:
            pesos = [_PESO_PUERTA_SIN_PREGUNTA.get(e.id, 1) for e in disponibles_pausa]
            pausa = rng.choices(disponibles_pausa, weights=pesos, k=1)[0]
            rasgos_pausa: list[DefinicionEvento] = [pausa]
            botin = evento_por_id("botin")
            prob_botin = _PROB_BOTIN_BASE + min(0.03, (numero_sala - 1) * 0.001)
            if (
                botin in eventos_puerta_escape_para_sala(numero_sala)
                and rng.random() < prob_botin
            ):
                rasgos_pausa.append(botin)
            return combinar_modificadores_puerta(tuple(rasgos_pausa))

    min_rasgos = 0
    prob_rasgo = 0.42 + min(0.45, (numero_sala - 1) * 0.012)
    if rng.random() < prob_rasgo:
        min_rasgos = 1
    if numero_sala >= 12 and rng.random() < 0.28:
        min_rasgos = max(min_rasgos, 2)

    max_rasgos = min(_MAX_RASGOS_PUERTA_COMBINADOS, len(desafios))
    if max_rasgos <= 0 and not recompensas:
        return combinar_modificadores_puerta(())
    n_extra = rng.randint(min(min_rasgos, max_rasgos), max_rasgos) if max_rasgos else 0
    elegidos = _elegir_desafios_puerta(desafios, n_extra, rng)
    if recompensas and rng.random() < _PROB_BOTIN_BASE + min(0.03, (numero_sala - 1) * 0.001):
        elegidos.append(rng.choice(recompensas))
    return combinar_modificadores_puerta(tuple(elegidos))


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
            lineas.append("💤 Sin preguntas en esta puerta.")
        if "botin" in modificadores.eventos_ids:
            lineas.append("Botín extra al superar: +1 vida (máx. 4)")
        return "\n".join(lineas)
    if modificadores.delta_vidas_al_completar > 0:
        n = modificadores.delta_vidas_al_completar
        txt = "1 vida" if n == 1 else f"{n} vidas"
        lineas.append(f"Recompensa al superar: +{txt} (máx. 4)")
    lineas.append(f"Preguntas: {n_preguntas}")
    if modificadores.rasgos:
        lineas.append(" · ".join(modificadores.rasgos))
    if modificadores.tiempo_puerta_seg:
        lineas.append(f"Tiempo de puerta: {modificadores.tiempo_puerta_seg} s")
    if modificadores.tiempo_pregunta_seg:
        lineas.append(f"Tiempo por pregunta: {modificadores.tiempo_pregunta_seg} s")
    if modificadores.fraccion_enunciado < 1.0:
        lineas.append("Enunciado parcial")
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
    if evento.dificultades_permitidas:
        difs = ", ".join(sorted(evento.dificultades_permitidas))
        lineas.append(f"Dificultad: {difs}")
    if evento.tipos_permitidos:
        tipos = ", ".join(sorted(evento.tipos_permitidos))
        lineas.append(f"Tipo: {tipos}")
    return "\n".join(lineas)


def tooltip_efecto_rasgo_puerta(evento_id: str) -> str:
    """Ayuda breve del icono: solo mecánica de juego, sin nombre ni descripción del catálogo."""
    ev = evento_por_id(evento_id)
    m = ev.modificadores
    partes: list[str] = []
    if m.sin_pregunta:
        partes.append("Sin preguntas en esta puerta.")
        if m.delta_vidas_al_completar:
            partes.append(f"Recuperas {m.delta_vidas_al_completar} vida.")
        return " ".join(partes)
    if m.tiempo_puerta_seg is not None:
        partes.append(f"{m.tiempo_puerta_seg} s para toda la puerta.")
    if m.tiempo_pregunta_seg is not None:
        partes.append(f"{m.tiempo_pregunta_seg} s por pregunta.")
    if m.fraccion_enunciado < 1.0:
        pct = int(round(m.fraccion_enunciado * 100))
        partes.append(f"Enunciado visible al {pct}%.")
    if m.opciones_ocultas:
        n = m.opciones_ocultas
        if n == 1:
            partes.append("1 opción incorrecta oculta.")
        else:
            partes.append(f"{n} opciones incorrectas ocultas.")
    if m.multiplicador_puntos > 1:
        partes.append(
            f"×{m.multiplicador_puntos} puntos en cada acierto de esta puerta."
        )
    return " ".join(partes) if partes else ev.descripcion


def tooltip_bloque_preguntas(n_preguntas: int) -> str:
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
            f"Al superarla sin fallar: +{txt} (máx. 4)."
        )
    n = bonus.delta_vidas
    txt = "1 vida" if n == 1 else f"{n} vidas"
    return f"Al superar la puerta sin fallar: +{txt} (máx. 4)."


_EMOJI_DIFICULTAD: dict[str, str] = {
    "Facil": "🟢",
    "Media": "🟡",
    "Dificil": "🔴",
}
_EMOJI_DIFS_DOS = "🎁"
_EMOJI_DIFS_TODAS = "⚖️"
_EMOJI_TIPO: dict[str, str] = {
    "Teoria": "📐",
    "Calculo": "🧮",
}


def _icono_filtro_dificultad(
    evento: EventoContenidoInstanciado,
) -> IconoEfectoPuerta | None:
    difs = evento.dificultades_permitidas
    if difs:
        if len(difs) == 1:
            d = next(iter(difs))
            return IconoEfectoPuerta(
                emoji=_EMOJI_DIFICULTAD.get(d, evento.emoji),
                tooltip=f"Solo dificultad {d}.",
            )
        if len(difs) == 2:
            difs_txt = ", ".join(sorted(difs))
            return IconoEfectoPuerta(
                emoji=_EMOJI_DIFS_DOS,
                tooltip=f"Dificultad: {difs_txt}.",
            )
        return IconoEfectoPuerta(
            emoji=_EMOJI_DIFS_TODAS,
            tooltip="Todas las dificultades de la materia.",
        )
    opts = evento.contenido_escape
    if evento.tipos_permitidos:
        return None
    if opts and opts.usa_grupo:
        return IconoEfectoPuerta(
            emoji=_EMOJI_DIFS_TODAS,
            tooltip="Complejidad según la sala; materias de todo el grupo.",
        )
    return IconoEfectoPuerta(
        emoji=_EMOJI_DIFS_TODAS,
        tooltip="Todas las dificultades de la materia.",
    )


def iconos_contenido_puerta(evento: EventoContenidoInstanciado) -> tuple[IconoEfectoPuerta, ...]:
    """Un emoji por aspecto de contenido (grupo, dificultad, tipo…)."""
    iconos: list[IconoEfectoPuerta] = []
    opts = evento.contenido_escape

    if opts and opts.usa_grupo:
        iconos.append(
            IconoEfectoPuerta(
                emoji="🧩",
                tooltip="Bloque de un grupo del plan (varias materias).",
            )
        )

    icono_difs = _icono_filtro_dificultad(evento)
    if icono_difs is not None:
        iconos.append(icono_difs)

    tipos = evento.tipos_permitidos
    if tipos:
        if len(tipos) == 1:
            t = next(iter(tipos))
            iconos.append(
                IconoEfectoPuerta(
                    emoji=_EMOJI_TIPO.get(t, "📋"),
                    tooltip=f"Solo preguntas de {t.lower()}.",
                )
            )
        else:
            tipos_txt = ", ".join(sorted(tipos))
            iconos.append(
                IconoEfectoPuerta(
                    emoji="📋",
                    tooltip=f"Tipo: {tipos_txt}.",
                )
            )

    return tuple(iconos)


def ids_pool_resistencia_aleatorio() -> tuple[str, ...]:
    return ("relampago", "opciones_ocultas", "enunciado_oculto", "doble")


def ids_eventos_buenos_resistencia() -> tuple[str, ...]:
    return ("doble",)


def ids_eventos_malos_resistencia() -> tuple[str, ...]:
    return ("relampago", "opciones_ocultas", "enunciado_oculto")


PREGUNTA_MIN_NIEBLA_RESISTENCIA = 25
_NIEBLA_MALOS_RESISTENCIA = frozenset({"opciones_ocultas", "enunciado_oculto"})


def niebla_disponible_resistencia(numero_pregunta: int) -> bool:
    return numero_pregunta >= PREGUNTA_MIN_NIEBLA_RESISTENCIA


def ids_eventos_malos_resistencia_para(numero_pregunta: int) -> tuple[str, ...]:
    todos = ids_eventos_malos_resistencia()
    if niebla_disponible_resistencia(numero_pregunta):
        return todos
    return tuple(k for k in todos if k not in _NIEBLA_MALOS_RESISTENCIA)


def evento_resistencia_aleatorio(kind: str, intensidad: float) -> EventoAleatorioResistencia:
    from Comun.resistencia_partida import EventoAleatorioResistencia

    clave = _ALIAS_RESISTENCIA.get(kind, kind)
    base = evento_por_id(clave)
    mod = base.modificadores

    tiempo = mod.tiempo_pregunta_seg
    if clave == "relampago" and tiempo is not None:
        tiempo = max(3, int(11 - 7 * intensidad))
    fraccion = mod.fraccion_enunciado
    if clave == "niebla_enunciado":
        fraccion = 0.55 if intensidad < 0.7 else 0.4
    opciones_ocultas = mod.opciones_ocultas
    if clave == "niebla_opciones":
        opciones_ocultas = 1 if intensidad < 0.6 else 2
    mult = mod.multiplicador_puntos
    if clave == "doble_puntos":
        mult = 2 if intensidad < 0.75 else 3

    etiqueta = base.nombre
    if clave == "relampago" and tiempo is not None:
        etiqueta = f"Relámpago: {tiempo} s por pregunta"
    elif clave == "niebla_opciones":
        etiqueta = f"Niebla: {opciones_ocultas} respuesta(s) oculta(s)"
    elif clave == "niebla_enunciado":
        etiqueta = "Niebla: enunciado parcialmente oculto"
    elif clave == "doble_puntos":
        etiqueta = "Doble puntos" if mult == 2 else "Triple puntos"

    return EventoAleatorioResistencia(
        etiqueta=etiqueta,
        tiempo_pregunta=tiempo,
        multiplicador_puntos=mult if mult > 1 else None,
        opciones_ocultas=opciones_ocultas or None,
        fraccion_enunciado=fraccion if fraccion < 1.0 else None,
    )


def emoji_evento_id(evento_id: str) -> str:
    return evento_por_id(evento_id).emoji


def descripcion_evento_id(evento_id: str) -> str:
    ev = evento_por_id(evento_id)
    return f"{ev.nombre}: {ev.descripcion}"


def iconos_efecto_puerta(
    *,
    evento: EventoContenidoInstanciado,
    modificadores: ModificadoresPuerta,
    n_preguntas: int,
) -> tuple[IconoEfectoPuerta, ...]:
    """Emojis de rasgos de puerta + bloque + contenido (tooltips = mecánica y filtros)."""
    iconos: list[IconoEfectoPuerta] = []

    for eid in modificadores.eventos_ids:
        if eid in _RASGOS_SOLO_RECOMPENSA:
            continue
        ev = evento_por_id(eid)
        iconos.append(
            IconoEfectoPuerta(emoji=ev.emoji, tooltip=tooltip_efecto_rasgo_puerta(eid))
        )

    if not modificadores.sin_pregunta and n_preguntas > 0:
        iconos.append(
            IconoEfectoPuerta(
                emoji="🔢",
                tooltip=tooltip_bloque_preguntas(n_preguntas),
            )
        )
        iconos.extend(iconos_contenido_puerta(evento))
    return tuple(iconos)
