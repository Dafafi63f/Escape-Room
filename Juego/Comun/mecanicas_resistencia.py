#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mecánicas extendidas del modo resistencia (reto día, apuestas, maldiciones, bloques).

El pool disponible en cada pregunta lo fija el juego (cuotas del banco + escalada).
Los bloques solo añaden un filtro temporal (materia, tipo, grupo, curso, semestre);
al expirar, ``bloque_filtro`` pasa a ``None`` y vuelve el criterio por defecto.

Fin de partida: solo por acciones del jugador (fallar, tiempo agotado, apuesta perdida,
abandonar). No hay derrota automática ni pérdida de vidas sin una respuesta/decisión.
La escalada y la presión de racha hacen más probable el fallo, pero la vida solo baja
cuando el jugador falla o se queda sin tiempo.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from Comun.config_historia import GRUPOS_TEMATICOS
from Comun.estado_resistencia import EstadoResistencia
from Comun.iconos_resistencia import prefijar_emoji
from Comun.modelos import Pregunta
from Comun.pool_libre import EstadoSeleccionPool
from Comun.resistencia_historia import EscaladaResistencia, PREGUNTA_MIN_EVENTOS_ALEATORIOS
from Comun.probabilidad_resistencia import factor_progreso_resistencia

__all__ = [
    "APUESTAS_DISPONIBLES",
    "ApuestaRiesgo",
    "CosteApuesta",
    "RecompensaApuesta",
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
    """Filtro temporal sobre el pool ya disponible (materia, tipo, grupo, curso o semestre)."""

    etiqueta: str
    preguntas_restantes: int
    materia: str | None = None
    tipo: str | None = None
    grupo: str | None = None
    curso: str | None = None
    semestre: str | None = None


_ETIQUETA_TIPO: dict[str, str] = {
    "Teoria": "Teoría",
    "Calculo": "Cálculo",
    "General": "generales",
}


def _etiqueta_bloque(n: int, descripcion: str) -> str:
    return f"Bloque: {n} preguntas {descripcion}"


def _descripcion_grupo_tematico(grupo: str, pool: list[Pregunta]) -> str:
    clave = str(grupo).strip()
    if clave in GRUPOS_TEMATICOS:
        return f"de {GRUPOS_TEMATICOS[clave]}"
    materias = sorted({p.materia for p in pool if p.grupo == grupo and p.materia})
    if len(materias) == 1:
        return f"de {materias[0]}"
    if materias:
        resto = f" (+{len(materias) - 2})" if len(materias) > 2 else ""
        return f"de {' · '.join(materias[:2])}{resto}"
    return f"del grupo {grupo}"


def _descripcion_tipo(tipo: str) -> str:
    etiqueta = _ETIQUETA_TIPO.get(tipo, tipo)
    if tipo in _ETIQUETA_TIPO:
        return f"de {etiqueta}"
    return f"de tipo {etiqueta}"


def _descripcion_curso(curso: str) -> str:
    return f"del curso {curso}"


def _descripcion_semestre(curso: str, semestre: str) -> str:
    if curso:
        return f"del curso {curso} · semestre {semestre}"
    return f"del semestre {semestre}"


@dataclass(frozen=True)
class RecompensaApuesta:
    mult_puntos: int = 1
    delta_vidas: int = 0
    powerup_id: str | None = None
    cantidad_powerup: int = 1
    powerup_aleatorio: bool = False


@dataclass(frozen=True)
class CosteApuesta:
    """Penalización si fallas la pregunta con apuesta activa."""

    vidas_fallo: int = 1  # Total de vidas perdidas (1 = solo el fallo habitual)
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
    if bloque.curso and p.curso != bloque.curso:
        return False
    if bloque.semestre and p.semestre != bloque.semestre:
        return False
    return True


def consumir_bloque_filtro(er: EstadoResistencia) -> None:
    """Avanza el filtro de bloque; al expirar vuelve al pool por defecto del momento."""
    if not er.bloque_filtro or er.bloque_filtro.preguntas_restantes <= 0:
        return
    rest = er.bloque_filtro.preguntas_restantes - 1
    if rest <= 0:
        er.bloque_filtro = None
        return
    bf = er.bloque_filtro
    er.bloque_filtro = BloqueFiltroActivo(
        etiqueta=bf.etiqueta,
        preguntas_restantes=rest,
        materia=bf.materia,
        tipo=bf.tipo,
        grupo=bf.grupo,
        curso=bf.curso,
        semestre=bf.semestre,
    )


def _materias_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.materia for p in pool if p.materia})


def _grupos_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.grupo for p in pool if p.grupo})


def _cursos_en_pool(pool: list[Pregunta]) -> list[str]:
    return sorted({p.curso for p in pool if p.curso})


def _pares_curso_semestre_en_pool(pool: list[Pregunta]) -> list[tuple[str, str]]:
    return sorted({(p.curso, p.semestre) for p in pool if p.curso and p.semestre})


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
                etiqueta=_etiqueta_bloque(n, f"de {mat}"),
                preguntas_restantes=n,
                materia=mat,
            )
        )
    opciones.append(
        BloqueFiltroActivo(
            etiqueta=_etiqueta_bloque(n, _descripcion_tipo("Calculo")),
            preguntas_restantes=n,
            tipo="Calculo",
        )
    )
    opciones.append(
        BloqueFiltroActivo(
            etiqueta=_etiqueta_bloque(n, _descripcion_tipo("Teoria")),
            preguntas_restantes=n,
            tipo="Teoria",
        )
    )
    if grupos:
        g = rng.choice(grupos)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=_etiqueta_bloque(n, _descripcion_grupo_tematico(g, pool)),
                preguntas_restantes=n,
                grupo=g,
            )
        )
    cursos = _cursos_en_pool(pool)
    if cursos:
        curso = rng.choice(cursos)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=_etiqueta_bloque(n, _descripcion_curso(curso)),
                preguntas_restantes=n,
                curso=curso,
            )
        )
    pares_cs = _pares_curso_semestre_en_pool(pool)
    if pares_cs:
        curso, semestre = rng.choice(pares_cs)
        opciones.append(
            BloqueFiltroActivo(
                etiqueta=_etiqueta_bloque(n, _descripcion_semestre(curso, semestre)),
                preguntas_restantes=n,
                curso=curso,
                semestre=semestre,
            )
        )
    return rng.choice(opciones)


def _riesgo_apuesta(apuesta: ApuestaRiesgo) -> float:
    r = apuesta.recompensa
    c = apuesta.coste
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


def _elegir_apuesta(rng: random.Random, numero_pregunta: int) -> ApuestaRiesgo:
    """Elige una apuesta; al avanzar la partida pesan más las de mayor riesgo."""
    t = factor_progreso_resistencia(numero_pregunta)
    centro = 1.0 + t * 4.5
    pesos = [1.0 / (0.6 + abs(_riesgo_apuesta(ap) - centro)) for ap in APUESTAS_DISPONIBLES]
    return rng.choices(APUESTAS_DISPONIBLES, weights=pesos, k=1)[0]


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
    return _elegir_apuesta(rng, numero_pregunta)


def _texto_recompensa_apuesta(recompensa: RecompensaApuesta) -> str:
    from Comun.powerups_resistencia import etiqueta_powerup

    partes: list[str] = []
    if recompensa.mult_puntos > 1:
        partes.append(f"×{recompensa.mult_puntos} puntos")
    if recompensa.delta_vidas > 0:
        n = recompensa.delta_vidas
        partes.append(f"+{n} vida" + ("s" if n > 1 else ""))
    if recompensa.powerup_id:
        nom = etiqueta_powerup(recompensa.powerup_id)
        if recompensa.cantidad_powerup > 1:
            partes.append(f"{recompensa.cantidad_powerup}× {nom}")
        else:
            partes.append(f"objeto {nom}")
    elif recompensa.powerup_aleatorio:
        partes.append("un objeto al azar")
    return ", ".join(partes) if partes else "sin bonus extra"


def _texto_coste_apuesta(coste: CosteApuesta) -> str:
    if coste.fin_partida:
        return "la partida termina al instante"
    partes: list[str] = []
    if coste.vidas_fallo <= 1:
        partes.append("pierdes 1 vida como de costumbre")
    else:
        partes.append(f"pierdes {coste.vidas_fallo} vidas")
    if coste.puntos_perdidos > 0:
        partes.append(f"−{coste.puntos_perdidos} puntos")
    if coste.pierde_todos_objetos:
        partes.append("pierdes todos los objetos")
    elif coste.pierde_powerup_aleatorio:
        partes.append("pierdes un objeto al azar")
    return "; ".join(partes)


def formatear_aviso_apuesta(apuesta: ApuestaRiesgo) -> str:
    recomp = _texto_recompensa_apuesta(apuesta.recompensa)
    coste = _texto_coste_apuesta(apuesta.coste)
    texto = f"{apuesta.etiqueta}: si aciertas, {recomp}; si fallas, {coste}."
    return prefijar_emoji(texto, "🎰")


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
    """Sin bloque activo: todas las preguntas del pool del momento son válidas."""
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
