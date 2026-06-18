#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motor de partida: núcleo en ``Comun`` y E/S de consola aquí."""

from __future__ import annotations

import time

from Consola.textos_consola import campo, con_emoji, feedback as feedback_ui, titulo as titulo_ui
from Comun.modelos import Pregunta
from Comun.motor_nucleo import (
    EstadoPartida,
    FeedbackRespuesta,
    ResultadoRespuesta,
    evaluar_respuesta,
    linea_estado,
    texto_solucion,
)
from Comun.reglas_partida import ReglasPartida, SistemaPuntuacion, formatear_resultado_puntuacion

from .consola import pedir_opcion
from .navegacion import ContextoPantalla, IrMenuPrincipal, SalirPrograma, establecer_contexto

__all__ = [
    "EstadoPartida",
    "FeedbackRespuesta",
    "ResultadoRespuesta",
    "aplicar_respuesta",
    "ejecutar_lista_fija",
    "evaluar_respuesta",
    "linea_estado",
    "mostrar_pregunta",
    "mostrar_resumen_partida",
    "preguntar_con_reglas",
    "registrar_contexto_pregunta",
]


def mostrar_pregunta(
    p: Pregunta,
    *,
    indice: int,
    total: int | None,
    etiqueta: str = "Pregunta",
    extra_meta: str | None = None,
    linea_estado: str | None = None,
    nombre_jugador: str | None = None,
    letras_ocultas: frozenset[str] | None = None,
    texto_pregunta: str | None = None,
) -> None:
    print("\n" + "=" * 60)
    if nombre_jugador:
        print(f"Jugador: {nombre_jugador}")
    if linea_estado:
        print(linea_estado)
    else:
        total_txt = str(total) if total is not None else "inf"
        print(f"{etiqueta} {indice}/{total_txt}")
    if extra_meta:
        print(extra_meta)
    print(f"Materia: {p.materia} | {p.tipo} / {p.dificultad}")
    print(f"Tematica: {p.tematica or '-'} | Curso {p.curso or '-'} · Sem. {p.semestre or '-'}")
    print(f"\n{texto_pregunta if texto_pregunta is not None else p.texto}")
    ocultas = letras_ocultas or frozenset()
    for letra in ("A", "B", "C", "D"):
        if letra in ocultas:
            continue
        print(f"  {letra}) {p.opciones.get(letra, '(opción no disponible)')}")


def registrar_contexto_pregunta(
    p: Pregunta,
    estado: EstadoPartida,
    *,
    indice: int,
    total: int | None,
    etiqueta: str = "Pregunta",
    extra_meta: str | None = None,
    progreso: str | None = None,
    letras_ocultas: frozenset[str] | None = None,
    texto_pregunta: str | None = None,
) -> None:
    linea = progreso or linea_estado(estado, f"{etiqueta} {indice}/{total or 'inf'}")
    kwargs = dict(
        p=p,
        indice=indice,
        total=total,
        etiqueta=etiqueta,
        extra_meta=extra_meta,
        linea_estado=linea,
        nombre_jugador=estado.nombre,
        letras_ocultas=letras_ocultas,
        texto_pregunta=texto_pregunta,
    )

    def _reimprimir() -> None:
        mostrar_pregunta(**kwargs)

    total_txt = str(total) if total is not None else "inf"
    establecer_contexto(
        ContextoPantalla(
            titulo=f"Partida — {etiqueta} {indice}/{total_txt}",
            lineas=[
                f"Reglas: {estado.reglas.describe()}",
                "Pulsa H para ver controles.",
            ],
            reimprimir=_reimprimir,
        )
    )
    _reimprimir()


def aplicar_respuesta(
    p: Pregunta,
    estado: EstadoPartida,
    resultado: ResultadoRespuesta,
) -> None:
    fb = evaluar_respuesta(p, estado, resultado)
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
    if fb.sin_vidas:
        print(f"\n{con_emoji('Te has quedado sin vidas.', '💔')}")


def preguntar_con_reglas(
    p: Pregunta,
    estado: EstadoPartida,
    *,
    letras_ocultas: frozenset[str] | None = None,
    tiempo_extra_seg: int = 0,
    limite_pregunta_seg: int | None = None,
) -> ResultadoRespuesta:
    if limite_pregunta_seg is not None:
        lim_p = limite_pregunta_seg
    else:
        lim_p = estado.reglas.tiempo_por_pregunta_seg
        if lim_p is not None:
            lim_p = lim_p + tiempo_extra_seg
    if lim_p:
        print(f"(Tienes hasta {lim_p}s para responder)")
    inicio = time.monotonic()
    opciones_validas = [
        letra
        for letra in ("A", "B", "C", "D")
        if letra not in (letras_ocultas or frozenset())
    ]
    if not opciones_validas:
        opciones_validas = ["A", "B", "C", "D"]
    respuesta = pedir_opcion(
        "\nTu respuesta: ",
        opciones_validas,
        default=opciones_validas[0],
        permitir_atras=False,
        en_partida=True,
    )
    transcurrido = time.monotonic() - inicio

    tiempo_agotado = False
    if lim_p and transcurrido > lim_p:
        tiempo_agotado = True
    if estado.tiempo_total_restante() == 0:
        tiempo_agotado = True

    if tiempo_agotado:
        return ResultadoRespuesta(acierto=False, respuesta=respuesta, tiempo_agotado=True)

    correcta = p.correcta if p.correcta in {"A", "B", "C", "D"} else ""
    return ResultadoRespuesta(
        acierto=respuesta == correcta and bool(correcta),
        respuesta=respuesta,
    )


def ejecutar_lista_fija(
    preguntas: list[Pregunta],
    *,
    nombre: str,
    reglas: ReglasPartida,
    titulo_fin: str = "FIN DEL BLOQUE",
    etiqueta: str = "Pregunta",
    guardar_informe: bool = False,
    meta_informe: dict | None = None,
    stats_historicas: dict | None = None,
) -> EstadoPartida:
    from .informe_examen import RegistroRespuesta, publicar_informe_partida

    estado = EstadoPartida(
        nombre=nombre,
        reglas=reglas,
        vidas_restantes=reglas.vidas,
    )
    total = len(preguntas)
    registrar_detalle = guardar_informe or reglas.correccion_al_final
    registros: list[RegistroRespuesta] = []
    abandonado = False

    for i, p in enumerate(preguntas, start=1):
        if not estado.debe_continuar(total):
            if estado.tiempo_total_restante() == 0:
                print(f"\n{con_emoji('Tiempo total del bloque agotado.', '⏱️')}")
            break

        progreso = linea_estado(estado, f"{etiqueta} {i}/{total}")
        registrar_contexto_pregunta(
            p,
            estado,
            indice=i,
            total=total,
            etiqueta=etiqueta,
            progreso=progreso,
        )

        try:
            resultado = preguntar_con_reglas(p, estado)
            aplicar_respuesta(p, estado, resultado)
            if registrar_detalle:
                registros.append(
                    RegistroRespuesta(
                        indice=i,
                        pregunta=p,
                        respuesta=resultado.respuesta,
                        acierto=resultado.acierto,
                        tiempo_agotado=resultado.tiempo_agotado,
                    )
                )
        except IrMenuPrincipal:
            abandonado = True
            print(f"\n{con_emoji('Partida abandonada. Volviendo al menú principal.', '🏠')}")
            break
        except SalirPrograma:
            raise

        if not estado.debe_continuar(total):
            break

    establecer_contexto(None)
    if estado.respondidas > 0:
        from .navegacion import limpiar_consola

        limpiar_consola()
        mostrar_resumen_partida(estado, titulo_fin, total)
        if guardar_informe and registros:
            publicar_informe_partida(
                estado,
                registros,
                titulo=titulo_fin,
                total_previsto=total,
                nombre_jugador=nombre,
                meta={**(meta_informe or {}), "abandonado": abandonado},
                stats_historicas=stats_historicas,
                prefijo="examen",
            )
    return estado


def mostrar_resumen_partida(estado: EstadoPartida, titulo: str, total_bloque: int) -> None:
    total = estado.respondidas
    previsto = total_bloque if total_bloque > 0 else total
    incompleto = previsto > total

    print("\n" + "=" * 60)
    print(titulo_ui(titulo))
    print(campo("jugador", f"Jugador: {estado.nombre}"))
    if incompleto:
        print(f"Preguntas respondidas: {total}/{previsto}")
    print(formatear_resultado_puntuacion(
        estado.reglas,
        aciertos=estado.aciertos,
        total=total,
        puntos_arcade=estado.puntos_arcade,
    ))
    if estado.reglas.sistema_puntuacion != SistemaPuntuacion.ARCADE:
        print(f"Resumen: {estado.aciertos}/{total} aciertos")
