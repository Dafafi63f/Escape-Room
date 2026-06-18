#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guardado de informes .txt desde el modo gráfico."""

from __future__ import annotations

from Comun.cierre_informe import CierreInformePartida
from Comun.preferencias_grafico import guardar_informes_txt_habilitados
from Comun.reglas_partida import SistemaPuntuacion, formatear_resultado_puntuacion
from Consola.informe_examen import RegistroRespuesta, publicar_informe_partida
from Comun.motor_nucleo import EstadoPartida
from Comun.rutas import ruta_informe_para_usuario

__all__ = [
    "CierreInformePartida",
    "guardar_informe_cierre",
    "lineas_resumen_breve",
    "publicar_informe_grafico",
]


def lineas_resumen_breve(
    estado: EstadoPartida,
    total_previsto: int,
    *,
    mostrar_aciertos: bool = True,
    abandonado: bool = False,
) -> list[str]:
    """Pocas líneas para la pantalla; el detalle va al .txt."""
    e = estado
    lineas: list[str] = []
    if abandonado:
        lineas.append("Actividad abandonada (se guardará lo respondido).")
    lineas.append(
        formatear_resultado_puntuacion(
            e.reglas,
            aciertos=e.aciertos,
            total=e.respondidas,
            puntos_arcade=e.puntos_arcade,
        )
    )
    if mostrar_aciertos and (
        e.reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE
        or e.reglas.correccion_al_final
    ):
        if e.reglas.sistema_puntuacion != SistemaPuntuacion.PORCENTAJE:
            lineas.append(f"Aciertos: {e.aciertos}/{e.respondidas}")
    if e.respondidas < total_previsto:
        lineas.append(f"Preguntas respondidas: {e.respondidas}/{total_previsto}")
    if guardar_informes_txt_habilitados():
        lineas.append(
            "Cada partida genera su propio .txt en Juego/Informes/ al salir del resumen."
        )
    else:
        lineas.append("Los informes .txt están desactivados en Opciones.")
    return lineas


def publicar_informe_grafico(
    estado: EstadoPartida,
    registros: list[RegistroRespuesta],
    *,
    titulo: str,
    total_previsto: int,
    prefijo: str,
    meta: dict | None = None,
    stats_historicas: dict | None = None,
    abandonado: bool = False,
) -> str | None:
    """Guarda un informe nuevo en disco (nunca sobrescribe otros de la misma sesión)."""
    if not registros:
        return None
    ruta = publicar_informe_partida(
        estado,
        registros,
        titulo=titulo,
        total_previsto=total_previsto,
        nombre_jugador=estado.nombre,
        meta={**(meta or {}), "abandonado": abandonado},
        stats_historicas=stats_historicas,
        prefijo=prefijo,
        mostrar_en_consola=False,
    )
    if ruta is None:
        return None
    return ruta_informe_para_usuario(ruta)


def guardar_informe_cierre(
    estado: EstadoPartida,
    cierre: CierreInformePartida,
) -> str | None:
    return publicar_informe_grafico(
        estado,
        cierre.registros,
        titulo=cierre.titulo,
        total_previsto=cierre.total_previsto,
        prefijo=cierre.prefijo,
        meta=cierre.meta,
        stats_historicas=cierre.stats_historicas,
        abandonado=cierre.abandonado,
    )
