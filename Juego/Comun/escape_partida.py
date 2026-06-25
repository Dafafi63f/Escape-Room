#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pool del escape room (dataset revisado o modo beta).

Responsabilidades
-----------------
* **Puerta**: nº de preguntas y rasgos de juego (cronómetros, niebla, puntos dobles…).
* **Evento de contenido**: materia, grupo, dificultad, tipo de pregunta.
* **Escalada (sala)**: complejidad global progresiva (inicio baja, medio amplio, final alta).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from Comun.dificultad import complejidad_pregunta, niveles_en_pool
from Comun.config_historia import etiqueta_grupo_tematico
from Comun.eventos_partida import (
    EventoContenidoInstanciado,
    ModificadoresPuerta,
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
    "iconos_recompensa_completar",
    "materias_del_grupo",
    "materias_del_pool",
    "materias_viables_sala",
    "puerta_es_jefe",
    "reglas_juego_desafio",
    "reglas_partida_desde_desafio",
    "seleccionar_preguntas_desafio",
    "tiempo_pregunta_escape_por_defecto",
    "acotar_tiempo_pregunta_escape",
    "TIEMPO_PREGUNTA_MIN_ESCAPE",
    "VIDAS_MAX_ESCAPE",
]

_DIFICULTADES_TODAS = frozenset({"Facil", "Media", "Dificil"})
_PLANTILLA_BALANCEADA = "pregunta_unica"
_TAMANOS_REDUCCION = (3, 5, 10)
VIDAS_MAX_ESCAPE = 4
TIEMPO_PREGUNTA_MIN_ESCAPE = 20
_DIFICULTAD_JEFE = frozenset({"Dificil"})


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
    dificultades_permitidas: frozenset[str] | None
    tipos_permitidos: frozenset[str] | None


@dataclass(frozen=True)
class CriteriosSeleccionPool:
    n_preguntas: int
    materia: str | None
    grupo: str | None
    dificultades_permitidas: frozenset[str]
    min_complejidad: int
    max_complejidad: int
    tipos_permitidos: frozenset[str] | None


@dataclass(frozen=True)
class ReglasJuegoDesafio:
    tiempo_pregunta_seg: int | None
    tiempo_puerta_seg: int | None
    fraccion_enunciado: float
    opciones_ocultas: int
    multiplicador_puntos: int


@dataclass(frozen=True)
class BonificacionCompletarEscape:
    """Recompensa al superar un bloque de preguntas (solo esa puerta; no arrastra)."""

    delta_vidas: int = 0
    etiqueta: str = ""

    @property
    def mensaje(self) -> str:
        if self.delta_vidas <= 0:
            return ""
        if self.etiqueta:
            return f"❤️ {self.etiqueta}: recuperas {self._texto_vidas()}."
        return f"❤️ Puerta superada: recuperas {self._texto_vidas()}."

    def _texto_vidas(self) -> str:
        n = self.delta_vidas
        return "1 vida" if n == 1 else f"{n} vidas"


def puerta_es_jefe(puerta: PuertaEscape) -> bool:
    """Bloque largo con preguntas solo difíciles."""
    if puerta.modificadores.sin_pregunta or puerta.n_preguntas < 10:
        return False
    difs = puerta.evento.dificultades_permitidas
    return difs is not None and difs <= _DIFICULTAD_JEFE and "Dificil" in difs


def delta_vidas_descanso_entrada(puerta: PuertaEscape) -> int:
    """Vida al elegir puerta sin preguntas (respiro, no botín)."""
    if not puerta.modificadores.sin_pregunta:
        return 0
    from Comun.eventos_partida import RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE, evento_por_id

    return sum(
        evento_por_id(eid).modificadores.delta_vidas_al_completar
        for eid in puerta.modificadores.eventos_ids
        if eid in RASGOS_PUERTA_SIN_PREGUNTA_ESCAPE
    )


def mensaje_feedback_puerta_sin_pregunta(puerta: PuertaEscape) -> str:
    """Texto al elegir una puerta sin bloque de preguntas."""
    from Comun.eventos_partida import evento_sin_pregunta_escape

    ev = evento_sin_pregunta_escape(puerta.modificadores)
    if ev is None:
        base = "💤 Avanzas sin preguntas."
    elif delta_vidas_descanso_entrada(puerta) > 0:
        base = f"{ev.emoji} {ev.nombre}: recuperas 1 vida."
    else:
        base = f"{ev.emoji} {ev.nombre}: avanzas sin preguntas."
    if "botin" in puerta.modificadores.eventos_ids:
        base += " Al cerrar la puerta podrás reclamar el botín."
    return base


def puerta_tiene_recompensa_vidas(puerta: PuertaEscape) -> bool:
    """True si la puerta puede dar vidas extra (botín, jefe o descanso)."""
    if puerta.modificadores.sin_pregunta:
        return any(
            eid in RASGOS_RECOMPENSA_VIDAS_ESCAPE for eid in puerta.modificadores.eventos_ids
        )
    if puerta_es_jefe(puerta):
        return True
    return any(
        eid in RASGOS_RECOMPENSA_VIDAS_ESCAPE for eid in puerta.modificadores.eventos_ids
    )


def bonificacion_completar_escape(puerta: PuertaEscape) -> BonificacionCompletarEscape:
    """Vidas extra al superar la puerta sin fallar (solo rasgos de recompensa o jefe)."""
    if puerta.modificadores.sin_pregunta:
        if any(
            eid in RASGOS_RECOMPENSA_VIDAS_ESCAPE for eid in puerta.modificadores.eventos_ids
        ):
            from Comun.eventos_partida import evento_por_id

            delta = sum(
                evento_por_id(eid).modificadores.delta_vidas_al_completar
                for eid in puerta.modificadores.eventos_ids
                if eid in RASGOS_RECOMPENSA_VIDAS_ESCAPE
            )
            return BonificacionCompletarEscape(delta_vidas=delta, etiqueta="Botín de la puerta")
        return BonificacionCompletarEscape()
    if puerta.n_preguntas <= 0:
        return BonificacionCompletarEscape()
    delta = 0
    etiqueta = ""
    if any(
        eid in RASGOS_RECOMPENSA_VIDAS_ESCAPE for eid in puerta.modificadores.eventos_ids
    ):
        delta = puerta.modificadores.delta_vidas_al_completar
        etiqueta = "Botín de la puerta"
    if puerta_es_jefe(puerta):
        delta = max(delta, 2)
        etiqueta = "Puerta jefe superada"
    return BonificacionCompletarEscape(delta_vidas=delta, etiqueta=etiqueta)


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
) -> int:
    """Suma vidas de recompensa respetando el tope. Devuelve vidas realmente ganadas."""
    if bonus.delta_vidas <= 0 or estado.vidas_restantes is None:
        return 0
    antes = estado.vidas_restantes
    estado.vidas_restantes = min(vidas_max, antes + bonus.delta_vidas)
    return estado.vidas_restantes - antes


def iconos_recompensa_completar(puerta: PuertaEscape) -> tuple:
    """Iconos de recompensa esperada al superar la puerta (escape_partida → eventos)."""
    from Comun.eventos_partida import IconoEfectoPuerta, tooltip_recompensa_completar

    bonus = bonificacion_completar_escape(puerta)
    if bonus.delta_vidas <= 0:
        return ()
    emoji = "👑" if puerta_es_jefe(puerta) else "❤️"
    return (
        IconoEfectoPuerta(
            emoji=emoji,
            tooltip=tooltip_recompensa_completar(bonus, es_jefe=puerta_es_jefe(puerta)),
        ),
    )


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
        fraccion_enunciado=mods.fraccion_enunciado,
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
    return tuple(viables) if viables else materias_pool


def grupos_viables_sala(
    pool: list[Pregunta],
    grupos_pool: tuple[str, ...],
    *,
    numero_sala: int,
    n_salas: int,
    min_preguntas: int = 3,
) -> tuple[str, ...]:
    """Grupos con al menos ``min_preguntas`` candidatas en la escalada de la sala."""
    from Comun.escape_room import PuertaEscape

    viables: list[str] = []
    for grupo in grupos_pool:
        evento = EventoContenidoInstanciado(
            definicion=evento_por_id("bloque_grupo"),
            grupo=grupo,
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
            viables.append(grupo)
    return tuple(viables) if viables else grupos_pool


def _evento_es_grupo(evento: EventoContenidoInstanciado) -> bool:
    opts = evento.contenido_escape
    return bool(opts and opts.usa_grupo and evento.grupo)


def _evento_balanceado_desde(evento: EventoContenidoInstanciado) -> EventoContenidoInstanciado:
    if evento.id == _PLANTILLA_BALANCEADA:
        return evento
    opts = evento.contenido_escape
    if opts and opts.usa_grupo:
        return evento
    return EventoContenidoInstanciado(
        definicion=evento_por_id(_PLANTILLA_BALANCEADA),
        materia=evento.materia,
        grupo=evento.grupo,
    )


def _puerta_cumple(puerta: PuertaEscape, pool: list[Pregunta], *, numero_sala: int, n_salas: int) -> bool:
    if puerta.modificadores.sin_pregunta or puerta.n_preguntas <= 0:
        return True
    return contar_candidatas_puerta(
        pool, puerta, numero_sala=numero_sala, n_salas=n_salas
    ) >= puerta.n_preguntas


def asegurar_puerta_viable(
    pool: list[Pregunta],
    puerta: PuertaEscape,
    *,
    numero_sala: int,
    n_salas: int,
    semilla: int,
    indice_puerta: int,
    materias_pool: tuple[str, ...],
    grupos_pool: tuple[str, ...] = (),
) -> PuertaEscape:
    """Ajusta tamaño, contenido o rasgos si no hay preguntas suficientes."""
    if _puerta_cumple(puerta, pool, numero_sala=numero_sala, n_salas=n_salas):
        return puerta
    if puerta.modificadores.sin_pregunta:
        return puerta

    candidata = puerta

    for n in reversed(_TAMANOS_REDUCCION):
        if n >= candidata.n_preguntas:
            continue
        prueba = replace(candidata, n_preguntas=n)
        if _puerta_cumple(prueba, pool, numero_sala=numero_sala, n_salas=n_salas):
            return prueba

    evento_relajado = _evento_balanceado_desde(candidata.evento)
    for n in reversed(_TAMANOS_REDUCCION):
        prueba = replace(candidata, n_preguntas=n, evento=evento_relajado)
        if _puerta_cumple(prueba, pool, numero_sala=numero_sala, n_salas=n_salas):
            return prueba

    if _evento_es_grupo(candidata.evento) and grupos_pool:
        from Comun.escape_room import PuertaEscape

        mejor: PuertaEscape | None = None
        mejor_n = 0
        for grupo in grupos_pool:
            evento = EventoContenidoInstanciado(
                definicion=evento_por_id("bloque_grupo"),
                grupo=grupo,
            )
            for n in reversed(_TAMANOS_REDUCCION):
                prueba = replace(
                    candidata,
                    n_preguntas=n,
                    evento=evento,
                    modificadores=ModificadoresPuerta(rasgos=("Clásica",)),
                )
                disp = contar_candidatas_puerta(
                    pool, prueba, numero_sala=numero_sala, n_salas=n_salas
                )
                if disp >= n and disp > mejor_n:
                    mejor = prueba
                    mejor_n = disp
        if mejor is not None:
            return mejor

    if candidata.evento.materia:
        from Comun.escape_room import PuertaEscape

        mejor: PuertaEscape | None = None
        mejor_n = 0
        for materia in materias_pool:
            evento = EventoContenidoInstanciado(
                definicion=evento_por_id(_PLANTILLA_BALANCEADA),
                materia=materia,
            )
            for n in reversed(_TAMANOS_REDUCCION):
                prueba = replace(
                    candidata,
                    n_preguntas=n,
                    evento=evento,
                    modificadores=ModificadoresPuerta(rasgos=("Clásica",)),
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
    semilla: int,
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

    rng = random.Random(semilla)
    elegidos = rng.sample(candidatas, n_preguntas)
    usadas.update(elegidos)
    return [pool[i] for i in elegidos]
