#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lógica compartida del modo resistencia (consola y gráfico)."""

from __future__ import annotations

from dataclasses import dataclass, replace

from Comun.estado_resistencia import (
    VIDAS_MAX_ABSOLUTO,
    VIDAS_MIN_CAP,
    EstadoResistencia,
)
from Comun.mecanicas_resistencia import (
    aplicar_efectos_maldicion,
    aplicar_presion_racha_modificadores,
    configurar_partida_resistencia,
    consumir_bloque_filtro,
    elegir_indice_similar,
    formatear_aviso_apuesta,
    preparar_eventos_nuevo_turno,
    procesar_post_turno_resistencia,
    rng_partida,
    texto_progreso_resistencia,
)
from Comun.modelos import Pregunta
from Comun.motor_nucleo import EstadoPartida, FeedbackRespuesta, ResultadoRespuesta, evaluar_respuesta
from Comun.powerups_resistencia import (
    EventoRecompensaResistencia,
    POWERUPS_LOOT,
    etiqueta_powerup,
    letras_ocultas_fifty_fifty,
    letras_ocultas_bomba,
    letras_ocultas_por_cantidad,
    texto_pregunta_visible,
    tirar_recompensas_tras_acierto,
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
    avisos_extra: list[str] | None = None,
    er: EstadoResistencia | None = None,
) -> list[str]:
    """Mensajes para popup antes de mostrar la pregunta.

    No hay tope global de popups: se encolan todos los avisos (recompensas
    previas, bloques, apuestas, eventos de escalada, exclusivas…). Los únicos
    límites numéricos están en la generación de eventos aleatorios y en las
    tiradas de recompensa tras acierto (la racha extrema puede superar el tope
    habitual de eventos hostiles).
    """
    avisos: list[str] = []
    if avisos_extra:
        avisos.extend(avisos_extra)
    if er is not None:
        apuesta_aviso = aviso_apuesta_activa(er)
        if apuesta_aviso:
            avisos.append(apuesta_aviso)
    for evento in eventos_aleatorios_para_pregunta(
        numero_pregunta,
        semilla_partida=er.semilla_partida if er else None,
        racha=er.racha if er is not None else 0,
    ):
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


def aviso_apuesta_activa(er: EstadoResistencia) -> str | None:
    if not er.apuesta_activa:
        return None
    return formatear_aviso_apuesta(er.apuesta_activa)


@dataclass(frozen=True)
class ResultadoTurnoResistencia:
    feedback: FeedbackRespuesta
    reintentar_pregunta: bool = False
    avisos_extra: tuple[str, ...] = ()
    mult_apuesta: int = 1


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
    aplicar_presion_racha_modificadores(er, p, numero_pregunta)
    aplicar_efectos_maldicion(er)


def texto_pregunta_para_turno(p: Pregunta, er: EstadoResistencia) -> str:
    return texto_pregunta_visible(p.texto, er.fraccion_enunciado)


def tiempo_pregunta_efectivo(reglas_seg: int | None, er: EstadoResistencia) -> int | None:
    if er.relampago_forzado_seg is not None:
        base = er.relampago_forzado_seg
    elif reglas_seg is None:
        return None
    else:
        base = reglas_seg
    return max(3, base + er.tiempo_extra_seg)


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
    if er.objetos_bloqueados:
        return "Maldición activa: no puedes usar objetos."
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
    elif powerup_id == "cambio":
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
    mult_apuesta: int = 1,
) -> None:
    """Aplica multiplicadores de escalada, racha, apuesta y pregunta exclusiva."""
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
    if mult_apuesta > 1:
        extra += delta * (mult_apuesta - 1)
    if extra > 0:
        estado.puntos_arcade += int(extra)


def _aplicar_recompensa_apuesta_exito(
    estado: EstadoPartida,
    er: EstadoResistencia,
    *,
    numero_pregunta: int,
) -> list[str]:
    if not er.apuesta_activa:
        return []
    recompensa = er.apuesta_activa.recompensa
    avisos: list[str] = []
    if recompensa.delta_vidas:
        aplicar_recompensa(
            estado,
            er,
            EventoRecompensaResistencia(
                "Apuesta: vida extra",
                delta_vidas=recompensa.delta_vidas,
            ),
        )
        n = recompensa.delta_vidas
        avisos.append(f"Apuesta: +{n} vida" + ("s" if n > 1 else ""))
    if recompensa.powerup_id:
        er.agregar_powerup(recompensa.powerup_id, recompensa.cantidad_powerup)
        nom = etiqueta_powerup(recompensa.powerup_id)
        avisos.append(f"Apuesta: {nom}")
    elif recompensa.powerup_aleatorio:
        rng = rng_partida(er, numero_pregunta * 19 + 7701)
        pid = rng.choice(POWERUPS_LOOT)
        er.agregar_powerup(pid, 1)
        avisos.append(f"Apuesta: {etiqueta_powerup(pid)}")
    return avisos


def _aplicar_penalizacion_apuesta(
    estado: EstadoPartida,
    er: EstadoResistencia,
    *,
    fallo: bool,
    numero_pregunta: int,
) -> tuple[bool, list[str]]:
    """Penalización de la apuesta activa. Devuelve (fin_partida, avisos)."""
    if not fallo or not er.apuesta_activa:
        return False, []
    coste = er.apuesta_activa.coste
    avisos: list[str] = []
    if coste.fin_partida:
        if estado.vidas_restantes is not None:
            estado.vidas_restantes = 0
        avisos.append("Apuesta perdida: fin de partida.")
        return True, avisos
    extra = max(0, coste.vidas_fallo - 1)
    if extra > 0 and estado.vidas_restantes is not None:
        estado.vidas_restantes = max(0, estado.vidas_restantes - extra)
    if coste.puntos_perdidos > 0:
        estado.puntos_arcade = max(0, estado.puntos_arcade - coste.puntos_perdidos)
        avisos.append(f"Apuesta: −{coste.puntos_perdidos} puntos")
    if coste.pierde_todos_objetos and er.inventario:
        er.inventario.clear()
        avisos.append("Apuesta: pierdes todos los objetos")
    elif coste.pierde_powerup_aleatorio and er.inventario:
        rng = rng_partida(er, numero_pregunta * 23 + 8803)
        candidatos = [pid for pid, n in er.inventario.items() if n > 0]
        if candidatos:
            pid = rng.choice(candidatos)
            er.consumir_powerup(pid)
            avisos.append(f"Apuesta: pierdes {etiqueta_powerup(pid)}")
    return False, avisos


def procesar_turno_resistencia(
    estado: EstadoPartida,
    er: EstadoResistencia,
    p: Pregunta,
    resultado: ResultadoRespuesta,
    *,
    indice_pregunta: int,
) -> ResultadoTurnoResistencia:
    """Evalúa la respuesta del jugador. Las vidas solo bajan por fallo o tiempo agotado."""
    acierto = resultado.acierto and not resultado.tiempo_agotado
    fallo = not acierto
    mult_apuesta = 1
    if acierto and er.apuesta_activa:
        mult_apuesta = max(1, er.apuesta_activa.recompensa.mult_puntos)

    if fallo and er.escudo_activo:
        er.escudo_activo = False
        solucion = None
        if estado.reglas.mostrar_solucion_tras_fallo and not er.sin_pistas_turno:
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
    if er.sin_pistas_turno and feedback.solucion:
        feedback = replace(feedback, solucion=None)

    _fin_apuesta, avisos_apuesta_fallo = _aplicar_penalizacion_apuesta(
        estado,
        er,
        fallo=fallo,
        numero_pregunta=indice_pregunta,
    )
    if fallo and estado.reglas.tiene_vidas() and (estado.vidas_restantes or 0) <= 0:
        feedback = replace(feedback, sin_vidas=True)
    elif fallo and _fin_apuesta:
        feedback = replace(feedback, sin_vidas=True)

    avisos_post: list[str] = list(avisos_apuesta_fallo)
    if acierto:
        er.registrar_acierto()
        avisos_post.extend(
            _aplicar_recompensa_apuesta_exito(
                estado, er, numero_pregunta=indice_pregunta
            )
        )
        for recompensa in tirar_recompensas_tras_acierto(er, numero_pregunta=indice_pregunta):
            aplicar_recompensa(estado, er, recompensa)
            avisos_post.append(formatear_aviso_recompensa(recompensa.etiqueta))
    elif fallo:
        er.registrar_fallo()

    avisos_post.extend(
        procesar_post_turno_resistencia(er, acierto=acierto, numero_pregunta=indice_pregunta)
    )

    if acierto and er.apuesta_activa:
        msg = feedback.mensaje
        if msg.startswith("Correcto"):
            extras_apuesta: list[str] = []
            if mult_apuesta > 1:
                extras_apuesta.append(f"×{mult_apuesta}")
            r = er.apuesta_activa.recompensa
            if r.delta_vidas > 0:
                extras_apuesta.append(f"+{r.delta_vidas} vida" + ("s" if r.delta_vidas > 1 else ""))
            if r.powerup_id or r.powerup_aleatorio:
                extras_apuesta.append("objeto")
            if extras_apuesta:
                feedback = replace(
                    feedback,
                    mensaje=f"{msg} (apuesta: {', '.join(extras_apuesta)})",
                )

    return ResultadoTurnoResistencia(
        feedback=feedback,
        avisos_extra=tuple(avisos_post),
        mult_apuesta=mult_apuesta if acierto else 1,
    )


__all__ = [
    "ResultadoTurnoResistencia",
    "aplicar_bonificaciones_puntos_resistencia",
    "aplicar_modificadores_visuales_escalada",
    "aplicar_recompensa",
    "aviso_apuesta_activa",
    "avisos_pre_pregunta_resistencia",
    "bonificacion_puntos_racha",
    "configurar_partida_resistencia",
    "consumir_bloque_filtro",
    "crear_estado_resistencia",
    "elegir_indice_similar",
    "formatear_aviso_apuesta",
    "formatear_aviso_evento",
    "formatear_aviso_recompensa",
    "preparar_eventos_nuevo_turno",
    "texto_pregunta_para_turno",
    "procesar_turno_resistencia",
    "texto_progreso_resistencia",
    "tiempo_pregunta_efectivo",
    "usar_powerup",
]
