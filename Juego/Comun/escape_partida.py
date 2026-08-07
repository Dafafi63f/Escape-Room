#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pool del escape room (banco revisado o ampliado).

Responsabilidades
-----------------
* **Puerta**: nº de preguntas y rasgos de juego (cronómetros, niebla, puntos dobles…).
* **Evento de contenido**: materia, grupo, dificultad, tipo de pregunta.
* **Escalada (sala)**: complejidad global progresiva (inicio baja, medio amplio, final alta).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, cast

from Comun.reglas import complejidad_pregunta, niveles_en_pool
from Comun.config_historia import etiqueta_grupo_tematico
from Comun.eventos_partida import (
    EventoContenidoInstanciado,
    ModificadoresPuerta,
    RASGOS_BOTIN_ESCAPE,
    RASGOS_RECOMPENSA_VIDAS_ESCAPE,
    evento_por_id,
    instanciar_evento_contenido,
)
from Comun.modelos import BancoPreguntas, Pregunta
from Comun.preguntas_resistencia import pool_resistencia_desde_dataset

if TYPE_CHECKING:
    from Comun.escape_room import PuertaEscape

__all__ = [
    "CriteriosPoolPuerta",
    "CriteriosSeleccionPool",
    "FiltroContenidoEvento",
    "FiltroPoolEscalada",
    "ReglasJuegoDesafio",
    "asegurar_puerta_viable",
    "aplicar_bonificacion_completar",
    "bonificacion_completar_escape",
    "combinar_criterios_seleccion_pool",
    "construir_pool_escape",
    "contar_candidatas_puerta",
    "criterios_pool_puerta",
    "filtro_pool_escalada",
    "grupos_del_pool",
    "grupos_viables_sala",
    "cursos_viables_sala",
    "semestres_viables_sala",
    "periodos_viables_sala",
    "plantilla_bloque_admite_jefe",
    "ambitos_jefe_viables_milestone",
    "materias_del_grupo",
    "materias_del_pool",
    "materias_viables_sala",
    "puerta_es_jefe",
    "puerta_es_maldita",
    "procesar_fallo_puerta_maldita",
    "reglas_juego_desafio",
    "reglas_partida_desde_desafio",
    "seleccionar_preguntas_desafio",
    "tiempo_pregunta_escape_por_defecto",
    "acotar_tiempo_pregunta_escape",
    "aplicar_penalizacion_extra_fallo_puerta",
    "debe_abandonar_puerta_por_perdida_vida",
    "etiqueta_penalizacion_fallo_puerta",
    "puerta_tiene_bloque_preguntas",
    "sufijo_avance_sala_tras_abandono",
    "sufijo_mensaje_fallo_puerta",
    "vidas_perdidas_fallo_puerta",
    "TIEMPO_PREGUNTA_MIN_ESCAPE",
    "VIDAS_MAX_ABSOLUTO_ESCAPE",
    "VIDAS_MAX_ESCAPE",
]

_DIFICULTADES_TODAS = frozenset({"Facil", "Media", "Dificil"})
_RASGO_CLASICA = "Clásica"
_PLANTILLA_BALANCEADA = "puerta_materia"
_TAMANOS_REDUCCION = (3, 5)
VIDAS_MAX_ESCAPE = 3
VIDAS_MAX_ABSOLUTO_ESCAPE = 9
TIEMPO_PREGUNTA_MIN_ESCAPE = 20
VIDAS_FALLO_PUERTA_ESCAPE = 1
VIDAS_FALLO_PUERTA_JEFE_ESCAPE = 2


@dataclass(frozen=True)
class CriteriosPoolPuerta:
    n_preguntas: int


@dataclass(frozen=True)
class FiltroPoolEscalada:
    dificultades_permitidas: frozenset[str]
    min_complejidad: int
    max_complejidad: int


@dataclass(frozen=True)
class FiltroContenidoEvento:
    materia: str | None
    grupo: str | None
    curso: str | None
    semestre: str | None
    dificultades_permitidas: frozenset[str] | None
    tipos_permitidos: frozenset[str] | None


@dataclass(frozen=True)
class CriteriosSeleccionPool:
    n_preguntas: int
    materia: str | None
    grupo: str | None
    curso: str | None
    semestre: str | None
    dificultades_permitidas: frozenset[str]
    min_complejidad: int
    max_complejidad: int
    tipos_permitidos: frozenset[str] | None


@dataclass(frozen=True)
class ReglasJuegoDesafio:
    tiempo_pregunta_seg: int | None
    tiempo_puerta_seg: int | None
    opciones_ocultas: int
    multiplicador_puntos: int


@dataclass(frozen=True)
class BonificacionCompletarEscape:
    """Recompensa al superar un bloque de preguntas (solo esa puerta; no arrastra)."""

    delta_vidas: int = 0
    delta_vidas_max: int = 0
    etiqueta: str = ""
    en_descanso: bool = False
    powerups: tuple[tuple[str, int], ...] = ()

    @property
    def tiene_recompensa(self) -> bool:
        return (
            self.delta_vidas > 0
            or self.delta_vidas_max > 0
            or bool(self.powerups)
        )

    @property
    def mensaje(self) -> str:
        if not self.tiene_recompensa:
            return ""
        partes: list[str] = []
        if self.delta_vidas_max > 0:
            n = self.delta_vidas_max
            txt = "1 al máximo" if n == 1 else f"{n} al máximo"
            partes.append(f"💖 Corazón máximo: +{txt} de vidas.")
        if self.delta_vidas > 0:
            txt = self._texto_vidas()
            if self.en_descanso:
                partes.append(f"❤️ Botín: +{txt}.")
            elif self.etiqueta:
                partes.append(f"❤️ {self.etiqueta}: recuperas {txt}.")
            else:
                partes.append(f"❤️ Puerta superada: recuperas {txt}.")
        if self.powerups:
            from Comun.emojis_escape import EMOJI_BOTIN_ESCAPE
            from Comun.resistencia_motor import etiqueta_powerup

            for pid, cant in self.powerups:
                nom = etiqueta_powerup(pid)
                if cant == 1:
                    partes.append(f"{EMOJI_BOTIN_ESCAPE} Objeto: {nom}.")
                else:
                    partes.append(f"{EMOJI_BOTIN_ESCAPE} Objetos: {cant}× {nom}.")
        return " ".join(partes)

    def _texto_vidas(self) -> str:
        n = self.delta_vidas
        return "1 vida" if n == 1 else f"{n} vidas"


def puerta_es_jefe(puerta: PuertaEscape) -> bool:
    """Bloque de jefe escape: 10 preguntas en puerta de bloque (grupo/curso/…)."""
    return puerta.es_jefe


def puerta_es_maldita(puerta: PuertaEscape | None) -> bool:
    """Puerta con fin de partida al fallar cualquier pregunta."""
    if puerta is None:
        return False
    return bool(puerta.modificadores.fin_partida_si_fallo)


@dataclass(frozen=True)
class ResultadoFalloPuertaMaldita:
    fin_partida: bool
    consumir_proteccion: bool
    mensaje_extra: str


def procesar_fallo_puerta_maldita(
    puerta: PuertaEscape | None,
    *,
    proteccion_activa: bool,
) -> ResultadoFalloPuertaMaldita | None:
    """Tras un fallo real (sin escudo/2.ª oportunidad). None si la puerta no es maldita."""
    if not puerta_es_maldita(puerta):
        return None
    if proteccion_activa:
        return ResultadoFalloPuertaMaldita(
            fin_partida=False,
            consumir_proteccion=True,
            mensaje_extra=" Sello de purga roto: pierdes vida y abandonas la puerta.",
        )
    return ResultadoFalloPuertaMaldita(
        fin_partida=True,
        consumir_proteccion=False,
        mensaje_extra=" Puerta maldita: fin de partida.",
    )


def puerta_tiene_bloque_preguntas(puerta: PuertaEscape | None) -> bool:
    if puerta is None:
        return False
    return not puerta.modificadores.sin_pregunta and puerta.n_preguntas > 0


def debe_abandonar_puerta_por_perdida_vida(
    puerta: PuertaEscape | None,
    *,
    vidas_antes: int | None,
    vidas_despues: int | None,
    reintentar: bool,
) -> bool:
    """Pierdes vida en una puerta con preguntas → abandonas y avanzas de sala."""
    if reintentar or not puerta_tiene_bloque_preguntas(puerta):
        return False
    if vidas_antes is None or vidas_despues is None:
        return False
    return vidas_despues < vidas_antes


def vidas_perdidas_fallo_puerta(puerta: PuertaEscape) -> int:
    """Vidas que se pierden al fallar una pregunta de la puerta (abandona el bloque)."""
    if puerta.modificadores.sin_pregunta or puerta.n_preguntas <= 0:
        return 0
    if puerta_es_jefe(puerta):
        return VIDAS_FALLO_PUERTA_JEFE_ESCAPE
    return VIDAS_FALLO_PUERTA_ESCAPE


def aplicar_penalizacion_extra_fallo_puerta(estado, puerta: PuertaEscape | None) -> int:
    """Resta vidas adicionales tras ``evaluar_respuesta`` (que ya resta 1)."""
    if puerta is None:
        return 0
    extra = vidas_perdidas_fallo_puerta(puerta) - 1
    if extra <= 0 or estado.vidas_restantes is None:
        return 0
    estado.vidas_restantes = max(0, estado.vidas_restantes - extra)
    return extra


def etiqueta_penalizacion_fallo_puerta(puerta: PuertaEscape) -> str:
    n = vidas_perdidas_fallo_puerta(puerta)
    if n <= 0:
        return ""
    if n == 1:
        return "Al fallar una pregunta: −1 vida. Pasas a la siguiente sala."
    return f"Al fallar una pregunta: −{n} vidas. Pasas a la siguiente sala."


def sufijo_avance_sala_tras_abandono() -> str:
    return " Pasas a la siguiente sala."


def sufijo_mensaje_fallo_puerta(puerta: PuertaEscape) -> str:
    n = vidas_perdidas_fallo_puerta(puerta)
    if n <= 1:
        return ""
    return f" (pierdes {n} vidas, puerta jefe)"


def mensaje_feedback_puerta_sin_pregunta(puerta: PuertaEscape) -> str:
    """Texto al elegir una puerta sin bloque de preguntas."""
    from Comun.eventos_partida import evento_por_id, evento_sin_pregunta_escape
    from Comun.tienda_escape import puerta_es_tienda

    if puerta_es_tienda(puerta):
        ev_tienda = evento_por_id("tienda")
        return f"{ev_tienda.nombre}: {ev_tienda.descripcion}"
    ev = evento_sin_pregunta_escape(puerta.modificadores)
    if ev is None:
        return "💤 Avanzas sin preguntas."
    return f"{ev.emoji} {ev.nombre}: avanzas sin preguntas."


def bonificacion_completar_escape(puerta: PuertaEscape) -> BonificacionCompletarEscape:
    """Vidas u objetos extra al superar la puerta sin fallar (botín, corazón máximo o jefe)."""

    def _bonus_botin() -> tuple[int, int]:
        delta = 0
        delta_max = 0
        for eid in puerta.modificadores.eventos_ids:
            if eid not in RASGOS_RECOMPENSA_VIDAS_ESCAPE:
                continue
            ev = evento_por_id(eid)
            delta += ev.modificadores.delta_vidas_al_completar
            delta_max += ev.modificadores.delta_vidas_max_al_completar
        if delta == 0 and delta_max == 0:
            delta = puerta.modificadores.delta_vidas_al_completar
            delta_max = puerta.modificadores.delta_vidas_max_al_completar
        return delta, delta_max

    def _powerups_botin() -> tuple[tuple[str, int], ...]:
        acum: dict[str, int] = {}
        for eid in puerta.modificadores.eventos_ids:
            if eid not in RASGOS_BOTIN_ESCAPE:
                continue
            pid = evento_por_id(eid).modificadores.powerup_al_completar
            if pid:
                acum[pid] = acum.get(pid, 0) + 1
        return tuple(sorted(acum.items()))

    powerups = _powerups_botin()

    if puerta.modificadores.sin_pregunta:
        tiene_vidas = any(
            eid in RASGOS_RECOMPENSA_VIDAS_ESCAPE
            for eid in puerta.modificadores.eventos_ids
        )
        if tiene_vidas or powerups:
            delta, delta_max = _bonus_botin() if tiene_vidas else (0, 0)
            return BonificacionCompletarEscape(
                delta_vidas=delta,
                delta_vidas_max=delta_max,
                etiqueta="Botín de la puerta",
                en_descanso=True,
                powerups=powerups,
            )
        return BonificacionCompletarEscape()
    if puerta.n_preguntas <= 0:
        return BonificacionCompletarEscape()
    delta = 0
    delta_max = 0
    etiqueta = ""
    if any(
        eid in RASGOS_RECOMPENSA_VIDAS_ESCAPE for eid in puerta.modificadores.eventos_ids
    ):
        delta, delta_max = _bonus_botin()
        etiqueta = "Botín de la puerta"
    if puerta_es_jefe(puerta):
        delta = max(delta, 2)
        etiqueta = "Puerta jefe superada"
    return BonificacionCompletarEscape(
        delta_vidas=delta,
        delta_vidas_max=delta_max,
        etiqueta=etiqueta,
        powerups=powerups,
    )


def puntos_extra_mult_desafio(
    delta_base: int,
    *,
    acierto: bool,
    mult: int,
) -> int:
    """Puntos adicionales por multiplicador de puerta (solo aciertos)."""
    if not acierto or mult <= 1:
        return 0
    return delta_base * (mult - 1)


def mensaje_acierto_desafio(
    delta_base: int,
    *,
    mult: int,
) -> str:
    extra = puntos_extra_mult_desafio(delta_base, acierto=True, mult=mult)
    total = delta_base + extra
    if mult > 1:
        return f"Correcto (+{total} pts, ×{mult} puerta)"
    return f"Correcto (+{total} puntos)"


def aplicar_bonificacion_completar(
    estado,
    bonus: BonificacionCompletarEscape,
    *,
    vidas_max: int = VIDAS_MAX_ESCAPE,
) -> tuple[int, int]:
    """Aplica botín/jefe: devuelve (vidas ganadas, nuevo tope de vidas)."""
    nuevo_max = vidas_max
    if bonus.delta_vidas_max > 0:
        nuevo_max = max(
            VIDAS_MAX_ESCAPE,
            min(VIDAS_MAX_ABSOLUTO_ESCAPE, vidas_max + bonus.delta_vidas_max),
        )
        if estado.vidas_restantes is not None and estado.vidas_restantes > nuevo_max:
            estado.vidas_restantes = nuevo_max
    if bonus.delta_vidas <= 0 or estado.vidas_restantes is None:
        return 0, nuevo_max
    antes = estado.vidas_restantes
    estado.vidas_restantes = min(nuevo_max, antes + bonus.delta_vidas)
    return estado.vidas_restantes - antes, nuevo_max


def construir_pool_escape(
    preguntas_dataset: list[Pregunta],
    *,
    banco: BancoPreguntas = BancoPreguntas.DATASET,
    path_csv=None,
    path_plantillas=None,
    materias_meta=None,
) -> list[Pregunta]:
    """Pool del escape; por defecto solo dataset revisado."""
    from pathlib import Path

    if banco == BancoPreguntas.DATASET:
        fuente = preguntas_dataset
    elif banco == BancoPreguntas.PLANTILLAS_TODO:
        if path_csv is None or path_plantillas is None or materias_meta is None:
            raise ValueError("Falta ruta o metadatos para el banco ampliado.")
        from Comun.datos import cargar_banco_todo

        fuente = cargar_banco_todo(
            Path(path_csv), Path(path_plantillas), materias_meta
        )
    else:
        raise ValueError(f"Banco no soportado en escape: {banco}")
    pool = pool_resistencia_desde_dataset(fuente)
    return sorted(pool, key=lambda p: (p.materia, p.texto, p.correcta))


def materias_del_pool(pool: list[Pregunta]) -> tuple[str, ...]:
    return tuple(sorted({p.materia for p in pool if p.materia}))


def grupos_del_pool(pool: list[Pregunta]) -> tuple[str, ...]:
    return tuple(sorted({p.grupo for p in pool if p.grupo}))


def materias_del_grupo(pool: list[Pregunta], grupo: str) -> tuple[str, ...]:
    return tuple(sorted({p.materia for p in pool if p.grupo == grupo and p.materia}))


def _pool_filtrado_escalada(
    pool: list[Pregunta],
    escalada: FiltroPoolEscalada,
    *,
    grupo: str | None = None,
    materia: str | None = None,
) -> list[Pregunta]:
    """Subconjunto del pool (grupo o materia) acotado por complejidad global de la sala."""
    out: list[Pregunta] = []
    for p in pool:
        if grupo and p.grupo != grupo:
            continue
        if materia and p.materia != materia:
            continue
        cx = complejidad_pregunta(p)
        if cx < escalada.min_complejidad or cx > escalada.max_complejidad:
            continue
        out.append(p)
    return out


def filtro_pool_escalada(
    numero_sala: int,
    *,
    n_salas: int,
    pool: list[Pregunta],
    grupo: str | None = None,
) -> FiltroPoolEscalada:
    """Complejidad global por fase: inicio (solo baja), medio (todo), final (solo alta).

    Si ``grupo`` está definido, los niveles se calculan solo con preguntas de ese grupo.
    """
    ref_pool = (
        [p for p in pool if p.grupo == grupo]
        if grupo
        else pool
    )
    niveles = sorted(niveles_en_pool(ref_pool if ref_pool else pool))
    if not niveles:
        return FiltroPoolEscalada(
            dificultades_permitidas=_DIFICULTADES_TODAS,
            min_complejidad=1,
            max_complejidad=99,
        )

    min_nivel, max_nivel = niveles[0], niveles[-1]
    if n_salas <= 1:
        t = 0.0
    else:
        t = (numero_sala - 1) / max(1, n_salas - 1)

    if t < 1 / 3:
        cx_min = cx_max = min_nivel
    elif t < 2 / 3:
        cx_min, cx_max = min_nivel, max_nivel
    else:
        if len(niveles) >= 2:
            cx_min = niveles[-2]
        else:
            cx_min = max_nivel
        cx_max = max_nivel

    return FiltroPoolEscalada(
        dificultades_permitidas=_DIFICULTADES_TODAS,
        min_complejidad=cx_min,
        max_complejidad=cx_max,
    )


def criterios_pool_puerta(puerta: PuertaEscape) -> CriteriosPoolPuerta:
    return CriteriosPoolPuerta(n_preguntas=puerta.n_preguntas)


def filtro_contenido_evento(evento: EventoContenidoInstanciado) -> FiltroContenidoEvento:
    return FiltroContenidoEvento(
        materia=evento.materia,
        grupo=evento.grupo,
        curso=evento.curso,
        semestre=evento.semestre,
        dificultades_permitidas=evento.dificultades_permitidas,
        tipos_permitidos=evento.tipos_permitidos,
    )


def combinar_criterios_seleccion_pool(
    puerta: CriteriosPoolPuerta,
    escalada: FiltroPoolEscalada,
    contenido: FiltroContenidoEvento,
) -> CriteriosSeleccionPool:
    permitidas = escalada.dificultades_permitidas
    if contenido.dificultades_permitidas is not None:
        inter = frozenset(permitidas & contenido.dificultades_permitidas)
        permitidas = inter if inter else contenido.dificultades_permitidas
    return CriteriosSeleccionPool(
        n_preguntas=puerta.n_preguntas,
        materia=contenido.materia,
        grupo=contenido.grupo,
        curso=contenido.curso,
        semestre=contenido.semestre,
        dificultades_permitidas=permitidas,
        min_complejidad=escalada.min_complejidad,
        max_complejidad=escalada.max_complejidad,
        tipos_permitidos=contenido.tipos_permitidos,
    )


def acotar_tiempo_pregunta_escape(seg: int | None) -> int | None:
    """Suelo de tiempo por pregunta en escape (resistencia no aplica este límite)."""
    if seg is None:
        return None
    return max(TIEMPO_PREGUNTA_MIN_ESCAPE, seg)


def tiempo_pregunta_escape_por_defecto(numero_sala: int, n_salas: int) -> int | None:
    """Tiempo por pregunta sin rasgo explícito: sube la presión sin llegar al extremo de resistencia."""
    if n_salas <= 1 or numero_sala <= 0:
        return None
    t = (numero_sala - 1) / max(1, n_salas - 1)
    if t < 0.4:
        return None
    if t < 0.7:
        return 50
    if t < 0.88:
        return 35
    return TIEMPO_PREGUNTA_MIN_ESCAPE


def reglas_juego_desafio(
    puerta: PuertaEscape,
    *,
    numero_sala: int,
    n_salas: int = 30,
) -> ReglasJuegoDesafio:
    mods = puerta.modificadores
    tiempo_preg = mods.tiempo_pregunta_seg
    tiempo_puerta = mods.tiempo_puerta_seg
    if tiempo_preg is None and tiempo_puerta is None:
        tiempo_preg = tiempo_pregunta_escape_por_defecto(numero_sala, n_salas)
    if tiempo_preg is not None:
        tiempo_preg = acotar_tiempo_pregunta_escape(tiempo_preg)
    return ReglasJuegoDesafio(
        tiempo_pregunta_seg=tiempo_preg,
        tiempo_puerta_seg=tiempo_puerta,
        opciones_ocultas=mods.opciones_ocultas,
        multiplicador_puntos=mods.multiplicador_puntos,
    )


def reglas_partida_desde_desafio(reglas_base, reglas: ReglasJuegoDesafio):
    """Aplica reglas de puerta; ``tiempo_total_seg`` es solo el cronómetro de bloque de la puerta."""
    return replace(
        reglas_base,
        tiempo_por_pregunta_seg=reglas.tiempo_pregunta_seg,
        tiempo_total_seg=reglas.tiempo_puerta_seg,
    )


def _criterios_desafio(
    puerta: PuertaEscape,
    *,
    numero_sala: int,
    n_salas: int,
    pool: list[Pregunta],
) -> CriteriosSeleccionPool:
    grupo = puerta.evento.grupo
    return combinar_criterios_seleccion_pool(
        criterios_pool_puerta(puerta),
        filtro_pool_escalada(
            numero_sala,
            n_salas=n_salas,
            pool=pool,
            grupo=grupo,
        ),
        filtro_contenido_evento(puerta.evento),
    )


def _pregunta_cumple_contenido(p: Pregunta, criterios: CriteriosSeleccionPool) -> bool:
    if criterios.materia and p.materia != criterios.materia:
        return False
    if criterios.grupo and p.grupo != criterios.grupo:
        return False
    if criterios.curso and p.curso != criterios.curso:
        return False
    if criterios.semestre and p.semestre != criterios.semestre:
        return False
    if criterios.tipos_permitidos and p.tipo not in criterios.tipos_permitidos:
        return False
    if p.dificultad not in criterios.dificultades_permitidas:
        return False
    cx = complejidad_pregunta(p)
    if cx < criterios.min_complejidad or cx > criterios.max_complejidad:
        return False
    return True


def _indices_candidatas(
    pool: list[Pregunta],
    criterios: CriteriosSeleccionPool,
    usadas: set[int],
) -> list[int]:
    candidatas: list[int] = []
    for idx in range(len(pool)):
        if idx in usadas:
            continue
        if _pregunta_cumple_contenido(pool[idx], criterios):
            candidatas.append(idx)
    return candidatas


def _criterios_sin_filtro_complejidad(criterios: CriteriosSeleccionPool) -> CriteriosSeleccionPool:
    return cast(CriteriosSeleccionPool, replace(criterios, min_complejidad=1, max_complejidad=99))


def _indices_por_dificultad(
    pool: list[Pregunta],
    indices: list[int],
    dificultad: str,
) -> list[int]:
    return [i for i in indices if pool[i].dificultad == dificultad]


def _seleccionar_indices_diversificando_dificultad(
    pool: list[Pregunta],
    candidatas: list[int],
    n: int,
    criterios: CriteriosSeleccionPool,
    usadas: set[int],
    rng: random.Random,
) -> list[int]:
    """Al menos una por dificultad del perfil con stock; el resto al azar (sin orden fijo)."""
    objetivo = criterios.dificultades_permitidas
    if len(objetivo) <= 1:
        return rng.sample(candidatas, n)

    relajadas = _indices_candidatas(
        pool, _criterios_sin_filtro_complejidad(criterios), usadas
    )
    elegidos: list[int] = []
    bloqueados = set(usadas)

    orden = list(objetivo)
    rng.shuffle(orden)
    for dif in orden:
        if len(elegidos) >= n:
            break
        stock = [i for i in _indices_por_dificultad(pool, candidatas, dif) if i not in bloqueados]
        if not stock:
            stock = [
                i
                for i in _indices_por_dificultad(pool, relajadas, dif)
                if i not in bloqueados
            ]
        if not stock:
            continue
        idx = rng.choice(stock)
        elegidos.append(idx)
        bloqueados.add(idx)

    restantes = [i for i in candidatas if i not in bloqueados]
    faltan = n - len(elegidos)
    if faltan > len(restantes):
        restantes = [i for i in relajadas if i not in bloqueados]
    if faltan > 0:
        elegidos.extend(rng.sample(restantes, faltan))
    return elegidos


def contar_candidatas_puerta(
    pool: list[Pregunta],
    puerta: PuertaEscape,
    *,
    numero_sala: int,
    n_salas: int,
    usadas: set[int] | None = None,
) -> int:
    if puerta.modificadores.sin_pregunta or puerta.n_preguntas <= 0:
        return puerta.n_preguntas
    criterios = _criterios_desafio(
        puerta, numero_sala=numero_sala, n_salas=n_salas, pool=pool
    )
    return len(_indices_candidatas(pool, criterios, usadas or set()))


def _devolver_viables_o_pool(
    viables: list,
    pool_completo: tuple,
    min_preguntas: int,
) -> tuple:
    if viables:
        return tuple(viables)
    if min_preguntas <= 3:
        return pool_completo
    return ()


def _contar_candidatas_foco_bloque(
    pool: list[Pregunta],
    evento: EventoContenidoInstanciado,
    *,
    numero_sala: int,
    n_salas: int,
    min_preguntas: int,
) -> int:
    from Comun.escape_room import PuertaEscape

    puerta = PuertaEscape(
        indice=0,
        n_preguntas=min_preguntas,
        modificadores=ModificadoresPuerta(),
        evento=evento,
    )
    return contar_candidatas_puerta(
        pool, puerta, numero_sala=numero_sala, n_salas=n_salas
    )


def materias_viables_sala(
    pool: list[Pregunta],
    materias_pool: tuple[str, ...],
    *,
    numero_sala: int,
    n_salas: int,
    min_preguntas: int = 3,
) -> tuple[str, ...]:
    """Materias con al menos ``min_preguntas`` candidatas en la escalada de la sala."""
    from Comun.escape_room import PuertaEscape

    viables: list[str] = []
    for materia in materias_pool:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id(_PLANTILLA_BALANCEADA),
            materia=materia,
        )
        puerta = PuertaEscape(
            indice=0,
            n_preguntas=min_preguntas,
            modificadores=ModificadoresPuerta(),
            evento=evento,
        )
        if contar_candidatas_puerta(
            pool, puerta, numero_sala=numero_sala, n_salas=n_salas
        ) >= min_preguntas:
            viables.append(materia)
    return _devolver_viables_o_pool(viables, materias_pool, min_preguntas)


def grupos_viables_sala(
    pool: list[Pregunta],
    grupos_pool: tuple[str, ...],
    *,
    numero_sala: int,
    n_salas: int,
    min_preguntas: int = 3,
) -> tuple[str, ...]:
    """Grupos con al menos ``min_preguntas`` candidatas en la escalada de la sala."""
    viables: list[str] = []
    plantilla = evento_por_id("puerta_grupo")
    for grupo in grupos_pool:
        evento = EventoContenidoInstanciado(definicion=plantilla, grupo=grupo)
        if _contar_candidatas_foco_bloque(
            pool,
            evento,
            numero_sala=numero_sala,
            n_salas=n_salas,
            min_preguntas=min_preguntas,
        ) >= min_preguntas:
            viables.append(grupo)
    return _devolver_viables_o_pool(viables, grupos_pool, min_preguntas)


def cursos_viables_sala(
    pool: list[Pregunta],
    cursos_pool: tuple[str, ...],
    *,
    numero_sala: int,
    n_salas: int,
    min_preguntas: int = 3,
) -> tuple[str, ...]:
    """Cursos con al menos ``min_preguntas`` candidatas en la escalada de la sala."""
    viables: list[str] = []
    plantilla = evento_por_id("puerta_curso")
    for curso in cursos_pool:
        evento = EventoContenidoInstanciado(definicion=plantilla, curso=curso)
        if _contar_candidatas_foco_bloque(
            pool,
            evento,
            numero_sala=numero_sala,
            n_salas=n_salas,
            min_preguntas=min_preguntas,
        ) >= min_preguntas:
            viables.append(curso)
    return _devolver_viables_o_pool(viables, cursos_pool, min_preguntas)


def semestres_viables_sala(
    pool: list[Pregunta],
    semestres_pool: tuple[str, ...],
    *,
    numero_sala: int,
    n_salas: int,
    min_preguntas: int = 3,
) -> tuple[str, ...]:
    """Semestres con al menos ``min_preguntas`` candidatas en la escalada de la sala."""
    viables: list[str] = []
    plantilla = evento_por_id("puerta_semestre")
    for semestre in semestres_pool:
        evento = EventoContenidoInstanciado(definicion=plantilla, semestre=semestre)
        if _contar_candidatas_foco_bloque(
            pool,
            evento,
            numero_sala=numero_sala,
            n_salas=n_salas,
            min_preguntas=min_preguntas,
        ) >= min_preguntas:
            viables.append(semestre)
    return _devolver_viables_o_pool(viables, semestres_pool, min_preguntas)


def periodos_viables_sala(
    pool: list[Pregunta],
    periodos_pool: tuple[tuple[str, str], ...],
    *,
    numero_sala: int,
    n_salas: int,
    min_preguntas: int = 3,
) -> tuple[tuple[str, str], ...]:
    """Periodos con al menos ``min_preguntas`` candidatas en la escalada de la sala."""
    viables: list[tuple[str, str]] = []
    plantilla = evento_por_id("puerta_periodo")
    for curso, semestre in periodos_pool:
        evento = EventoContenidoInstanciado(
            definicion=plantilla, curso=curso, semestre=semestre
        )
        if _contar_candidatas_foco_bloque(
            pool,
            evento,
            numero_sala=numero_sala,
            n_salas=n_salas,
            min_preguntas=min_preguntas,
        ) >= min_preguntas:
            viables.append((curso, semestre))
    return _devolver_viables_o_pool(viables, periodos_pool, min_preguntas)


def plantilla_bloque_admite_jefe(
    pool: list[Pregunta],
    plantilla,
    *,
    numero_sala: int,
    n_salas: int,
    min_preguntas: int,
    grupos_pool: tuple[str, ...] = (),
    cursos_pool: tuple[str, ...] = (),
    semestres_pool: tuple[str, ...] = (),
    periodos_pool: tuple[tuple[str, str], ...] = (),
) -> bool:
    """True si algún foco de la plantilla bloque tiene al menos ``min_preguntas`` candidatas."""
    from Comun.eventos_partida import OpcionesContenidoEscape, plantilla_lleva_perfil_materia

    if plantilla_lleva_perfil_materia(plantilla):
        return False
    opts = plantilla.contenido_escape or OpcionesContenidoEscape()
    ambito = opts.ambito_efectivo
    if ambito == "grupo":
        return bool(
            grupos_viables_sala(
                pool,
                grupos_pool,
                numero_sala=numero_sala,
                n_salas=n_salas,
                min_preguntas=min_preguntas,
            )
        )
    if ambito == "curso":
        return bool(
            cursos_viables_sala(
                pool,
                cursos_pool,
                numero_sala=numero_sala,
                n_salas=n_salas,
                min_preguntas=min_preguntas,
            )
        )
    if ambito == "semestre":
        return bool(
            semestres_viables_sala(
                pool,
                semestres_pool,
                numero_sala=numero_sala,
                n_salas=n_salas,
                min_preguntas=min_preguntas,
            )
        )
    if ambito == "periodo":
        return bool(
            periodos_viables_sala(
                pool,
                periodos_pool,
                numero_sala=numero_sala,
                n_salas=n_salas,
                min_preguntas=min_preguntas,
            )
        )
    return False


def ambitos_jefe_viables_milestone(
    pool: list[Pregunta],
    *,
    numero_sala: int,
    n_salas: int,
    min_preguntas: int,
) -> tuple[str, ...]:
    """Ámbitos de filtro amplio con al menos un bloque viable para jefe (10 preguntas)."""
    from Comun.eventos_partida import (
        _AMBITOS_FILTRO_AMPLIO,
        _ambitos_amplio_disponibles,
        evento_por_id,
        pools_bloque_del_pool,
    )
    from Comun.jefe_partida import PREGUNTAS_POR_JEFE

    min_j = min_preguntas if min_preguntas > 0 else PREGUNTAS_POR_JEFE
    pools = pools_bloque_del_pool(pool)
    disponibles = set(_ambitos_amplio_disponibles(numero_sala) or ["grupo"])
    viables: list[str] = []
    for ambito, _, plantilla_id in _AMBITOS_FILTRO_AMPLIO:
        if ambito not in disponibles:
            continue
        plantilla = evento_por_id(plantilla_id)
        if plantilla_bloque_admite_jefe(
            pool,
            plantilla,
            numero_sala=numero_sala,
            n_salas=n_salas,
            min_preguntas=min_j,
            **pools,
        ):
            viables.append(ambito)
    return tuple(viables)


def _evento_es_grupo(evento: EventoContenidoInstanciado) -> bool:
    from Comun.eventos_partida import tipo_filtro_evento
    from Comun.filtros_bloque import TipoFiltroBloque

    return tipo_filtro_evento(evento) == TipoFiltroBloque.GRUPO


def _evento_es_materia(evento: EventoContenidoInstanciado) -> bool:
    from Comun.eventos_partida import tipo_filtro_evento
    from Comun.filtros_bloque import TipoFiltroBloque

    return tipo_filtro_evento(evento) == TipoFiltroBloque.MATERIA


def _evento_balanceado_desde(evento: EventoContenidoInstanciado) -> EventoContenidoInstanciado:
    from Comun.eventos_partida import tipo_filtro_evento
    from Comun.filtros_bloque import TipoFiltroBloque

    if evento.id == _PLANTILLA_BALANCEADA and evento.perfil_id == "balanceado":
        return evento
    if tipo_filtro_evento(evento) == TipoFiltroBloque.GRUPO:
        return EventoContenidoInstanciado(
            definicion=evento_por_id("puerta_grupo"),
            grupo=evento.grupo,
            perfil_id=None,
        )
    if evento.materia:
        return EventoContenidoInstanciado(
            definicion=evento_por_id(_PLANTILLA_BALANCEADA),
            materia=evento.materia,
            grupo=evento.grupo,
            perfil_id="balanceado",
        )
    return EventoContenidoInstanciado(
        definicion=evento_por_id(_PLANTILLA_BALANCEADA),
        materia=evento.materia,
        grupo=evento.grupo,
        curso=evento.curso,
        semestre=evento.semestre,
        perfil_id="balanceado",
    )


def _puerta_cumple(puerta: PuertaEscape, pool: list[Pregunta], *, numero_sala: int, n_salas: int) -> bool:
    if puerta.modificadores.sin_pregunta or puerta.n_preguntas <= 0:
        return True
    return contar_candidatas_puerta(
        pool, puerta, numero_sala=numero_sala, n_salas=n_salas
    ) >= puerta.n_preguntas


_MAX_INTENTOS_PUERTA_JEFE = 64


def _ids_rasgos_desafio_opcionales(mods: ModificadoresPuerta) -> list[str]:
    from Comun.eventos_partida import RASGOS_BOTIN_ESCAPE, RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE

    return [
        eid
        for eid in mods.eventos_ids
        if eid not in RASGOS_BOTIN_ESCAPE and eid not in RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE
    ]


def _modificadores_jefe_escape(
    mods_base: ModificadoresPuerta,
    *,
    numero_sala: int,
    rng: random.Random,
) -> ModificadoresPuerta:
    from Comun.eventos_partida import (
        RASGO_PUERTA_MALDITA,
        RASGOS_BOTIN_ESCAPE,
        combinar_modificadores_puerta,
        elegir_botines_jefe_escape,
        evento_por_id,
    )

    rasgos = [
        evento_por_id(eid)
        for eid in mods_base.eventos_ids
        if eid not in RASGOS_BOTIN_ESCAPE
    ]
    rasgos.extend(elegir_botines_jefe_escape(numero_sala, rng))
    mods = combinar_modificadores_puerta(tuple(rasgos), numero_sala=numero_sala)
    if mods.fin_partida_si_fallo:
        rasgos_limpios = [
            evento_por_id(eid) for eid in mods.eventos_ids if eid != RASGO_PUERTA_MALDITA
        ]
        mods = combinar_modificadores_puerta(tuple(rasgos_limpios), numero_sala=numero_sala)
    return mods


def _eventos_foco_bloque(
    evento: EventoContenidoInstanciado,
    pools_bloque: dict[str, tuple],
) -> tuple[EventoContenidoInstanciado, ...]:
    from Comun.eventos_partida import OpcionesContenidoEscape

    plantilla = evento.definicion
    opts = plantilla.contenido_escape or OpcionesContenidoEscape()
    ambito = opts.ambito_efectivo
    focos: list[EventoContenidoInstanciado] = []
    if ambito == "grupo":
        for grupo in pools_bloque.get("grupos_pool", ()):
            focos.append(EventoContenidoInstanciado(definicion=plantilla, grupo=grupo))
    elif ambito == "curso":
        for curso in pools_bloque.get("cursos_pool", ()):
            focos.append(EventoContenidoInstanciado(definicion=plantilla, curso=curso))
    elif ambito == "semestre":
        for semestre in pools_bloque.get("semestres_pool", ()):
            focos.append(EventoContenidoInstanciado(definicion=plantilla, semestre=semestre))
    elif ambito == "periodo":
        for curso, semestre in pools_bloque.get("periodos_pool", ()):
            focos.append(
                EventoContenidoInstanciado(
                    definicion=plantilla, curso=curso, semestre=semestre
                )
            )
    if not focos:
        return (evento,)
    vistos: set[tuple] = set()
    unicos: list[EventoContenidoInstanciado] = []
    for ev in focos:
        clave = (ev.grupo, ev.curso, ev.semestre, ev.materia)
        if clave in vistos:
            continue
        vistos.add(clave)
        unicos.append(ev)
    return tuple(unicos)


def _jefe_quitar_rasgo_desafio(
    puerta: PuertaEscape,
    *,
    numero_sala: int,
    rng: random.Random,
) -> PuertaEscape:
    from Comun.escape_room import PuertaEscape
    from Comun.eventos_partida import combinar_modificadores_puerta, evento_por_id

    opcionales = _ids_rasgos_desafio_opcionales(puerta.modificadores)
    if not opcionales:
        return puerta
    quitar = rng.choice(opcionales)
    rasgos = [
        evento_por_id(eid) for eid in puerta.modificadores.eventos_ids if eid != quitar
    ]
    mods = combinar_modificadores_puerta(tuple(rasgos), numero_sala=numero_sala)
    return cast(PuertaEscape, replace(puerta, modificadores=mods))


def _jefe_cambiar_rasgo_desafio(
    puerta: PuertaEscape,
    *,
    numero_sala: int,
    rng: random.Random,
    desafios_disp: list,
) -> PuertaEscape:
    from Comun.escape_room import PuertaEscape
    from Comun.eventos_partida import (
        _compatible_con_rasgos_puerta,
        combinar_modificadores_puerta,
        evento_por_id,
    )

    opcionales = _ids_rasgos_desafio_opcionales(puerta.modificadores)
    if not opcionales or not desafios_disp:
        return puerta
    quitar = rng.choice(opcionales)
    actuales = tuple(
        evento_por_id(eid) for eid in puerta.modificadores.eventos_ids if eid != quitar
    )
    compatibles = [
        ev for ev in desafios_disp if _compatible_con_rasgos_puerta(ev, actuales)
    ]
    if not compatibles:
        return puerta
    rasgos = list(actuales) + [rng.choice(compatibles)]
    mods = combinar_modificadores_puerta(tuple(rasgos), numero_sala=numero_sala)
    return cast(PuertaEscape, replace(puerta, modificadores=mods))


def _jefe_regenerar_modificadores(
    puerta: PuertaEscape,
    *,
    numero_sala: int,
    rng: random.Random,
) -> PuertaEscape:
    from Comun.escape_room import PuertaEscape
    from Comun.eventos_partida import generar_modificadores_puerta

    mods = generar_modificadores_puerta(
        numero_sala=numero_sala,
        rng=rng,
        pausas_usadas=frozenset(),
        pity=None,
        permitir_pausas=False,
    )
    if mods.sin_pregunta:
        return puerta
    mods_jefe = _modificadores_jefe_escape(mods, numero_sala=numero_sala, rng=rng)
    return cast(PuertaEscape, replace(puerta, modificadores=mods_jefe))


def _asegurar_puerta_jefe_viable(
    pool: list[Pregunta],
    puerta: PuertaEscape,
    *,
    numero_sala: int,
    n_salas: int,
    rng: random.Random,
    pools_bloque: dict[str, tuple],
) -> PuertaEscape:
    """Itera rasgos y foco hasta tener >=10 candidatas; mantiene bloque de jefe."""
    from Comun.escape_room import PuertaEscape
    from Comun.eventos_partida import (
        RASGOS_BOTIN_ESCAPE,
        eventos_puerta_escape_para_sala,
        pools_bloque_del_pool,
    )
    from Comun.jefe_partida import PREGUNTAS_POR_JEFE

    candidata = cast(
        PuertaEscape,
        replace(
            puerta,
            n_preguntas=PREGUNTAS_POR_JEFE,
            es_jefe=True,
        ),
    )
    if _puerta_cumple(candidata, pool, numero_sala=numero_sala, n_salas=n_salas):
        return candidata

    pools = pools_bloque or pools_bloque_del_pool(pool)
    focos = list(_eventos_foco_bloque(candidata.evento, pools))
    rng.shuffle(focos)
    desafios_disp = [
        ev
        for ev in eventos_puerta_escape_para_sala(numero_sala)
        if not ev.exclusivo_puerta_escape and ev.id not in RASGOS_BOTIN_ESCAPE
    ]

    for intento in range(_MAX_INTENTOS_PUERTA_JEFE):
        if _puerta_cumple(candidata, pool, numero_sala=numero_sala, n_salas=n_salas):
            return candidata
        accion = intento % 5
        if accion == 0:
            candidata = _jefe_quitar_rasgo_desafio(
                candidata, numero_sala=numero_sala, rng=rng
            )
        elif accion == 1:
            candidata = _jefe_cambiar_rasgo_desafio(
                candidata,
                numero_sala=numero_sala,
                rng=rng,
                desafios_disp=desafios_disp,
            )
        elif accion == 2 and focos:
            candidata = cast(
                PuertaEscape,
                replace(candidata, evento=focos[intento % len(focos)]),
            )
        elif accion == 3:
            candidata = _jefe_regenerar_modificadores(
                candidata, numero_sala=numero_sala, rng=rng
            )
        elif accion == 4:
            candidata = cast(
                PuertaEscape,
                replace(
                    candidata, evento=_evento_balanceado_desde(candidata.evento)
                ),
            )

    mejor: PuertaEscape | None = None
    mejor_n = 0
    for evento in focos:
        prueba = cast(
            PuertaEscape,
            replace(
                candidata,
                n_preguntas=PREGUNTAS_POR_JEFE,
                es_jefe=True,
                evento=evento,
            ),
        )
        disp = contar_candidatas_puerta(
            pool, prueba, numero_sala=numero_sala, n_salas=n_salas
        )
        if disp >= PREGUNTAS_POR_JEFE and disp > mejor_n:
            mejor = prueba
            mejor_n = disp
    if mejor is not None:
        return mejor

    mods_min = _modificadores_jefe_escape(
        ModificadoresPuerta(rasgos=(_RASGO_CLASICA,)),
        numero_sala=numero_sala,
        rng=rng,
    )
    for evento in focos:
        prueba = cast(
            PuertaEscape,
            replace(
                candidata,
                n_preguntas=PREGUNTAS_POR_JEFE,
                es_jefe=True,
                evento=evento,
                modificadores=mods_min,
            ),
        )
        if _puerta_cumple(prueba, pool, numero_sala=numero_sala, n_salas=n_salas):
            return prueba

    return candidata


def asegurar_puerta_viable(
    pool: list[Pregunta],
    puerta: PuertaEscape,
    *,
    numero_sala: int,
    n_salas: int,
    materias_pool: tuple[str, ...],
    grupos_pool: tuple[str, ...] = (),
    rng: random.Random | None = None,
    pools_bloque: dict[str, tuple] | None = None,
) -> PuertaEscape:
    """Ajusta tamaño, contenido o rasgos si no hay preguntas suficientes."""
    if _puerta_cumple(puerta, pool, numero_sala=numero_sala, n_salas=n_salas):
        return puerta
    if puerta.modificadores.sin_pregunta:
        return puerta

    if puerta.es_jefe:
        if rng is None:
            raise ValueError("Puerta jefe: hace falta rng para el ajuste iterativo.")
        return _asegurar_puerta_jefe_viable(
            pool,
            puerta,
            numero_sala=numero_sala,
            n_salas=n_salas,
            rng=rng,
            pools_bloque=pools_bloque or {},
        )

    candidata = puerta
    from Comun.escape_room import PuertaEscape

    for n in reversed(_TAMANOS_REDUCCION):
        if n >= candidata.n_preguntas:
            continue
        prueba = cast(PuertaEscape, replace(candidata, n_preguntas=n))
        if _puerta_cumple(prueba, pool, numero_sala=numero_sala, n_salas=n_salas):
            return prueba

    evento_relajado = _evento_balanceado_desde(candidata.evento)
    for n in reversed(_TAMANOS_REDUCCION):
        prueba = cast(
            PuertaEscape,
            replace(candidata, n_preguntas=n, evento=evento_relajado),
        )
        if _puerta_cumple(prueba, pool, numero_sala=numero_sala, n_salas=n_salas):
            return prueba

    if grupos_pool and _evento_es_grupo(candidata.evento):
        from Comun.escape_room import PuertaEscape

        mejor: PuertaEscape | None = None
        mejor_n = 0
        for grupo in grupos_pool:
            evento = EventoContenidoInstanciado(
                definicion=evento_por_id("puerta_grupo"),
                grupo=grupo,
            )
            for n in reversed(_TAMANOS_REDUCCION):
                prueba = cast(
                    PuertaEscape,
                    replace(
                        candidata,
                        n_preguntas=n,
                        evento=evento,
                        modificadores=ModificadoresPuerta(rasgos=(_RASGO_CLASICA,)),
                    ),
                )
                disp = contar_candidatas_puerta(
                    pool, prueba, numero_sala=numero_sala, n_salas=n_salas
                )
                if disp >= n and disp > mejor_n:
                    mejor = prueba
                    mejor_n = disp
        if mejor is not None:
            return mejor

    if materias_pool:
        mejor = None
        mejor_n = 0
        for materia in materias_pool:
            evento = EventoContenidoInstanciado(
                definicion=evento_por_id(_PLANTILLA_BALANCEADA),
                materia=materia,
            )
            for n in reversed(_TAMANOS_REDUCCION):
                prueba = cast(
                    PuertaEscape,
                    replace(
                        candidata,
                        n_preguntas=n,
                        evento=evento,
                        modificadores=ModificadoresPuerta(rasgos=(_RASGO_CLASICA,)),
                    ),
                )
                disp = contar_candidatas_puerta(
                    pool, prueba, numero_sala=numero_sala, n_salas=n_salas
                )
                if disp >= n and disp > mejor_n:
                    mejor = prueba
                    mejor_n = disp
        if mejor is not None:
            return mejor

    raise ValueError(
        f"No se pudo hacer viable la puerta {candidata.evento.nombre!r} "
        f"en sala {numero_sala}."
    )


def seleccionar_preguntas_desafio(
    pool: list[Pregunta],
    puerta: PuertaEscape,
    *,
    numero_sala: int,
    n_salas: int,
    rng: random.Random,
    usadas: set[int] | None = None,
) -> list[Pregunta]:
    if puerta.modificadores.sin_pregunta or puerta.n_preguntas <= 0:
        return []

    criterios = _criterios_desafio(
        puerta, numero_sala=numero_sala, n_salas=n_salas, pool=pool
    )
    n_preguntas = criterios.n_preguntas
    usadas = usadas if usadas is not None else set()

    candidatas = _indices_candidatas(pool, criterios, usadas)
    if len(candidatas) < n_preguntas:
        candidatas = _indices_candidatas(pool, criterios, set())
    if len(candidatas) < n_preguntas:
        etiqueta = puerta.evento.nombre
        destino = puerta.evento.etiqueta_foco or (
            etiqueta_grupo_tematico(puerta.evento.grupo) if puerta.evento.grupo else "?"
        )
        raise ValueError(
            f"No hay suficientes preguntas para {etiqueta!r} ({destino!r}) "
            f"en sala {numero_sala}: hace falta {n_preguntas}, hay {len(candidatas)}."
        )

    elegidos = _seleccionar_indices_diversificando_dificultad(
        pool, candidatas, n_preguntas, criterios, usadas, rng
    )
    usadas.update(elegidos)
    resultado = [pool[i] for i in elegidos]
    if len(criterios.dificultades_permitidas) > 1 and len(resultado) > 1:
        from Comun.generador_examen_historia import ordenar_preguntas_por_dificultad

        resultado = ordenar_preguntas_por_dificultad(resultado)
    return resultado


def reemplazar_pregunta_cambio_escape(
    pool: list[Pregunta],
    puerta: PuertaEscape,
    *,
    indice_actual: int | None,
    numero_sala: int,
    n_salas: int,
    rng: random.Random,
    usadas: set[int],
) -> Pregunta | None:
    """Sustituye la pregunta actual por otra del mismo criterio (powerup cambio)."""
    if puerta.modificadores.sin_pregunta or puerta.n_preguntas <= 0:
        return None
    criterios = _criterios_desafio(
        puerta, numero_sala=numero_sala, n_salas=n_salas, pool=pool
    )
    candidatas = [
        i for i in _indices_candidatas(pool, criterios, usadas) if i != indice_actual
    ]
    if not candidatas:
        candidatas = [
            i for i in _indices_candidatas(pool, criterios, set()) if i != indice_actual
        ]
    if not candidatas:
        return None
    elegido = rng.choice(candidatas)
    usadas.add(elegido)
    return pool[elegido]
