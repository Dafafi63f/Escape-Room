#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo escape room: salas con tres puertas (rasgos de puerta + evento de contenido)."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from Comun.eventos_partida import (
    EventoContenidoInstanciado,
    ModificadoresPuerta,
    PityPuertasEspecialesEscape,
    RASGOS_BOTIN_ESCAPE,
    RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE,
    SALAS_HARD_PITY_BOTIN_ESCAPE,
    SALAS_HARD_PITY_DESCANSO_ESCAPE,
    SALAS_HARD_PITY_TIENDA_ESCAPE,
    actualizar_pity_tras_sala,
    combinar_modificadores_puerta,
    debe_garantizar_botin_escape,
    debe_garantizar_descanso_escape,
    debe_garantizar_tienda_escape,
    definicion_grupo_con_perfil,
    definicion_materia_con_perfil,
    elegir_botin_para_sala,
    elegir_plantillas_contenido_escape,
    evento_por_id,
    generar_modificadores_puerta,
    instanciar_evento_contenido,
    materias_distintas_puertas,
    perfil_materia_por_id,
    texto_evento_contenido,
    texto_modificadores_puerta,
)
from Comun.escape_partida import (
    asegurar_puerta_viable,
    grupos_del_pool,
    grupos_viables_sala,
    materias_viables_sala,
)
from Comun.modelos import BancoPreguntas, OPCIONES_BANCO_JUEGO, Pregunta

ID_PRESET_ESCAPE_ROOM = "escape_room"
_CONTEXTO_ESCAPE = "escape"
PUERTAS_POR_SALA = 3
SALAS_MIN = 5
SALAS_MAX = 50
SALAS_PASO = 5
SALAS_DEFECTO = 30
TAMANOS_PUERTA = (3, 5, 10)
OPCIONES_BANCO_ESCAPE = OPCIONES_BANCO_JUEGO

__all__ = [
    "AjustesEscapeRoom",
    "ConfigEscapeRoom",
    "GuionEscapeRoom",
    "ID_PRESET_ESCAPE_ROOM",
    "OPCIONES_BANCO_ESCAPE",
    "PUERTAS_POR_SALA",
    "PuertaEscape",
    "SalaEscapeRoom",
    "SALAS_DEFECTO",
    "SALAS_MAX",
    "SALAS_HARD_PITY_DESCANSO_ESCAPE",
    "SALAS_HARD_PITY_TIENDA_ESCAPE",
    "SALAS_HARD_PITY_BOTIN_ESCAPE",
    "PityPuertasEspecialesEscape",
    "firma_puerta_escape",
    "SALAS_MIN",
    "SALAS_PASO",
    "TAMANOS_PUERTA",
    "config_escape_room",
    "es_preset_escape_room",
    "generar_puertas_sala",
    "generar_salas_escape",
    "normalizar_n_salas_escape",
    "semilla_partida_escape",
    "tamanos_puerta_para_sala",
    "total_preguntas_escape",
    "total_preguntas_guion",
]


def normalizar_n_salas_escape(n: int) -> int:
    """Acota y alinea al paso de 5 entre SALAS_MIN y SALAS_MAX."""
    n = max(SALAS_MIN, min(SALAS_MAX, int(n)))
    offset = n - SALAS_MIN
    return SALAS_MIN + (offset // SALAS_PASO) * SALAS_PASO


@dataclass(frozen=True)
class AjustesEscapeRoom:
    """Opciones elegidas antes de iniciar una partida escape."""

    banco: BancoPreguntas = BancoPreguntas.DATASET
    n_salas: int = SALAS_DEFECTO

    def __post_init__(self) -> None:
        object.__setattr__(self, "n_salas", normalizar_n_salas_escape(self.n_salas))
        if self.banco not in OPCIONES_BANCO_ESCAPE:
            raise ValueError(f"banco no válido: {self.banco}")


@dataclass(frozen=True)
class PuertaEscape:
    """Puerta: tamaño del bloque + rasgos de juego; el evento filtra el contenido."""

    indice: int
    n_preguntas: int
    modificadores: ModificadoresPuerta
    evento: EventoContenidoInstanciado

    @property
    def texto_completo(self) -> str:
        partes = [
            texto_modificadores_puerta(self.modificadores, n_preguntas=self.n_preguntas),
            texto_evento_contenido(self.evento),
        ]
        return "\n".join(partes)


def firma_puerta_escape(puerta: PuertaEscape) -> tuple[str, ...]:
    """Identidad visible de la puerta para evitar duplicados en la misma sala."""
    if puerta.modificadores.sin_pregunta:
        for eid in puerta.modificadores.eventos_ids:
            if eid in RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE:
                return ("pausa", eid)
        return ("pausa", "descanso")
    foco = puerta.evento.etiqueta_foco or ""
    perfil = puerta.evento.perfil_id or ""
    return ("contenido", puerta.evento.id, perfil, foco)


@dataclass(frozen=True)
class SalaEscapeRoom:
    id: str
    nombre: str


@dataclass(frozen=True)
class ConfigEscapeRoom:
    n_salas: int
    puertas_por_sala: int
    salas: tuple[SalaEscapeRoom, ...]


def es_preset_escape_room(preset) -> bool:
    return getattr(preset, "contexto_reglas", "") == _CONTEXTO_ESCAPE


def total_preguntas_escape(config: ConfigEscapeRoom) -> int:
    return config.n_salas


def config_escape_room(
    *,
    n_salas: int = SALAS_DEFECTO,
    puertas_por_sala: int = PUERTAS_POR_SALA,
) -> ConfigEscapeRoom:
    if n_salas <= 0:
        raise ValueError("n_salas debe ser positivo.")
    if puertas_por_sala <= 0:
        raise ValueError("puertas_por_sala debe ser positivo.")
    salas = generar_salas_escape(n_salas=n_salas)
    return ConfigEscapeRoom(
        n_salas=n_salas,
        puertas_por_sala=puertas_por_sala,
        salas=salas,
    )


def generar_salas_escape(*, n_salas: int) -> tuple[SalaEscapeRoom, ...]:
    return tuple(
        SalaEscapeRoom(id=f"sala_{i + 1:02d}", nombre=f"Sala {i + 1}")
        for i in range(n_salas)
    )


def tamanos_puerta_para_sala(
    sala_idx: int,
    *,
    n_salas: int,
    puertas_por_sala: int,
    rng: random.Random,
) -> tuple[int, ...]:
    numero = sala_idx + 1
    if numero <= max(1, n_salas // 3):
        plantilla = [3, 3, 3]
        if rng.random() < 0.35:
            plantilla[rng.randrange(puertas_por_sala)] = 5
    else:
        t = (numero - 1) / max(1, n_salas - 1)
        if t < 0.55:
            plantilla = [3, 3, 5]
        elif t < 0.85:
            plantilla = [3, 5, 5]
        else:
            plantilla = [3, 5, 10]

    tamanos = list(plantilla)
    while len(tamanos) < puertas_por_sala:
        tamanos.append(rng.choice(TAMANOS_PUERTA))
    rng.shuffle(tamanos[:puertas_por_sala])
    return tuple(tamanos[:puertas_por_sala])


def generar_puertas_sala(
    sala: SalaEscapeRoom,
    sala_idx: int,
    *,
    materias_pool: tuple[str, ...],
    pool_preguntas: list[Pregunta],
    semilla: int,
    puertas_por_sala: int = PUERTAS_POR_SALA,
    n_salas: int = SALAS_DEFECTO,
    pity: PityPuertasEspecialesEscape | None = None,
) -> tuple[tuple[PuertaEscape, ...], PityPuertasEspecialesEscape]:
    if not materias_pool:
        raise ValueError("El pool de materias del escape room está vacío.")

    estado_pity = pity or PityPuertasEspecialesEscape()
    puertas: tuple[PuertaEscape, ...] = ()
    for intento in range(64):
        puertas = _construir_puertas_sala(
            sala,
            sala_idx,
            materias_pool=materias_pool,
            pool_preguntas=pool_preguntas,
            semilla=semilla + intento * 1_000_003,
            puertas_por_sala=puertas_por_sala,
            n_salas=n_salas,
            pity=estado_pity,
        )
        firmas = [firma_puerta_escape(p) for p in puertas]
        if len(set(firmas)) == len(firmas):
            estado_pity = actualizar_pity_tras_sala(
                estado_pity, puertas, numero_sala=sala_idx + 1
            )
            return puertas, estado_pity
    estado_pity = actualizar_pity_tras_sala(
        estado_pity, puertas, numero_sala=sala_idx + 1
    )
    return puertas, estado_pity


def _insertar_puerta_especial_escape(
    puertas: list[PuertaEscape],
    *,
    pausa_id: str,
    semilla: int,
    sala_idx: int,
    numero_sala: int,
    materias_base: tuple[str, ...],
) -> None:
    if any(pausa_id in p.modificadores.eventos_ids for p in puertas):
        return
    pausa = evento_por_id(pausa_id)
    if numero_sala < pausa.nivel_min_sala_escape:
        return
    candidatos = [
        i for i, p in enumerate(puertas) if not p.modificadores.sin_pregunta
    ]
    if not candidatos:
        candidatos = list(range(len(puertas)))
    rng = random.Random(semilla + sala_idx * 3001 + len(pausa_id) * 97)
    idx = rng.choice(candidatos)
    mods = combinar_modificadores_puerta((pausa,), numero_sala=numero_sala)
    evento = instanciar_evento_contenido(
        evento_por_id("puerta_materia"),
        materias_pool=materias_base,
        grupos_pool=(),
        semilla=semilla,
        indice_puerta=sala_idx * 10 + idx,
        materia_preferida=materias_base[idx % len(materias_base)],
    )
    puertas[idx] = replace(
        puertas[idx],
        n_preguntas=0,
        modificadores=mods,
        evento=evento,
    )


def _insertar_botin_en_puerta_escape(
    puertas: list[PuertaEscape],
    *,
    numero_sala: int,
    semilla: int,
    sala_idx: int,
) -> None:
    if any(
        any(eid in RASGOS_BOTIN_ESCAPE for eid in p.modificadores.eventos_ids)
        for p in puertas
    ):
        return
    candidatos = [
        i for i, p in enumerate(puertas) if not p.modificadores.sin_pregunta
    ]
    if not candidatos:
        return
    rng = random.Random(semilla + sala_idx * 2903 + 13)
    idx = rng.choice(candidatos)
    puerta = puertas[idx]
    ev_ids = [
        eid
        for eid in puerta.modificadores.eventos_ids
        if eid not in RASGOS_BOTIN_ESCAPE
    ]
    botin = elegir_botin_para_sala(numero_sala, rng)
    if botin is None:
        return
    rasgos = [evento_por_id(eid) for eid in ev_ids] + [botin]
    mods = combinar_modificadores_puerta(tuple(rasgos), numero_sala=numero_sala)
    puertas[idx] = replace(puerta, modificadores=mods)


def _aplicar_hard_pity_puertas_especiales(
    puertas: list[PuertaEscape],
    *,
    pity: PityPuertasEspecialesEscape,
    numero_sala: int,
    semilla: int,
    sala_idx: int,
    materias_base: tuple[str, ...],
) -> None:
    """Inserta descanso o tienda si el hard pity lo exige y aún no hay ninguno en la sala."""
    if debe_garantizar_descanso_escape(pity, numero_sala):
        _insertar_puerta_especial_escape(
            puertas,
            pausa_id="descanso",
            semilla=semilla,
            sala_idx=sala_idx,
            numero_sala=numero_sala,
            materias_base=materias_base,
        )
    if debe_garantizar_tienda_escape(pity, numero_sala):
        _insertar_puerta_especial_escape(
            puertas,
            pausa_id="tienda",
            semilla=semilla,
            sala_idx=sala_idx,
            numero_sala=numero_sala,
            materias_base=materias_base,
        )
    if debe_garantizar_botin_escape(pity, numero_sala):
        _insertar_botin_en_puerta_escape(
            puertas,
            numero_sala=numero_sala,
            semilla=semilla,
            sala_idx=sala_idx,
        )


def _construir_puertas_sala(
    sala: SalaEscapeRoom,
    sala_idx: int,
    *,
    materias_pool: tuple[str, ...],
    pool_preguntas: list[Pregunta],
    semilla: int,
    puertas_por_sala: int,
    n_salas: int,
    pity: PityPuertasEspecialesEscape,
) -> tuple[PuertaEscape, ...]:
    del sala
    numero_sala = sala_idx + 1
    rng = random.Random(semilla + sala_idx * 7919)
    plantillas = elegir_plantillas_contenido_escape(puertas_por_sala, numero_sala, rng)
    materias_base = materias_viables_sala(
        pool_preguntas,
        materias_pool,
        numero_sala=numero_sala,
        n_salas=n_salas,
    )
    materias_puerta = materias_distintas_puertas(materias_base, puertas_por_sala, rng)

    tamanos = tamanos_puerta_para_sala(
        sala_idx, n_salas=n_salas, puertas_por_sala=puertas_por_sala, rng=rng
    )
    grupos_pool = grupos_del_pool(pool_preguntas)
    grupos_base = grupos_viables_sala(
        pool_preguntas,
        grupos_pool,
        numero_sala=numero_sala,
        n_salas=n_salas,
    )

    puertas: list[PuertaEscape] = []
    pausas_usadas: set[str] = set()
    for i, (plantilla, perfil_id) in enumerate(plantillas):
        mods = generar_modificadores_puerta(
            numero_sala=numero_sala,
            semilla=semilla + sala_idx * 1009,
            indice_puerta=i,
            pausas_usadas=frozenset(pausas_usadas),
            pity=pity,
        )
        if mods.sin_pregunta:
            for eid in mods.eventos_ids:
                if eid in RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE:
                    pausas_usadas.add(eid)
        n_preg = 0 if mods.sin_pregunta else tamanos[i]
        if mods.sin_pregunta:
            evento = instanciar_evento_contenido(
                evento_por_id("puerta_materia"),
                materias_pool=materias_base,
                grupos_pool=(),
                semilla=semilla,
                indice_puerta=sala_idx * 10 + i,
                materia_preferida=materias_base[i % len(materias_base)],
            )
        else:
            plantilla_usada = plantilla
            perfil_usado = perfil_id
            if n_preg >= 10 and numero_sala >= perfil_materia_por_id("dificil").nivel_min_sala and rng.random() < 0.6:
                perfil_dificil = perfil_materia_por_id("dificil")
                opts_jefe = plantilla.contenido_escape
                if opts_jefe and opts_jefe.usa_grupo:
                    plantilla_usada = definicion_grupo_con_perfil(perfil_dificil)
                else:
                    plantilla_usada = definicion_materia_con_perfil(perfil_dificil)
                perfil_usado = "dificil"
            materia_pref = materias_puerta[i] if i < len(materias_puerta) else None
            opts = plantilla_usada.contenido_escape
            usa_grupo = bool(opts and opts.usa_grupo)
            evento = instanciar_evento_contenido(
                plantilla_usada,
                materias_pool=materias_base if not usa_grupo else materias_pool,
                grupos_pool=grupos_base if usa_grupo else grupos_pool,
                semilla=semilla,
                indice_puerta=sala_idx * 10 + i,
                materia_preferida=None if usa_grupo else materia_pref,
                perfil_id=perfil_usado,
            )
        puerta = PuertaEscape(indice=i, n_preguntas=n_preg, modificadores=mods, evento=evento)
        puerta = asegurar_puerta_viable(
            pool_preguntas,
            puerta,
            numero_sala=numero_sala,
            n_salas=n_salas,
            semilla=semilla + sala_idx * 1009,
            indice_puerta=i,
            materias_pool=materias_base,
            grupos_pool=grupos_base,
        )
        puertas.append(puerta)
    _aplicar_hard_pity_puertas_especiales(
        puertas,
        pity=pity,
        numero_sala=numero_sala,
        semilla=semilla,
        sala_idx=sala_idx,
        materias_base=materias_base,
    )
    return tuple(puertas)


def semilla_partida_escape(*, nombre: str) -> int:
    from datetime import date

    hoy = date.today().isoformat()
    texto = f"{nombre}|escape|{hoy}"
    return abs(hash(texto)) % (2**31)


GuionEscapeRoom = ConfigEscapeRoom
cargar_guion_escape_room = config_escape_room
total_preguntas_guion = total_preguntas_escape
