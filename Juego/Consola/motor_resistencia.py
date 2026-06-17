#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Partida de resistencia (modo historia) en consola."""

from __future__ import annotations

from Comun.cierre_informe import meta_cierre_historia
from Comun.estado_resistencia import EstadoResistencia
from Comun.modelos import Pregunta
from Comun.motor_nucleo import EstadoPartida, FeedbackRespuesta, ResultadoRespuesta, linea_estado
from Comun.motor_resistencia_comun import (
    aplicar_bonificaciones_puntos_resistencia,
    aplicar_modificadores_visuales_escalada,
    crear_estado_resistencia,
    procesar_turno_resistencia,
    texto_pregunta_para_turno,
    tiempo_pregunta_efectivo,
    usar_powerup,
)
from Comun.iconos_resistencia import emoji_powerup, prefijar_emoji
from Comun.powerups_resistencia import descripcion_powerup, etiqueta_powerup
from Comun.ranking_resistencia import registrar_partida
from Comun.reglas_partida import ReglasPartida, formatear_resultado_puntuacion
from Comun.resistencia_historia import (
    aplicar_escalada_a_reglas,
    construir_pool_resistencia,
    crear_seleccion_resistencia,
    elegir_indice_resistencia,
    escalada_para_pregunta,
    etiqueta_tier_exclusiva,
    texto_efectos_escalada,
)
from Comun.rutas import resolver_ranking_resistencia
from Consola.consola import pedir_menu_numerado
from Consola.informe_examen import RegistroRespuesta, publicar_informe_partida
from Consola.motor_partida import (
    mostrar_resumen_partida,
    preguntar_con_reglas,
    registrar_contexto_pregunta,
)
from Consola.navegacion import IrMenuPrincipal, SalirPrograma, establecer_contexto
from Consola.textos_consola import campo, con_emoji, feedback as feedback_ui


def _progreso_resistencia(er: EstadoResistencia, numero_pregunta: int) -> str:
    return f"#{numero_pregunta} · Racha {er.racha}"


def _mostrar_feedback_turno(fb: FeedbackRespuesta, *, recompensa: str | None = None) -> None:
    if fb.mensaje == "Respuesta registrada.":
        return
    msg = feedback_ui(fb.mensaje)
    if fb.mensaje.startswith("Correcto"):
        print(f"[OK] {msg}")
    elif fb.mensaje.startswith("Incorrecto"):
        print(f"[X] {msg}")
    else:
        print(f"[!] {msg}")
    if fb.solucion:
        print(fb.solucion)
    if recompensa:
        print(f"[+] {recompensa}")
    if fb.sin_vidas:
        print(f"\n{con_emoji('Te has quedado sin vidas.', '💔')}")


def _menu_powerup(er: EstadoResistencia) -> str | None:
    items = [(pid, n) for pid, n in sorted(er.inventario.items()) if n > 0]
    if not items:
        return None
    opciones: list[tuple[str, str]] = [("0", "Responder sin usar objeto")]
    for i, (pid, n) in enumerate(items, start=1):
        opciones.append(
            (
                str(i),
                f"{prefijar_emoji(f'{etiqueta_powerup(pid)} ×{n}', emoji_powerup(pid))} — {descripcion_powerup(pid)}",
            )
        )
    idx = pedir_menu_numerado("Inventario (opcional):", opciones, defecto=1)
    if idx == 1:
        return None
    return items[idx - 2][0]


def ejecutar_resistencia_historia(
    preguntas: list[Pregunta],
    *,
    nombre: str,
    reglas: ReglasPartida,
    preset_id: str,
    preset_nombre: str,
    perfil: str,
    materias_meta: dict[str, dict[str, str]] | None = None,
    stats_historicas: dict | None = None,
) -> EstadoPartida:
    pool = construir_pool_resistencia(preguntas, materias_meta or {})
    if not pool:
        raise ValueError("No hay preguntas para el modo resistencia.")

    er = crear_estado_resistencia(reglas.vidas or 3)
    escalada = escalada_para_pregunta(1)
    estado = EstadoPartida(
        nombre=nombre,
        reglas=aplicar_escalada_a_reglas(reglas, escalada),
        vidas_restantes=min(reglas.vidas or 3, er.vidas_max),
    )
    seleccion = crear_seleccion_resistencia(pool)
    registros: list[RegistroRespuesta] = []
    indice = 0

    while estado.debe_continuar(None):
        er.reset_pregunta()
        indice += 1
        escalada = escalada_para_pregunta(indice)
        estado.reglas = aplicar_escalada_a_reglas(reglas, escalada)
        idx = elegir_indice_resistencia(pool, seleccion, escalada, indice)
        if idx is None:
            break
        p = pool[idx]
        aplicar_modificadores_visuales_escalada(er, escalada, p, indice)
        texto_mostrar = texto_pregunta_para_turno(p, er)
        progreso = _progreso_resistencia(er, indice)
        extra = texto_efectos_escalada(escalada)
        if p.exclusiva_resistencia:
            tier = etiqueta_tier_exclusiva(p)
            extra = f"★ Pregunta exclusiva ({tier})" + (f" · {extra}" if extra else "")
        if er.inventario:
            inv = er.inventario_resumen()
            extra = (extra + " · " if extra else "") + f"Inventario: {inv}"
        registrar_contexto_pregunta(
            p,
            estado,
            indice=indice,
            total=None,
            etiqueta="Resistencia",
            extra_meta=extra,
            progreso=linea_estado(estado, progreso, vidas_max=er.vidas_max),
            letras_ocultas=er.letras_ocultas,
            texto_pregunta=texto_mostrar,
        )
        try:
            while True:
                powerup = _menu_powerup(er)
                if powerup == "skip":
                    err = usar_powerup("skip", er, p)
                    if err:
                        print(f"[!] {err}")
                        continue
                    print("[i] Pregunta saltada.")
                    break
                if powerup:
                    err = usar_powerup(powerup, er, p)
                    if err:
                        print(f"[!] {err}")
                        continue
                    if powerup in {"fifty_fifty", "bomba"}:
                        registrar_contexto_pregunta(
                            p,
                            estado,
                            indice=indice,
                            total=None,
                            etiqueta="Resistencia",
                            extra_meta=extra,
                            progreso=linea_estado(estado, progreso, vidas_max=er.vidas_max),
                            letras_ocultas=er.letras_ocultas,
                            texto_pregunta=texto_pregunta_para_turno(p, er),
                        )
                    elif powerup == "tiempo_extra":
                        print("[i] +20 s en esta pregunta.")
                    elif powerup == "escudo":
                        print("[i] Escudo activo para el próximo fallo.")
                    continue

                resultado = preguntar_con_reglas(
                    p,
                    estado,
                    letras_ocultas=er.letras_ocultas,
                    tiempo_extra_seg=er.tiempo_extra_seg,
                )
                puntos_prev = estado.puntos_arcade
                turno = procesar_turno_resistencia(
                    estado, er, p, resultado, indice_pregunta=indice
                )
                aplicar_bonificaciones_puntos_resistencia(
                    estado,
                    puntos_prev=puntos_prev,
                    racha=er.racha,
                    mult_escalada=escalada.multiplicador_puntos,
                    exclusiva=p.exclusiva_resistencia,
                    acierto=resultado.acierto,
                    tiempo_agotado=resultado.tiempo_agotado,
                )
                recompensa_txt = turno.recompensa.etiqueta if turno.recompensa else None
                _mostrar_feedback_turno(turno.feedback, recompensa=recompensa_txt)
                if turno.reintentar_pregunta:
                    registrar_contexto_pregunta(
                        p,
                        estado,
                        indice=indice,
                        total=None,
                        etiqueta="Resistencia",
                        extra_meta=extra,
                        progreso=linea_estado(
                            estado, _progreso_resistencia(er, indice), vidas_max=er.vidas_max
                        ),
                        letras_ocultas=er.letras_ocultas,
                        texto_pregunta=texto_pregunta_para_turno(p, er),
                    )
                    continue
                registros.append(
                    RegistroRespuesta(
                        indice=estado.respondidas,
                        pregunta=p,
                        respuesta=resultado.respuesta,
                        acierto=resultado.acierto,
                        tiempo_agotado=resultado.tiempo_agotado,
                    )
                )
                break
        except IrMenuPrincipal:
            establecer_contexto(None)
            return estado
        except SalirPrograma:
            raise

    establecer_contexto(None)
    if estado.respondidas > 0:
        posicion: int | None = None
        try:
            _, posicion = registrar_partida(
                resolver_ranking_resistencia(),
                nombre=nombre,
                racha=er.mejor_racha,
                puntos=estado.puntos_arcade,
                respondidas=estado.respondidas,
                preset_id=preset_id,
            )
        except ValueError:
            posicion = None

        mostrar_resumen_partida(
            estado,
            f"FIN RACHA — {preset_nombre}",
            estado.respondidas,
        )
        print(f"\n{campo('racha', f'Preguntas respondidas: {estado.respondidas}. Mejor racha (puntos): {er.mejor_racha}.')}")
        print(formatear_resultado_puntuacion(
            reglas,
            aciertos=estado.aciertos,
            total=estado.respondidas,
            puntos_arcade=estado.puntos_arcade,
        ))
        if posicion is not None:
            print(f"{campo('ranking_pos', f'Posición en ranking local: #{posicion}')}")

        publicar_informe_partida(
            estado,
            registros,
            titulo=f"FIN RACHA — {preset_nombre}",
            total_previsto=estado.respondidas,
            nombre_jugador=nombre,
            meta=meta_cierre_historia(
                preset_id=preset_id,
                preset_nombre=preset_nombre,
                perfil=perfil,
                materias=[],
                n_preguntas=estado.respondidas,
                modo_resistencia=True,
                racha=er.mejor_racha,
            ),
            stats_historicas=stats_historicas,
            prefijo="resistencia",
        )
    return estado
