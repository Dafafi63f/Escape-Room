#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lógica compartida del modo resistencia (consola y gráfico)."""

from __future__ import annotations

from dataclasses import dataclass

from Comun.estado_resistencia import (
    VIDAS_MAX_ABSOLUTO,
    VIDAS_MIN_CAP,
    EstadoResistencia,
)
from Comun.modelos import Pregunta
from Comun.motor_nucleo import EstadoPartida, FeedbackRespuesta, ResultadoRespuesta, evaluar_respuesta
from Comun.powerups_resistencia import (
    EventoRecompensaResistencia,
    evento_recompensa_aleatoria,
    letras_ocultas_fifty_fifty,
    letras_ocultas_bomba,
    letras_ocultas_por_cantidad,
    texto_pregunta_visible,
)
from Comun.iconos_resistencia import (
    emoji_aviso_exclusiva,
    emoji_evento_etiqueta,
    emoji_recompensa_etiqueta,
    prefijar_emoji,
)
from Comun.resistencia_historia import (
    EscaladaResistencia,
    etiqueta_tier_exclusiva,
    eventos_aleatorios_para_pregunta,
)


def formatear_aviso_recompensa(etiqueta: str) -> str:
    if etiqueta.startswith("Objeto: "):
        texto = f"¡Obtuviste {etiqueta.removeprefix('Objeto: ')}!"
    else:
        texto = etiqueta
    return prefijar_emoji(texto, emoji_recompensa_etiqueta(etiqueta))


def formatear_aviso_evento(etiqueta: str) -> str:
    if etiqueta.startswith("Relámpago"):
        seg = etiqueta.split(":")[-1].strip() if ":" in etiqueta else ""
        texto = f"¡Pregunta relámpago!{f' {seg}' if seg else ''}"
    elif etiqueta in {"Doble puntos", "Triple puntos"}:
        texto = f"¡{etiqueta} en esta pregunta!"
    elif etiqueta.startswith("Niebla:"):
        if "enunciado" in etiqueta:
            texto = "¡Parte del enunciado estará oculta!"
        else:
            texto = f"¡{etiqueta}!"
    elif etiqueta in {"Pregunta difícil", "Pregunta extra difícil"}:
        texto = f"¡{etiqueta}!"
    else:
        texto = f"Ahora: {etiqueta}"
    return prefijar_emoji(texto, emoji_evento_etiqueta(etiqueta))


def avisos_pre_pregunta_resistencia(
    p: Pregunta,
    numero_pregunta: int,
    *,
    recompensa_etiqueta: str | None = None,
) -> list[str]:
    """Mensajes para popup antes de mostrar la pregunta."""
    avisos: list[str] = []
    if recompensa_etiqueta:
        avisos.append(formatear_aviso_recompensa(recompensa_etiqueta))
    for evento in eventos_aleatorios_para_pregunta(numero_pregunta):
        avisos.append(formatear_aviso_evento(evento.etiqueta))
    if p.exclusiva_resistencia:
        tier = etiqueta_tier_exclusiva(p)
        if tier:
            avisos.append(
                prefijar_emoji(
                    f"Pregunta exclusiva — {tier}",
                    emoji_aviso_exclusiva(),
                )
            )
    return avisos


@dataclass(frozen=True)
class ResultadoTurnoResistencia:
    feedback: FeedbackRespuesta
    reintentar_pregunta: bool = False
    recompensa: EventoRecompensaResistencia | None = None


def crear_estado_resistencia(vidas_iniciales: int) -> EstadoResistencia:
    er = EstadoResistencia()
    er.vidas_max = max(vidas_iniciales, er.vidas_max)
    return er


def aplicar_modificadores_visuales_escalada(
    er: EstadoResistencia,
    escalada: EscaladaResistencia,
    p: Pregunta,
    numero_pregunta: int,
) -> None:
    """Oculta respuestas o parte del enunciado según eventos de la escalada."""
    er.fraccion_enunciado = escalada.fraccion_enunciado
    if escalada.opciones_ocultas > 0:
        ocultas = letras_ocultas_por_cantidad(
            p,
            escalada.opciones_ocultas,
            semilla=numero_pregunta,
        )
        er.letras_ocultas = er.letras_ocultas | ocultas


def texto_pregunta_para_turno(p: Pregunta, er: EstadoResistencia) -> str:
    return texto_pregunta_visible(p.texto, er.fraccion_enunciado)


def tiempo_pregunta_efectivo(reglas_seg: int | None, er: EstadoResistencia) -> int | None:
    if reglas_seg is None:
        return None
    return reglas_seg + er.tiempo_extra_seg


def aplicar_recompensa(
    estado: EstadoPartida,
    er: EstadoResistencia,
    evento: EventoRecompensaResistencia,
) -> None:
    if evento.delta_vidas_max:
        er.vidas_max = max(
            VIDAS_MIN_CAP,
            min(VIDAS_MAX_ABSOLUTO, er.vidas_max + evento.delta_vidas_max),
        )
        if estado.vidas_restantes is not None and estado.vidas_restantes > er.vidas_max:
            estado.vidas_restantes = er.vidas_max
    if evento.delta_vidas and estado.vidas_restantes is not None:
        estado.vidas_restantes = max(0, min(er.vidas_max, estado.vidas_restantes + evento.delta_vidas))
    if evento.powerup_id:
        er.agregar_powerup(evento.powerup_id, evento.cantidad_powerup)
    er.ultimo_evento = evento.etiqueta


def usar_powerup(
    powerup_id: str,
    er: EstadoResistencia,
    p: Pregunta,
) -> str | None:
    """Consume un comodín; devuelve mensaje de error o None si OK."""
    if not er.consumir_powerup(powerup_id):
        return "No tienes ese objeto."
    if powerup_id == "fifty_fifty":
        er.letras_ocultas = letras_ocultas_fifty_fifty(p)
    elif powerup_id == "bomba":
        ocultas = letras_ocultas_bomba(p)
        er.letras_ocultas = er.letras_ocultas | ocultas
    elif powerup_id == "tiempo_extra":
        er.tiempo_extra_seg += 20
    elif powerup_id == "escudo":
        er.escudo_activo = True
    elif powerup_id == "skip":
        pass
    else:
        return f"Objeto desconocido: {powerup_id}"
    return None


def bonificacion_puntos_racha(racha: int) -> float:
    """Multiplicador de puntos por aciertos seguidos (la racha solo afecta a la puntuación)."""
    if racha < 2:
        return 1.0
    return 1.0 + min(1.0, (racha - 1) * 0.05)


def aplicar_bonificaciones_puntos_resistencia(
    estado: EstadoPartida,
    *,
    puntos_prev: int,
    racha: int,
    mult_escalada: int,
    exclusiva: bool,
    acierto: bool,
    tiempo_agotado: bool,
) -> None:
    """Aplica multiplicadores de escalada, racha y pregunta exclusiva."""
    if not acierto or tiempo_agotado:
        return
    delta = estado.puntos_arcade - puntos_prev
    if delta <= 0:
        return
    extra = 0.0
    if mult_escalada > 1:
        extra += delta * (mult_escalada - 1)
    bonif_racha = bonificacion_puntos_racha(racha)
    if bonif_racha > 1.0:
        extra += delta * (bonif_racha - 1.0)
    if exclusiva:
        extra += delta * 0.5
    if extra > 0:
        estado.puntos_arcade += int(extra)


def procesar_turno_resistencia(
    estado: EstadoPartida,
    er: EstadoResistencia,
    p: Pregunta,
    resultado: ResultadoRespuesta,
    *,
    indice_pregunta: int,
) -> ResultadoTurnoResistencia:
    acierto = resultado.acierto and not resultado.tiempo_agotado
    fallo = not acierto

    if fallo and er.escudo_activo:
        er.escudo_activo = False
        solucion = None
        if estado.reglas.mostrar_solucion_tras_fallo:
            from Comun.motor_nucleo import texto_solucion

            solucion = texto_solucion(p)
        return ResultadoTurnoResistencia(
            feedback=FeedbackRespuesta(
                mensaje="Escudo: el fallo no cuesta vida ni corta la racha.",
                solucion=solucion,
            ),
            reintentar_pregunta=True,
        )

    feedback = evaluar_respuesta(p, estado, resultado)
    recompensa: EventoRecompensaResistencia | None = None
    if acierto:
        er.registrar_acierto()
        recompensa = evento_recompensa_aleatoria(indice_pregunta, semilla=indice_pregunta)
        if recompensa:
            aplicar_recompensa(estado, er, recompensa)
    elif fallo:
        er.registrar_fallo()

    return ResultadoTurnoResistencia(
        feedback=feedback,
        recompensa=recompensa,
    )
