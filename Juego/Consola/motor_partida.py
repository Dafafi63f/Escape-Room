#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motor común: preguntar, aplicar reglas (vidas/tiempo) y resumir resultados."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .consola import pedir_opcion
from .navegacion import ContextoPantalla, IrMenuPrincipal, SalirPrograma, establecer_contexto
from .modelos import Pregunta
from .reglas_partida import (
    ReglasPartida,
    SistemaPuntuacion,
    calcular_puntos_arcade,
    formatear_resultado_puntuacion,
)


@dataclass
class EstadoPartida:
    nombre: str
    reglas: ReglasPartida
    vidas_restantes: int | None
    aciertos: int = 0
    respondidas: int = 0
    puntos_arcade: int = 0
    fallos_por_materia: dict[str, int] = field(default_factory=dict)
    inicio_total: float = field(default_factory=time.monotonic)

    def tiempo_total_restante(self) -> int | None:
        lim = self.reglas.tiempo_total_seg
        if not lim:
            return None
        rest = int(lim - (time.monotonic() - self.inicio_total))
        return max(0, rest)

    def debe_continuar(self, total_previsto: int | None) -> bool:
        if self.reglas.tiene_vidas() and (self.vidas_restantes or 0) <= 0:
            return False
        if total_previsto is not None and self.respondidas >= total_previsto:
            return False
        rest = self.tiempo_total_restante()
        if rest is not None and rest <= 0:
            return False
        return True


@dataclass
class ResultadoRespuesta:
    acierto: bool
    respuesta: str = ""
    tiempo_agotado: bool = False


def linea_estado(estado: EstadoPartida, progreso: str) -> str:
    partes = [progreso]
    if estado.reglas.tiene_vidas():
        partes.append(f"Vidas: {estado.vidas_restantes}")
    rest = estado.tiempo_total_restante()
    if rest is not None:
        partes.append(f"Tiempo restante: {rest}s")
    if estado.reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE:
        partes.append(f"Puntos: {estado.puntos_arcade}")
    elif estado.reglas.mostrar_aciertos_en_curso and estado.respondidas > 0:
        partes.append(f"Aciertos: {estado.aciertos}/{estado.respondidas}")
    return " | ".join(partes)


def mostrar_pregunta(
    p: Pregunta,
    *,
    indice: int,
    total: int | None,
    etiqueta: str = "Pregunta",
    extra_meta: str | None = None,
    linea_estado: str | None = None,
    nombre_jugador: str | None = None,
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
    print(f"\n{p.texto}")
    for letra in ("A", "B", "C", "D"):
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
) -> None:
    """Registra la pantalla de la pregunta actual para reimprimirla tras pausa."""
    linea = progreso or linea_estado(estado, f"{etiqueta} {indice}/{total or 'inf'}")
    kwargs = dict(
        p=p,
        indice=indice,
        total=total,
        etiqueta=etiqueta,
        extra_meta=extra_meta,
        linea_estado=linea,
        nombre_jugador=estado.nombre,
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


def _mostrar_solucion(p: Pregunta) -> None:
    if p.correcta in {"A", "B", "C", "D"}:
        texto = p.opciones.get(p.correcta, "")
        print(f"Correcta: {p.correcta}) {texto}")
    else:
        print("Correcta: (dato no disponible en esta pregunta)")


def preguntar_con_reglas(
    p: Pregunta,
    estado: EstadoPartida,
) -> ResultadoRespuesta:
    lim_p = estado.reglas.tiempo_por_pregunta_seg
    if lim_p:
        print(f"(Tienes hasta {lim_p}s para responder)")
    inicio = time.monotonic()
    respuesta = pedir_opcion(
        "\nTu respuesta: ",
        ["A", "B", "C", "D"],
        default="A",
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


def aplicar_respuesta(
    p: Pregunta,
    estado: EstadoPartida,
    resultado: ResultadoRespuesta,
) -> None:
    estado.respondidas += 1
    reglas = estado.reglas

    if reglas.correccion_al_final:
        if resultado.tiempo_agotado or not resultado.acierto:
            estado.fallos_por_materia[p.materia] = estado.fallos_por_materia.get(p.materia, 0) + 1
        else:
            estado.aciertos += 1
        return

    if resultado.tiempo_agotado:
        print("[!] Tiempo agotado — cuenta como fallo")
        if reglas.tiene_vidas():
            estado.vidas_restantes = (estado.vidas_restantes or 0) - 1
        estado.fallos_por_materia[p.materia] = estado.fallos_por_materia.get(p.materia, 0) + 1
        if reglas.mostrar_solucion_tras_fallo:
            _mostrar_solucion(p)
        return

    if resultado.acierto:
        estado.aciertos += 1
        if reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE:
            delta = calcular_puntos_arcade(p.dificultad, True)
            estado.puntos_arcade += delta
            print(f"[OK] Correcto (+{delta} puntos)")
        else:
            print("[OK] Correcto")
    else:
        if reglas.tiene_vidas():
            estado.vidas_restantes = (estado.vidas_restantes or 0) - 1
        estado.fallos_por_materia[p.materia] = estado.fallos_por_materia.get(p.materia, 0) + 1
        if reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE:
            delta = calcular_puntos_arcade(p.dificultad, False)
            estado.puntos_arcade += delta
            msg = f"[X] Incorrecto ({delta} puntos)"
        else:
            msg = "[X] Incorrecto"
        print(msg)
        if reglas.mostrar_solucion_tras_fallo:
            _mostrar_solucion(p)
        if reglas.tiene_vidas() and (estado.vidas_restantes or 0) <= 0:
            print("\nTe has quedado sin vidas.")


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
    """Recorre preguntas en orden (examen, historia). Sin limpiar consola entre preguntas."""
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
                print("\nTiempo total del bloque agotado.")
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
            print("\nPartida abandonada. Volviendo al menú principal.")
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
    print(titulo)
    print(f"Jugador: {estado.nombre}")
    if incompleto:
        print(f"Preguntas respondidas: {total}/{previsto}")
    print(formatear_resultado_puntuacion(
        estado.reglas,
        aciertos=estado.aciertos,
        total=total,
        puntos_arcade=estado.puntos_arcade,
    ))
    if estado.reglas.mostrar_aciertos_en_curso or estado.reglas.sistema_puntuacion != SistemaPuntuacion.ARCADE:
        print(f"Resumen: {estado.aciertos}/{total} aciertos")
