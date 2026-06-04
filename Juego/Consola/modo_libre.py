#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo libre: partida configurable, filtros, dificultad progresiva e informes .txt."""

from __future__ import annotations

import random
from collections import deque

from .consola import (
    _activar_menu_consola,
    complejidad_pregunta,
    dificultad_global_actual,
    elegir_filtro,
    elegir_filtro_obligatorio,
    pedir_entero_en_rango,
    pedir_opcion,
    pedir_texto,
)
from .entrada_menu import elegir_indice_menu
from .informe_examen import RegistroRespuesta, publicar_informe_partida
from .modelos import BancoPreguntas, ETIQUETA_BANCO, Pregunta
from .motor_partida import (
    EstadoPartida,
    aplicar_respuesta,
    linea_estado,
    mostrar_resumen_partida,
    preguntar_con_reglas,
    registrar_contexto_pregunta,
)

from .navegacion import (
    AsistentePasos,
    ContextoPantalla,
    IrMenuPrincipal,
    SalirPrograma,
    VolverAtras,
    establecer_contexto,
    limpiar_consola,
    mostrar_transicion,
)
from .politica_reglas import aplicar_politica, resolver_politica_libre


def jugar_modo_libre(
    preguntas: list[Pregunta],
    banco: BancoPreguntas,
) -> bool:
    modo_txt, desc_banco = ETIQUETA_BANCO[banco]

    def _pantalla_intro() -> None:
        print("\n=== MODO LIBRE ===")
        print("Partida abierta con filtros.")
        print(f"Banco activo: {modo_txt} — {desc_banco}")

    mostrar_transicion(_pantalla_intro)

    def paso_nombre(asist: AsistentePasos) -> None:
        asist.datos["nombre"] = pedir_texto(
            "Nombre de jugador: ",
            default="Anonimo",
            permitir_atras=True,
        )

    def paso_tamano(asist: AsistentePasos) -> None:
        infinito = pedir_opcion(
            "¿Activar modo infinito? (S/N): ",
            ["S", "N"],
            default="S",
            permitir_atras=True,
        ) == "S"
        asist.datos["modo_infinito"] = infinito
        if infinito:
            asist.datos["total"] = 10
        else:
            asist.datos["total"] = pedir_entero_en_rango(
                "¿Cuántas preguntas quieres jugar? [10]: ",
                1,
                999,
                10,
            )

    def paso_reglas(asist: AsistentePasos) -> None:
        politica = resolver_politica_libre(
            modo_infinito=asist.datos["modo_infinito"],
            n_preguntas=asist.datos["total"],
        )
        asist.datos["reglas"] = aplicar_politica(politica)

    def paso_filtros(asist: AsistentePasos) -> None:
        def _dibujar_filtros() -> None:
            print("\nModo de filtro principal:")
            print("  0) Todas (por defecto)")
            print("  1) Por tematica")
            print("  2) Por semestre")
            print("  3) Por tipo")

        _activar_menu_consola("Filtros de preguntas", _dibujar_filtros)
        idx = elegir_indice_menu(
            3,
            defecto=0,
            permitir_cero=True,
            permitir_atras=True,
            prompt="Selecciona opcion",
        )
        modo_filtro = str(idx)
        _etiquetas_filtro = {
            "0": "Todas las preguntas",
            "1": "Por tematica",
            "2": "Por curso-semestre",
            "3": "Por tipo",
        }
        print(f"\n>>> Filtro elegido: {modo_filtro}) {_etiquetas_filtro[modo_filtro]}")
        asist.datos["modo_filtro"] = modo_filtro
        asist.datos["tematica"] = None
        asist.datos["curso"] = None
        asist.datos["semestre"] = None
        asist.datos["tipo_principal"] = None

        if modo_filtro == "1":
            asist.datos["tematica"] = elegir_filtro(
                "tematica", [p.tematica for p in preguntas]
            )
        elif modo_filtro == "2":
            combos = [f"{p.curso}-{p.semestre}" for p in preguntas if p.curso and p.semestre]
            if not combos:
                print(
                    "\nNo hay pares curso-semestre en este banco. "
                    "Pulsa Supr para elegir otro filtro."
                )
                raise VolverAtras()
            curso_semestre = elegir_filtro_obligatorio("curso-semestre", combos)
            c, s = curso_semestre.split("-", 1)
            asist.datos["curso"] = c
            asist.datos["semestre"] = s
        elif modo_filtro == "3":
            asist.datos["tipo_principal"] = elegir_filtro_obligatorio(
                "tipo", [p.tipo for p in preguntas]
            )

    def paso_dificultad(asist: AsistentePasos) -> None:
        reglas = asist.datos["reglas"]
        if not reglas.dificultad_progresiva:
            asist.datos["global_inicial"] = 1
            return
        pool = _construir_pool(preguntas, asist.datos)
        if not pool:
            raise ValueError("sin_pool")
        max_global = max(complejidad_pregunta(p) for p in pool)
        asist.datos["global_inicial"] = pedir_entero_en_rango(
            f"Dificultad global inicial [1-{max_global}] (Enter=1): ",
            1,
            max_global,
            1,
        )

    asistente = AsistentePasos("Configuración modo libre")
    try:
        asistente.ejecutar(
            [
                ("Nombre", paso_nombre),
                ("Tamaño de partida", paso_tamano),
                ("Reglas", paso_reglas),
                ("Filtros", paso_filtros),
                ("Dificultad inicial", paso_dificultad),
            ]
        )
    except IrMenuPrincipal:
        return False
    except SalirPrograma:
        raise
    except ValueError:
        print("\nNo hay preguntas para ese filtro. Vuelve atras (Supr) y cambia los filtros.")
        return False

    d = asistente.datos
    pool = _construir_pool(preguntas, d)
    if not pool:
        print("\nNo hay preguntas para ese filtro. Prueba con otra combinación.")
        return False

    modo_infinito = d["modo_infinito"]
    total = d["total"]
    reglas = d["reglas"]

    if d["modo_filtro"] in {"0", "1"} and d["tematica"] is None:
        random.shuffle(pool)

    total_objetivo = min(total, len(pool)) if not modo_infinito else None
    max_global = max(complejidad_pregunta(p) for p in pool)
    global_inicial = d.get("global_inicial", 1)
    ventana_no_repeticion = max(1, len(pool) // 4)
    historial_reciente: deque[int] = deque(maxlen=ventana_no_repeticion)
    usadas: set[int] = set()

    estado = EstadoPartida(
        nombre=d["nombre"],
        reglas=reglas,
        vidas_restantes=reglas.vidas,
    )

    def _pantalla_partida() -> None:
        print("\n=== PARTIDA (modo libre) ===")
        print(f"Jugador: {d['nombre']}")
        print(f"Reglas: {reglas.describe()}")
        if modo_infinito:
            print("Modo infinito (Ctrl+C = pausa).")
            print("Al terminar la sesion se guarda informe .txt en Juego/informes/.")
        else:
            print(f"Preguntas previstas: {total_objetivo}")
            print("Ctrl+C = pausa · Sin limpiar entre preguntas.")
            print("Al terminar se guarda un informe .txt en Juego/informes/.")

    limpiar_consola()
    _pantalla_partida()
    if not modo_infinito:
        input("\nPulsa Enter para comenzar...")

    establecer_contexto(
        ContextoPantalla(
            titulo="Modo libre — partida en curso",
            lineas=[
                f"Jugador: {d['nombre']}",
                f"Reglas: {reglas.describe()}",
                "Ctrl+C = pausa (1 = continuar y reimprimir)",
            ],
        )
    )

    registros_cierre: list[RegistroRespuesta] = []

    try:
        while estado.debe_continuar(total_objetivo):
            respondidas = estado.respondidas
            global_actual = max_global
            if reglas.dificultad_progresiva:
                global_actual = dificultad_global_actual(
                    respondidas=respondidas,
                    global_inicial=global_inicial,
                    max_global=max_global,
                )
            bloqueadas = set(historial_reciente)
            candidatas = [
                idx
                for idx, p in enumerate(pool)
                if idx not in usadas
                and idx not in bloqueadas
                and (not reglas.dificultad_progresiva or complejidad_pregunta(p) <= global_actual)
            ]
            if not candidatas:
                if modo_infinito:
                    usadas.clear()
                    candidatas = [
                        idx
                        for idx, p in enumerate(pool)
                        if idx not in bloqueadas
                        and (
                            not reglas.dificultad_progresiva
                            or complejidad_pregunta(p) <= global_actual
                        )
                    ]
                    if not candidatas:
                        candidatas = list(range(len(pool)))
                else:
                    candidatas = [idx for idx in range(len(pool)) if idx not in usadas]
                    if not candidatas:
                        break
            idx_elegida = random.choice(candidatas)
            usadas.add(idx_elegida)
            historial_reciente.append(idx_elegida)
            p = pool[idx_elegida]

            progreso = (
                f"Pregunta {estado.respondidas + 1}/inf"
                if modo_infinito
                else f"Pregunta {estado.respondidas + 1}/{total_objetivo}"
            )
            extra = None
            if reglas.dificultad_progresiva:
                origen = "plantilla" if p.fuente == "plantilla" else "dataset"
                extra = (
                    f"Tematica: {p.tematica or '-'} | Tipo: {p.tipo} | Origen: {origen} | "
                    f"Dificultad global: {global_actual}/{max_global}"
                )

            mostrar_pregunta(
                p,
                indice=estado.respondidas + 1,
                total=total_objetivo,
                extra_meta=extra,
                linea_estado=linea_estado(estado, progreso),
            )

            try:
                resultado = preguntar_con_reglas(p, estado)
                aplicar_respuesta(p, estado, resultado)
                registros_cierre.append(
                    RegistroRespuesta(
                        indice=estado.respondidas,
                        pregunta=p,
                        respuesta=resultado.respuesta,
                        acierto=resultado.acierto,
                        tiempo_agotado=resultado.tiempo_agotado,
                    )
                )
            except IrMenuPrincipal:
                establecer_contexto(None)
                return False
            except SalirPrograma:
                raise

        establecer_contexto(None)
        if estado.respondidas > 0:
            limpiar_consola()
            mostrar_resumen_partida(
                estado,
                "FIN DE PARTIDA (modo libre)",
                total_objetivo or estado.respondidas,
            )
            if registros_cierre:
                _filtros = {
                    "0": "Todas",
                    "1": f"Tematica: {d.get('tematica') or '-'}",
                    "2": f"Curso {d.get('curso') or '-'} sem. {d.get('semestre') or '-'}",
                    "3": f"Tipo: {d.get('tipo_principal') or '-'}",
                }
                _etiqueta = (
                    "Partida modo libre (infinito — sesion terminada)"
                    if modo_infinito
                    else "Partida modo libre (bloque finito)"
                )
                try:
                    publicar_informe_partida(
                        estado,
                        registros_cierre,
                        titulo="FIN DE PARTIDA (modo libre)",
                        total_previsto=total_objetivo or estado.respondidas,
                        nombre_jugador=d["nombre"],
                        meta={
                            "etiqueta_sesion": _etiqueta,
                            "banco": f"{modo_txt} — {desc_banco}",
                            "filtro": _filtros.get(d.get("modo_filtro", "0"), "?"),
                            "n_preguntas": total_objetivo or estado.respondidas,
                        },
                        prefijo="partida_libre",
                    )
                except Exception as exc:
                    print(f"\n[!] Error al guardar o mostrar el informe: {exc}")
            elif estado.respondidas > 0:
                print(
                    "\n[!] No se pudo generar el informe (no hay registro de respuestas). "
                    "Si persiste, reporta el fallo."
                )
    except SalirPrograma:
        establecer_contexto(None)
        raise

    return True


def _construir_pool(preguntas: list[Pregunta], d: dict) -> list[Pregunta]:
    return [
        p
        for p in preguntas
        if (d.get("tematica") is None or p.tematica == d["tematica"])
        and (d.get("curso") is None or p.curso == d["curso"])
        and (d.get("semestre") is None or p.semestre == d["semestre"])
        and (d.get("tipo_principal") is None or p.tipo == d["tipo_principal"])
    ]
