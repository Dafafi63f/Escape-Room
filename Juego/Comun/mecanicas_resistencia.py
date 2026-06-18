#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mecánicas extendidas del modo resistencia (reto día, apuestas, maldiciones, bloques).

Fin de partida: solo por acciones del jugador (fallar, tiempo agotado, apuesta perdida,
abandonar). No hay derrota automática ni pérdida de vidas sin una respuesta/decisión.
La escalada y la presión de racha hacen más probable el fallo, pero la vida solo baja
cuando el jugador falla o se queda sin tiempo.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from Comun.estado_resistencia import EstadoResistencia
from Comun.iconos_resistencia import prefijar_emoji
from Comun.modelos import Pregunta
from Comun.pool_libre import EstadoSeleccionPool
from Comun.resistencia_historia import EscaladaResistencia, PREGUNTA_MIN_EVENTOS_ALEATORIOS

__all__ = [
    "ApuestaRiesgo",
    "BloqueFiltroActivo",
    "MaldicionActiva",
    "aplicar_efectos_maldicion",
    "configurar_partida_resistencia",
    "consumir_bloque_filtro",
    "elegir_indice_similar",
    "formatear_aviso_apuesta",
    "formatear_aviso_bloque",
    "aplicar_presion_racha_modificadores",
    "exceso_presion_racha",
    "formatear_aviso_maldicion",
    "formatear_aviso_presion_racha",
    "intensidad_presion_racha",
    "oferta_apuesta_para_pregunta",
    "preparar_eventos_nuevo_turno",
    "preparar_presion_racha_turno",
    "presion_racha_umbral",
    "procesar_post_turno_resistencia",
    "rng_partida",
    "texto_progreso_resistencia",
]

_MALDIGIONES: tuple[tuple[str, str, str], ...] = (
    ("niebla", "Maldición: niebla en el enunciado", "🌫️"),
    ("sin_objetos", "Maldición: no puedes usar objetos", "⛔"),
    ("relampago", "Maldición: relámpago forzado", "⚡"),
    ("sin_pistas", "Maldición: sin solución tras fallar", "🙈"),
)


# Presión por racha alta: la pregunta actual se vuelve más exigente (sin castigos automáticos).
PRESION_RACHA_UMBRAL = 25
_PRESION_RACHA_ESCALA = 30.0


def presion_racha_umbral() -> int:
    return PRESION_RACHA_UMBRAL


def intensidad_presion_racha(racha: int) -> float:
    """Escala con la racha; puede superar 1.0 y romper topes de eventos negativos."""
    if racha < PRESION_RACHA_UMBRAL:
        return 0.0
    exceso = racha - PRESION_RACHA_UMBRAL
    return exceso / _PRESION_RACHA_ESCALA


def exceso_presion_racha(racha: int) -> float:
    """Porción por encima del nivel «completo» (1.0) de presión."""
    return max(0.0, intensidad_presion_racha(racha) - 1.0)


def formatear_aviso_presion_racha(intensidad: float) -> str:
    if intensidad > 1.0:
        texto = (
            "Presión extrema de la racha: se acumulan eventos hostiles "
            "más allá del límite habitual."
        )
    elif intensidad < 0.35:
        texto = "La racha aprieta: el enunciado será más difícil de leer."
    elif intensidad < 0.65:
        texto = "Presión de la racha: menos margen y más niebla en esta pregunta."
    else:
        texto = "Presión de la racha: esta pregunta es especialmente exigente."
    return prefijar_emoji(texto, "⚖️")


def preparar_presion_racha_turno(
    er: EstadoResistencia,
    numero_pregunta: int,
) -> str | None:
    """Marca la intensidad de presión del turno (sin quitar vidas ni cortar racha)."""
    del numero_pregunta  # reservado para avisos deterministas futuros
    t = intensidad_presion_racha(er.racha)
    er.presion_racha_intensidad = t
    if t <= 0.0:
        return None
    return formatear_aviso_presion_racha(t)


def aplicar_presion_racha_modificadores(
    er: EstadoResistencia,
    p: Pregunta,
    numero_pregunta: int,
) -> None:
    """Modificadores extra según la racha; con racha extrema apila efectos hostiles."""
    t = er.presion_racha_intensidad
    if t <= 0.0:
        return
    from Comun.powerups_resistencia import letras_ocultas_por_cantidad

    base = min(1.0, t)
    er.fraccion_enunciado = min(er.fraccion_enunciado, max(0.35, 1.0 - 0.35 * base))
    if base >= 0.25:
        seg = max(5, int(14 - 8 * base))
        if er.relampago_forzado_seg is None or er.relampago_forzado_seg > seg:
            er.relampago_forzado_seg = seg
    if base >= 0.4:
        n_ocultas = 1 if base < 0.7 else 2
        er.letras_ocultas = er.letras_ocultas | letras_ocultas_por_cantidad(
            p,
            n_ocultas,
            semilla=numero_pregunta + 9001,
        )
    if base >= 0.75:
        rng = rng_partida(er, numero_pregunta * 101 + int(base * 1000))
        if rng.random() < 0.35 + 0.4 * base:
            er.sin_pistas_turno = True

    if t <= 1.0:
        return

    exceso = t - 1.0
    er.fraccion_enunciado = min(er.fraccion_enunciado, max(0.15, 0.30 - 0.08 * min(exceso, 2.0)))
    seg_ext = max(3, int(6 - 2 * min(exceso, 1.5)))
    if er.relampago_forzado_seg is None or er.relampago_forzado_seg > seg_ext:
        er.relampago_forzado_seg = seg_ext
    n_extra = min(2, 1 + int(exceso))
    er.letras_ocultas = er.letras_ocultas | letras_ocultas_por_cantidad(
        p,
        n_extra,
        semilla=numero_pregunta + 17003 + er.racha,
    )
    er.sin_pistas_turno = True
    er.objetos_bloqueados = True
    if exceso >= 0.5:
        er.fraccion_enunciado = min(er.fraccion_enunciado, 0.22)


@dataclass(frozen=True)
class BloqueFiltroActivo:
    etiqueta: str
    preguntas_restantes: int
    materia: str | None = None
    tipo: str | None = None
    grupo: str | None = None
    dificultad: str | None = None


@dataclass(frozen=True)
class ApuestaRiesgo:
    etiqueta: str
    mult_puntos: int
    vidas_fallo: int


@dataclass
class MaldicionActiva:
    id: str
    etiqueta: str
    preguntas_restantes: int = 1


def rng_partida(er: EstadoResistencia, clave: int) -> random.Random:
    base = er.semilla_partida if er.semilla_partida is not None else 0
    return random.Random(base * 1_000_003 + clave * 104_729)


def configurar_partida_resistencia(er: EstadoResistencia, *, preset_id: str) -> None:
    from Comun.reto_dia_resistencia import es_id_reto_dia, semilla_reto_dia

    if es_id_reto_dia(preset_id):
        er.reto_dia = True
        er.semilla_partida = semilla_reto_dia()


def texto_progreso_resistencia(er: EstadoResistencia, numero_pregunta: int) -> str:
    return f"#{numero_pregunta} · Racha {er.racha}"


def _pregunta_cumple_bloque(p: Pregunta, bloque: BloqueFiltroActivo) -> bool:
    if bloque.materia and p.materia != bloque.materia:
        return False
    if bloque.tipo and p.tipo != bloque.tipo:
        return False
    if bloque.grupo and p.grupo != bloque.grupo:
        return False
    if bloque.dificultad and p.dificultad != bloque.dificultad:
        return False
    return True


def consumir_bloque_filtro(er: EstadoResistencia) -> None:
    if er.bloque_filtro and er.bloque_filtro.preguntas_restantes > 0:
        rest = er.bloque_filtro.preguntas_restantes - 1
        if rest <= 0:
            er.bloque_filtro = None
        else:
            bf = er.bloque_filtro
            er.bloque_filtro = BloqueFiltroActivo(
                etiqueta=bf.etiqueta,
                preguntas_restantes=rest,
                materia=bf.materia,
                tipo=bf.tipo,
                grupo=bf.grupo,
                dificultad=bf.dificultad,
            )


def _materias_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.materia for p in pool if p.materia})


def _grupos_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.grupo for p in pool if p.grupo})


def _generar_bloque_filtro(
    pool: list[Pregunta],
    numero_pregunta: int,
    er: EstadoResistencia,
) -> BloqueFiltroActivo | None:
    if er.bloque_filtro and er.bloque_filtro.preguntas_restantes > 0:
        return None
    if numero_pregunta < PREGUNTA_MIN_EVENTOS_ALEATORIOS:
        return None
    rng = rng_partida(er, numero_pregunta * 37 + 901)
    from Comun.probabilidad_resistencia import probabilidad_buena_resistencia

    prob = probabilidad_buena_resistencia(numero_pregunta) * 0.42
    if rng.random() > prob:
        return None

    n = rng.randint(3, 5)
    opciones: list[BloqueFiltroActivo] = []
    materias = _materias_en_pool(pool)
    grupos = _grupos_en_pool(pool)
    if materias:
        mat = rng.choice(materias)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=f"Bloque: {n} preguntas de {mat}",
                preguntas_restantes=n,
                materia=mat,
            )
        )
    opciones.append(
        BloqueFiltroActivo(
            etiqueta=f"Bloque: {n} preguntas de Cálculo",
            preguntas_restantes=n,
            tipo="Calculo",
        )
    )
    opciones.append(
        BloqueFiltroActivo(
            etiqueta=f"Bloque: {n} preguntas de Teoría",
            preguntas_restantes=n,
            tipo="Teoria",
        )
    )
    if grupos:
        g = rng.choice(grupos)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=f"Bloque: {n} preguntas del grupo {g}",
                preguntas_restantes=n,
                grupo=g,
            )
        )
    return rng.choice(opciones)


def oferta_apuesta_para_pregunta(
    numero_pregunta: int,
    er: EstadoResistencia,
) -> ApuestaRiesgo | None:
    if numero_pregunta < 8:
        return None
    if er.maldicion is not None:
        return None
    if er.apuesta_activa is not None:
        return None
    rng = rng_partida(er, numero_pregunta * 53 + 4049)
    from Comun.probabilidad_resistencia import probabilidad_buena_resistencia

    prob = probabilidad_buena_resistencia(numero_pregunta) * 0.34
    if rng.random() > prob:
        return None
    tabla = [
        ApuestaRiesgo("Doble o nada", mult_puntos=2, vidas_fallo=2),
        ApuestaRiesgo("Triple arriesgado", mult_puntos=3, vidas_fallo=2),
    ]
    return rng.choice(tabla)


def preparar_eventos_nuevo_turno(
    er: EstadoResistencia,
    pool: list[Pregunta],
    numero_pregunta: int,
) -> list[str]:
    """Eventos al cargar una pregunta nueva (presión de racha, bloque, apuesta)."""
    avisos: list[str] = []
    aviso_presion = preparar_presion_racha_turno(er, numero_pregunta)
    if aviso_presion:
        avisos.append(aviso_presion)
    bloque = _generar_bloque_filtro(pool, numero_pregunta, er)
    if bloque:
        er.bloque_filtro = bloque
        avisos.append(formatear_aviso_bloque(bloque.etiqueta))
    if not er.apuesta_oferta:
        er.apuesta_oferta = oferta_apuesta_para_pregunta(numero_pregunta, er)
    return avisos


def formatear_aviso_bloque(etiqueta: str) -> str:
    return prefijar_emoji(etiqueta, "📚")


def formatear_aviso_apuesta(apuesta: ApuestaRiesgo) -> str:
    texto = (
        f"{apuesta.etiqueta}: ×{apuesta.mult_puntos} puntos si aciertas, "
        f"pero un fallo cuesta {apuesta.vidas_fallo} vidas."
    )
    return prefijar_emoji(texto, "🎰")


def formatear_aviso_maldicion(etiqueta: str) -> str:
    return prefijar_emoji(etiqueta, "💀")


def _activar_maldicion(er: EstadoResistencia, numero_pregunta: int) -> MaldicionActiva | None:
    if er.maldicion is not None:
        return None
    fallos = sum(1 for ok in er.ventana_resultados if not ok)
    if len(er.ventana_resultados) < 3 or fallos < 2:
        return None
    rng = rng_partida(er, numero_pregunta * 71 + 3001)
    from Comun.probabilidad_resistencia import probabilidad_mala_resistencia

    if rng.random() > probabilidad_mala_resistencia(numero_pregunta):
        return None
    cid, etiqueta, _ = rng.choice(_MALDIGIONES)
    duracion = 2 if rng.random() < 0.35 else 1
    return MaldicionActiva(id=cid, etiqueta=etiqueta, preguntas_restantes=duracion)


def aplicar_efectos_maldicion(er: EstadoResistencia) -> None:
    if not er.maldicion:
        return
    cid = er.maldicion.id
    if cid == "niebla":
        er.fraccion_enunciado = min(er.fraccion_enunciado, 0.45)
    elif cid == "sin_objetos":
        er.objetos_bloqueados = True
    elif cid == "relampago":
        er.relampago_forzado_seg = 8
    elif cid == "sin_pistas":
        er.sin_pistas_turno = True


def procesar_post_turno_resistencia(
    er: EstadoResistencia,
    *,
    acierto: bool,
    numero_pregunta: int,
) -> list[str]:
    """Tras evaluar respuesta: ventana de fallos, maldiciones y tick de maldición activa."""
    avisos: list[str] = []
    er.ventana_resultados.append(acierto)
    if len(er.ventana_resultados) > 3:
        er.ventana_resultados.pop(0)

    if er.maldicion:
        er.maldicion.preguntas_restantes -= 1
        if er.maldicion.preguntas_restantes <= 0:
            er.maldicion = None
            er.objetos_bloqueados = False
            er.sin_pistas_turno = False

    if not acierto:
        nueva = _activar_maldicion(er, numero_pregunta)
        if nueva:
            er.maldicion = nueva
            avisos.append(formatear_aviso_maldicion(nueva.etiqueta))

    er.apuesta_activa = None
    er.apuesta_oferta = None
    return avisos


def pregunta_compatible_bloque(p: Pregunta, er: EstadoResistencia) -> bool:
    if not er.bloque_filtro or er.bloque_filtro.preguntas_restantes <= 0:
        return True
    return _pregunta_cumple_bloque(p, er.bloque_filtro)


def elegir_indice_similar(
    pool: list[Pregunta],
    estado: EstadoSeleccionPool,
    escalada: EscaladaResistencia,
    numero_pregunta: int,
    idx_actual: int,
    *,
    er: EstadoResistencia | None = None,
) -> int | None:
    """Sustituye por otra pregunta con la misma materia y tipo."""
    from Comun.resistencia_historia import indices_candidatos_resistencia

    actual = pool[idx_actual]
    candidatas = indices_candidatos_resistencia(
        pool,
        estado,
        escalada,
        numero_pregunta,
        solo_no_usadas=True,
        er=er,
    )
    similares = [
        i
        for i in candidatas
        if i != idx_actual
        and pool[i].materia == actual.materia
        and pool[i].tipo == actual.tipo
    ]
    if not similares:
        candidatas = indices_candidatos_resistencia(
            pool,
            estado,
            escalada,
            numero_pregunta,
            solo_no_usadas=False,
            er=er,
        )
        similares = [
            i
            for i in candidatas
            if i != idx_actual
            and pool[i].materia == actual.materia
            and pool[i].tipo == actual.tipo
        ]
    if not similares:
        similares = [
            i
            for i in candidatas
            if i != idx_actual and pool[i].materia == actual.materia
        ]
    if not similares:
        return None
    rng = rng_partida(er, numero_pregunta * 19 + idx_actual) if er else random.Random()
    elegido = rng.choice(similares)
    estado.usadas.discard(idx_actual)
    estado.usadas.add(elegido)
    if estado.historial_reciente and estado.historial_reciente[-1] == idx_actual:
        estado.historial_reciente[-1] = elegido
    else:
        estado.historial_reciente.append(elegido)
    return elegido
