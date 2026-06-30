#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo escape room: salas con tres puertas (rasgos de puerta + evento de contenido).

Generación procedural por semilla aleatoria en cada partida (``semilla_partida_escape``).
Un ``RngPartida`` avanza todo el azar de la sesión (puertas, tienda, botín).
Pity de descanso, tienda y botín; la tienda se pospone si no hay puntos para comprar.
Economía e inventario: ``economia_partida`` + ``objetos_partida`` vía ``tienda_escape``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from Comun.eventos_partida import (
    DefinicionEvento,
    EventoContenidoInstanciado,
    ModificadoresPuerta,
    PityPuertasEspecialesEscape,
    RASGOS_BOTIN_ESCAPE,
    RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE,
    RASGO_PUERTA_MALDITA,
    SALAS_HARD_PITY_BOTIN_ESCAPE,
    SALAS_HARD_PITY_DESCANSO_ESCAPE,
    SALAS_HARD_PITY_TIENDA_ESCAPE,
    actualizar_pity_tras_sala,
    combinar_modificadores_puerta,
    cursos_del_pool,
    debe_garantizar_botin_escape,
    debe_garantizar_descanso_escape,
    debe_garantizar_tienda_escape,
    definicion_grupo_con_perfil,
    definicion_materia_con_perfil,
    elegir_botin_para_sala,
    elegir_botines_jefe_escape,
    elegir_plantillas_contenido_escape,
    evento_por_id,
    generar_modificadores_puerta,
    instanciar_evento_contenido,
    materias_distintas_puertas,
    perfil_materia_por_id,
    periodos_del_pool,
    semestres_del_pool,
    texto_evento_contenido,
    texto_modificadores_puerta,
)
from Comun.escape_partida import (
    asegurar_puerta_viable,
    grupos_del_pool,
    grupos_viables_sala,
    materias_viables_sala,
)
from Comun.jefe_partida import (
    PREGUNTAS_POR_JEFE,
    TAMANOS_BLOQUE_NORMAL,
    elegir_dificultad_jefe_escape,
    n_puertas_jefe_en_sala,
    perfil_id_para_dificultad_jefe,
    sala_es_milestone_jefe,
)
from Comun.modelos import BancoPreguntas, OPCIONES_BANCO_JUEGO, Pregunta

ID_PRESET_ESCAPE_ROOM = "escape_room"
_CONTEXTO_ESCAPE = "escape"
PUERTAS_POR_SALA = 3
SALAS_MIN = 5
SALAS_MAX = 50
SALAS_PASO = 5
SALAS_DEFECTO = 30
TAMANOS_PUERTA = TAMANOS_BLOQUE_NORMAL
OPCIONES_BANCO_ESCAPE = OPCIONES_BANCO_JUEGO

__all__ = [
    "AjustesEscapeRoom",
    "ConfigEscapeRoom",
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
    "quitar_maldicion_puertas_sala",
    "regenerar_puertas_sala_escape",
    "semilla_partida_escape",
    "tamanos_puerta_para_sala",
    "total_preguntas_escape",
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
    es_jefe: bool = False

    @property
    def texto_completo(self) -> str:
        partes = [
            texto_modificadores_puerta(self.modificadores, n_preguntas=self.n_preguntas),
            texto_evento_contenido(self.evento),
        ]
        return "\n".join(partes)


def firma_puerta_escape(puerta: PuertaEscape) -> tuple[str, ...]:
    """Identidad visible de la puerta para evitar duplicados en la misma sala."""
    if puerta.es_jefe:
        foco = puerta.evento.etiqueta_foco or puerta.evento.grupo or ""
        perfil = puerta.evento.perfil_id or ""
        return ("jefe", puerta.evento.id, perfil, foco)
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
            plantilla = [3, 5, 5]

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
    rng: random.Random,
    puertas_por_sala: int = PUERTAS_POR_SALA,
    n_salas: int = SALAS_DEFECTO,
    pity: PityPuertasEspecialesEscape | None = None,
    estado=None,
    vidas_max: int | None = None,
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
            rng=rng,
            puertas_por_sala=puertas_por_sala,
            n_salas=n_salas,
            pity=estado_pity,
            estado=estado,
            vidas_max=vidas_max,
        )
        firmas = [firma_puerta_escape(p) for p in puertas]
        if len(set(firmas)) == len(firmas):
            estado_pity = actualizar_pity_tras_sala(
                estado_pity,
                puertas,
                numero_sala=sala_idx + 1,
                estado=estado,
                vidas_max=vidas_max,
            )
            return puertas, estado_pity
    estado_pity = actualizar_pity_tras_sala(
        estado_pity,
        puertas,
        numero_sala=sala_idx + 1,
        estado=estado,
        vidas_max=vidas_max,
    )
    return puertas, estado_pity


def _pools_filtro_contenido(pool: list[Pregunta]) -> dict[str, tuple]:
    return {
        "cursos_pool": cursos_del_pool(pool),
        "semestres_pool": semestres_del_pool(pool),
        "periodos_pool": periodos_del_pool(pool),
    }


def _reconstruir_puerta_con_preguntas(
    indice: int,
    *,
    plantilla,
    perfil_id: str | None,
    n_preg: int,
    numero_sala: int,
    sala_idx: int,
    materias_base: tuple[str, ...],
    materias_pool: tuple[str, ...],
    materias_puerta: tuple[str, ...],
    grupos_base: tuple[str, ...],
    grupos_pool: tuple[str, ...],
    pool_preguntas: list[Pregunta],
    n_salas: int,
    rng: random.Random,
    pity: PityPuertasEspecialesEscape,
    estado=None,
    vidas_max: int | None = None,
    permitir_pausas: bool = True,
) -> PuertaEscape:
    mods = generar_modificadores_puerta(
        numero_sala=numero_sala,
        rng=rng,
        indice_puerta=indice,
        pausas_usadas=frozenset(RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE),
        pity=pity,
        estado=estado,
        vidas_max=vidas_max,
        permitir_pausas=permitir_pausas,
    )
    if mods.sin_pregunta:
        n_preg = 0
        evento = instanciar_evento_contenido(
            evento_por_id("puerta_materia"),
            materias_pool=materias_base,
            grupos_pool=(),
            rng=rng,
            indice_puerta=sala_idx * 10 + indice,
            materia_preferida=materias_base[indice % len(materias_base)],
        )
    else:
        plantilla_usada = plantilla
        perfil_usado = perfil_id
        materia_pref = materias_puerta[indice] if indice < len(materias_puerta) else None
        opts = plantilla_usada.contenido_escape
        ambito = opts.ambito_efectivo if opts else "materia"
        pools_filtro = _pools_filtro_contenido(pool_preguntas)
        evento = instanciar_evento_contenido(
            plantilla_usada,
            materias_pool=materias_base if ambito == "materia" else materias_pool,
            grupos_pool=grupos_base if ambito == "grupo" else grupos_pool,
            rng=rng,
            indice_puerta=sala_idx * 10 + indice,
            materia_preferida=None if ambito != "materia" else materia_pref,
            perfil_id=perfil_usado,
            **pools_filtro,
        )
    puerta = PuertaEscape(
        indice=indice,
        n_preguntas=n_preg if not mods.sin_pregunta else 0,
        modificadores=mods,
        evento=evento,
    )
    return asegurar_puerta_viable(
        pool_preguntas,
        puerta,
        numero_sala=numero_sala,
        n_salas=n_salas,
        indice_puerta=indice,
        materias_pool=materias_base,
        grupos_pool=grupos_base,
    )


def _normalizar_puertas_tienda_escape(
    puertas: list[PuertaEscape],
    *,
    numero_sala: int,
    sala_idx: int,
    materias_base: tuple[str, ...],
    materias_pool: tuple[str, ...],
    materias_puerta: tuple[str, ...],
    grupos_base: tuple[str, ...],
    grupos_pool: tuple[str, ...],
    pool_preguntas: list[Pregunta],
    plantillas,
    tamanos: tuple[int, ...],
    n_salas: int,
    rng: random.Random,
    pity: PityPuertasEspecialesEscape,
    estado=None,
    vidas_max: int | None = None,
) -> None:
    """Quita tiendas inviables y restaura una puerta con preguntas (sin convertir en descanso)."""
    if estado is None:
        return
    from Comun.tienda_escape import puede_visitar_tienda_escape, puerta_es_tienda

    if puede_visitar_tienda_escape(numero_sala, estado, vidas_max=vidas_max):
        return
    for i, puerta in enumerate(puertas):
        if not puerta_es_tienda(puerta):
            continue
        plantilla, perfil_id = plantillas[i]
        puertas[i] = _reconstruir_puerta_con_preguntas(
            i,
            plantilla=plantilla,
            perfil_id=perfil_id,
            n_preg=tamanos[i],
            numero_sala=numero_sala,
            sala_idx=sala_idx,
            materias_base=materias_base,
            materias_pool=materias_pool,
            materias_puerta=materias_puerta,
            grupos_base=grupos_base,
            grupos_pool=grupos_pool,
            pool_preguntas=pool_preguntas,
            n_salas=n_salas,
            rng=rng,
            pity=pity,
            estado=estado,
            vidas_max=vidas_max,
        )


def _insertar_puerta_especial_escape(
    puertas: list[PuertaEscape],
    *,
    pausa_id: str,
    rng: random.Random,
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
    idx = rng.choice(candidatos)
    mods = combinar_modificadores_puerta((pausa,), numero_sala=numero_sala)
    evento = instanciar_evento_contenido(
        evento_por_id("puerta_materia"),
        materias_pool=materias_base,
        grupos_pool=(),
        rng=rng,
        indice_puerta=sala_idx * 10 + idx,
        materia_preferida=materias_base[idx % len(materias_base)],
    )
    puertas[idx] = replace(
        puertas[idx],
        n_preguntas=0,
        modificadores=mods,
        evento=evento,
    )


def _puerta_acepta_botin_hard_pity(puerta: PuertaEscape) -> bool:
    """Puertas donde el hard pity puede forzar botín (nunca tienda ni jefe)."""
    if puerta.es_jefe:
        return False
    if "tienda" in puerta.modificadores.eventos_ids:
        return False
    if any(eid in RASGOS_BOTIN_ESCAPE for eid in puerta.modificadores.eventos_ids):
        return False
    if puerta.modificadores.sin_pregunta:
        return "descanso" in puerta.modificadores.eventos_ids
    return True


def _mods_puerta_con_botin_anadido(
    puerta: PuertaEscape,
    botin: DefinicionEvento,
    *,
    numero_sala: int,
) -> ModificadoresPuerta:
    if puerta.modificadores.sin_pregunta:
        pausa = evento_por_id("descanso")
        rasgos: list[DefinicionEvento] = [pausa]
        for eid in puerta.modificadores.eventos_ids:
            if eid in RASGOS_BOTIN_ESCAPE:
                rasgos.append(evento_por_id(eid))
        rasgos.append(botin)
        return combinar_modificadores_puerta(tuple(rasgos), numero_sala=numero_sala)
    ev_ids = [
        eid
        for eid in puerta.modificadores.eventos_ids
        if eid not in RASGOS_BOTIN_ESCAPE
    ]
    rasgos = [evento_por_id(eid) for eid in ev_ids] + [botin]
    return combinar_modificadores_puerta(tuple(rasgos), numero_sala=numero_sala)


def _insertar_botin_en_puerta_escape(
    puertas: list[PuertaEscape],
    *,
    numero_sala: int,
    rng: random.Random,
    sala_idx: int,
) -> None:
    """Hard pity: al menos una puerta con botín (pregunta o descanso; nunca tienda)."""
    del sala_idx
    if any(
        any(eid in RASGOS_BOTIN_ESCAPE for eid in p.modificadores.eventos_ids)
        for p in puertas
    ):
        return
    candidatos = [i for i, p in enumerate(puertas) if _puerta_acepta_botin_hard_pity(p)]
    if not candidatos:
        return
    idx = rng.choice(candidatos)
    botin = elegir_botin_para_sala(numero_sala, rng)
    if botin is None:
        return
    puerta = puertas[idx]
    mods = _mods_puerta_con_botin_anadido(puerta, botin, numero_sala=numero_sala)
    puertas[idx] = replace(puerta, modificadores=mods)


def _crear_puerta_jefe_escape(
    indice: int,
    *,
    numero_sala: int,
    sala_idx: int,
    grupos_base: tuple[str, ...],
    grupos_pool: tuple[str, ...],
    pool_preguntas: list[Pregunta],
    n_salas: int,
    rng: random.Random,
    grupos_usados: set[str],
) -> PuertaEscape:
    dif_tipo = elegir_dificultad_jefe_escape(numero_sala, rng)
    perfil_id = perfil_id_para_dificultad_jefe(dif_tipo)
    perfil = perfil_materia_por_id(perfil_id)
    plantilla = definicion_grupo_con_perfil(perfil)
    candidatos = [g for g in grupos_base if g not in grupos_usados] or list(grupos_base)
    if not candidatos:
        candidatos = list(grupos_pool) or list(grupos_base)
    grupo = rng.choice(candidatos)
    grupos_usados.add(grupo)
    mods = generar_modificadores_puerta(
        numero_sala=numero_sala,
        rng=rng,
        indice_puerta=indice,
        pausas_usadas=frozenset(RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE),
        pity=None,
        permitir_pausas=False,
    )
    rasgos = [evento_por_id(eid) for eid in mods.eventos_ids]
    rasgos.extend(elegir_botines_jefe_escape(numero_sala, rng))
    mods = combinar_modificadores_puerta(tuple(rasgos), numero_sala=numero_sala)
    if mods.fin_partida_si_fallo:
        rasgos_limpios = [
            evento_por_id(eid) for eid in mods.eventos_ids if eid != "puerta_maldita"
        ]
        mods = combinar_modificadores_puerta(tuple(rasgos_limpios), numero_sala=numero_sala)
    evento = instanciar_evento_contenido(
        plantilla,
        materias_pool=(),
        grupos_pool=(grupo,),
        rng=rng,
        indice_puerta=sala_idx * 10 + indice,
        perfil_id=perfil_id,
    )
    puerta = PuertaEscape(
        indice=indice,
        n_preguntas=PREGUNTAS_POR_JEFE,
        modificadores=mods,
        evento=evento,
        es_jefe=True,
    )
    return asegurar_puerta_viable(
        pool_preguntas,
        puerta,
        numero_sala=numero_sala,
        n_salas=n_salas,
        indice_puerta=indice,
        materias_pool=(),
        grupos_pool=grupos_base or grupos_pool,
    )


def _construir_puertas_sala_jefe(
    sala_idx: int,
    *,
    materias_pool: tuple[str, ...],
    pool_preguntas: list[Pregunta],
    rng: random.Random,
    puertas_por_sala: int,
    n_salas: int,
    pity: PityPuertasEspecialesEscape,
) -> tuple[PuertaEscape, ...]:
    numero_sala = sala_idx + 1
    n_jefes = n_puertas_jefe_en_sala(numero_sala)
    grupos_pool = grupos_del_pool(pool_preguntas)
    grupos_base = grupos_viables_sala(
        pool_preguntas,
        grupos_pool,
        numero_sala=numero_sala,
        n_salas=n_salas,
    )
    materias_base = materias_viables_sala(
        pool_preguntas,
        materias_pool,
        numero_sala=numero_sala,
        n_salas=n_salas,
    )
    plantillas = elegir_plantillas_contenido_escape(puertas_por_sala, numero_sala, rng)
    materias_puerta = materias_distintas_puertas(materias_base, puertas_por_sala, rng)
    tamanos = tamanos_puerta_para_sala(
        sala_idx, n_salas=n_salas, puertas_por_sala=puertas_por_sala, rng=rng
    )

    puertas: list[PuertaEscape] = []
    grupos_usados: set[str] = set()
    for i in range(n_jefes):
        puertas.append(
            _crear_puerta_jefe_escape(
                i,
                numero_sala=numero_sala,
                sala_idx=sala_idx,
                grupos_base=grupos_base,
                grupos_pool=grupos_pool,
                pool_preguntas=pool_preguntas,
                n_salas=n_salas,
                rng=rng,
                grupos_usados=grupos_usados,
            )
        )

    n_normales = puertas_por_sala - n_jefes
    for j in range(n_normales):
        i = n_jefes + j
        plantilla, perfil_id = plantillas[i] if i < len(plantillas) else plantillas[-1]
        puertas.append(
            _reconstruir_puerta_con_preguntas(
                i,
                plantilla=plantilla,
                perfil_id=perfil_id,
                n_preg=tamanos[i] if i < len(tamanos) else 3,
                numero_sala=numero_sala,
                sala_idx=sala_idx,
                materias_base=materias_base,
                materias_pool=materias_pool,
                materias_puerta=materias_puerta,
                grupos_base=grupos_base,
                grupos_pool=grupos_pool,
                pool_preguntas=pool_preguntas,
                n_salas=n_salas,
                rng=rng,
                pity=pity,
                permitir_pausas=False,
            )
        )

    if debe_garantizar_botin_escape(pity, numero_sala):
        _insertar_botin_en_puerta_escape(
            puertas,
            numero_sala=numero_sala,
            rng=rng,
            sala_idx=sala_idx,
        )
    return tuple(puertas)


def _aplicar_hard_pity_puertas_especiales(
    puertas: list[PuertaEscape],
    *,
    pity: PityPuertasEspecialesEscape,
    numero_sala: int,
    rng: random.Random,
    sala_idx: int,
    materias_base: tuple[str, ...],
    estado=None,
    vidas_max: int | None = None,
) -> None:
    """Inserta descanso o tienda si el hard pity lo exige y aún no hay ninguno en la sala."""
    if sala_es_milestone_jefe(numero_sala):
        return
    if debe_garantizar_descanso_escape(pity, numero_sala):
        _insertar_puerta_especial_escape(
            puertas,
            pausa_id="descanso",
            rng=rng,
            sala_idx=sala_idx,
            numero_sala=numero_sala,
            materias_base=materias_base,
        )
    if debe_garantizar_tienda_escape(pity, numero_sala):
        tienda_viable = True
        if estado is not None:
            from Comun.tienda_escape import puede_visitar_tienda_escape

            tienda_viable = puede_visitar_tienda_escape(
                numero_sala, estado, vidas_max=vidas_max
            )
        if tienda_viable:
            _insertar_puerta_especial_escape(
                puertas,
                pausa_id="tienda",
                rng=rng,
                sala_idx=sala_idx,
                numero_sala=numero_sala,
                materias_base=materias_base,
            )
    if debe_garantizar_botin_escape(pity, numero_sala):
        _insertar_botin_en_puerta_escape(
            puertas,
            numero_sala=numero_sala,
            rng=rng,
            sala_idx=sala_idx,
        )


def _construir_puertas_sala(
    sala: SalaEscapeRoom,
    sala_idx: int,
    *,
    materias_pool: tuple[str, ...],
    pool_preguntas: list[Pregunta],
    rng: random.Random,
    puertas_por_sala: int,
    n_salas: int,
    pity: PityPuertasEspecialesEscape,
    estado=None,
    vidas_max: int | None = None,
) -> tuple[PuertaEscape, ...]:
    del sala
    numero_sala = sala_idx + 1
    if sala_es_milestone_jefe(numero_sala):
        return _construir_puertas_sala_jefe(
            sala_idx,
            materias_pool=materias_pool,
            pool_preguntas=pool_preguntas,
            rng=rng,
            puertas_por_sala=puertas_por_sala,
            n_salas=n_salas,
            pity=pity,
        )

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
            rng=rng,
            indice_puerta=i,
            pausas_usadas=frozenset(pausas_usadas),
            pity=pity,
            estado=estado,
            vidas_max=vidas_max,
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
                rng=rng,
                indice_puerta=sala_idx * 10 + i,
                materia_preferida=materias_base[i % len(materias_base)],
            )
        else:
            plantilla_usada = plantilla
            perfil_usado = perfil_id
            materia_pref = materias_puerta[i] if i < len(materias_puerta) else None
            opts = plantilla_usada.contenido_escape
            ambito = opts.ambito_efectivo if opts else "materia"
            pools_filtro = _pools_filtro_contenido(pool_preguntas)
            evento = instanciar_evento_contenido(
                plantilla_usada,
                materias_pool=materias_base if ambito == "materia" else materias_pool,
                grupos_pool=grupos_base if ambito == "grupo" else grupos_pool,
                rng=rng,
                indice_puerta=sala_idx * 10 + i,
                materia_preferida=None if ambito != "materia" else materia_pref,
                perfil_id=perfil_usado,
                **pools_filtro,
            )
        puerta = PuertaEscape(indice=i, n_preguntas=n_preg, modificadores=mods, evento=evento)
        puerta = asegurar_puerta_viable(
            pool_preguntas,
            puerta,
            numero_sala=numero_sala,
            n_salas=n_salas,
            indice_puerta=i,
            materias_pool=materias_base,
            grupos_pool=grupos_base,
        )
        puertas.append(puerta)
    _aplicar_hard_pity_puertas_especiales(
        puertas,
        pity=pity,
        numero_sala=numero_sala,
        rng=rng,
        sala_idx=sala_idx,
        materias_base=materias_base,
        estado=estado,
        vidas_max=vidas_max,
    )
    _normalizar_puertas_tienda_escape(
        puertas,
        numero_sala=numero_sala,
        sala_idx=sala_idx,
        materias_base=materias_base,
        materias_pool=materias_pool,
        materias_puerta=materias_puerta,
        grupos_base=grupos_base,
        grupos_pool=grupos_pool,
        pool_preguntas=pool_preguntas,
        plantillas=plantillas,
        tamanos=tamanos,
        n_salas=n_salas,
        rng=rng,
        pity=pity,
        estado=estado,
        vidas_max=vidas_max,
    )
    return tuple(puertas)


def regenerar_puertas_sala_escape(
    sala: SalaEscapeRoom,
    sala_idx: int,
    *,
    materias_pool: tuple[str, ...],
    pool_preguntas: list[Pregunta],
    rng: random.Random,
    puertas_por_sala: int = PUERTAS_POR_SALA,
    n_salas: int = SALAS_DEFECTO,
    pity: PityPuertasEspecialesEscape | None = None,
    estado=None,
    vidas_max: int | None = None,
) -> tuple[PuertaEscape, ...]:
    """Reroll de puertas sin avanzar el pity de salas."""
    del pity
    puertas: tuple[PuertaEscape, ...] = ()
    for _ in range(64):
        puertas = _construir_puertas_sala(
            sala,
            sala_idx,
            materias_pool=materias_pool,
            pool_preguntas=pool_preguntas,
            rng=rng,
            puertas_por_sala=puertas_por_sala,
            n_salas=n_salas,
            pity=None,
            estado=estado,
            vidas_max=vidas_max,
        )
        firmas = [firma_puerta_escape(p) for p in puertas]
        if len(set(firmas)) == len(firmas):
            return puertas
    return puertas


def quitar_maldicion_puertas_sala(
    puertas: tuple[PuertaEscape, ...],
    *,
    numero_sala: int,
) -> tuple[PuertaEscape, ...]:
    """Elimina el rasgo maldito de cada puerta de la sala."""
    resultado: list[PuertaEscape] = []
    for puerta in puertas:
        if not puerta.modificadores.fin_partida_si_fallo:
            resultado.append(puerta)
            continue
        rasgos = [
            evento_por_id(eid)
            for eid in puerta.modificadores.eventos_ids
            if eid != RASGO_PUERTA_MALDITA
        ]
        mods = combinar_modificadores_puerta(tuple(rasgos), numero_sala=numero_sala)
        resultado.append(replace(puerta, modificadores=mods))
    return tuple(resultado)


def semilla_partida_escape() -> int:
    """Semilla aleatoria al iniciar cada partida de escape room."""
    from Comun.semillas import semilla_partida_aleatoria

    return semilla_partida_aleatoria()
