#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo libre: partida configurable, filtros, dificultad progresiva e informes .txt."""

from __future__ import annotations

import random
from dataclasses import replace

from Comun.dificultad import (
    describe_niveles_seleccion,
    max_complejidad_pool,
    niveles_en_pool,
    normalizar_niveles_seleccionados,
    techo_complejidad_partida,
)
from Comun.pool_libre import (
    crear_estado_seleccion,
    elegir_indice_siguiente,
    filtrar_pool_asistente,
)
from .consola import (
    _activar_menu_consola,
    elegir_filtro,
    elegir_filtro_obligatorio,
    pedir_entero_en_rango,
    pedir_opcion,
    pedir_texto,
)
from .entrada_menu import elegir_indice_menu, esperar_enter
from Comun.cierre_informe import meta_cierre_libre
from Comun.jugador import NOMBRE_JUGADOR_DEFECTO
from .informe_examen import RegistroRespuesta, publicar_informe_partida
from Comun.modelos import BancoPreguntas, ETIQUETA_BANCO, Pregunta
from .motor_partida import (
    EstadoPartida,
    aplicar_respuesta,
    linea_estado,
    mostrar_resumen_partida,
    preguntar_con_reglas,
    registrar_contexto_pregunta,
)

from Consola.navegacion import (
    AsistentePasos,
    ContextoPantalla,
    IrMenuPrincipal,
    SalirPrograma,
    VolverAtras,
    establecer_contexto,
    limpiar_consola,
    mostrar_transicion,
)
from Consola.politica_reglas import aplicar_politica, resolver_politica_libre
from Consola.textos_consola import banner, campo, con_emoji, titulo as titulo_ui


def jugar_modo_libre(
    preguntas: list[Pregunta],
    banco: BancoPreguntas,
) -> bool:
    modo_txt, desc_banco = ETIQUETA_BANCO[banco]

    def _pantalla_intro() -> None:
        print(f"\n{banner('MODO LIBRE')}")
        print(con_emoji("Partida abierta con filtros.", "🎮"))
        print(f"{campo('banco', 'Banco activo')}: {modo_txt} — {desc_banco}")

    mostrar_transicion(_pantalla_intro)

    def paso_nombre(asist: AsistentePasos) -> None:
        asist.datos["nombre"] = pedir_texto(
            f"{campo('nombre', 'Nombre de jugador')}: ",
            default=NOMBRE_JUGADOR_DEFECTO,
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
            print(f"\n{campo('filtro_principal', 'Modo de filtro principal')}:")
            print(f"  0) {con_emoji('Todas (por defecto)', '🌐')}")
            print(f"  1) {con_emoji('Por tematica', '📚')}")
            print(f"  2) {con_emoji('Por semestre', '📅')}")
            print(f"  3) {con_emoji('Por tipo', '🏷️')}")

        _activar_menu_consola(titulo_ui("Filtros de preguntas"), _dibujar_filtros)
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
        pool = _construir_pool(preguntas, asist.datos)
        if not pool:
            raise ValueError("sin_pool")
        disponibles = sorted(niveles_en_pool(pool))
        if len(disponibles) <= 1:
            asist.datos["niveles_complejidad"] = frozenset(disponibles)
            return
        print(f"Niveles con preguntas: {', '.join(str(n) for n in disponibles)}")
        texto = input(
            "Niveles a usar (ej. 1,3,6; Enter=todos): "
        ).strip()
        if not texto:
            seleccion = frozenset(disponibles)
        else:
            try:
                elegidos = {
                    int(parte.strip())
                    for parte in texto.split(",")
                    if parte.strip()
                }
            except ValueError:
                elegidos = set()
            seleccion = normalizar_niveles_seleccionados(elegidos, pool)
        asist.datos["niveles_complejidad"] = seleccion
        reglas = asist.datos["reglas"]
        if reglas.dificultad_progresiva and len(seleccion) < 2:
            print("Aviso: la dificultad progresiva requiere al menos 2 niveles.")

    asistente = AsistentePasos("Configuración modo libre")
    try:
        asistente.ejecutar(
            [
                ("Nombre", paso_nombre),
                ("Tamaño de partida", paso_tamano),
                ("Reglas", paso_reglas),
                ("Filtros", paso_filtros),
                ("Niveles de complejidad", paso_dificultad),
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
    max_global = max_complejidad_pool(pool)
    niveles_complejidad = normalizar_niveles_seleccionados(
        d.get("niveles_complejidad"),
        pool,
    )
    if reglas.dificultad_progresiva and len(niveles_complejidad) < 2:
        reglas = replace(reglas, dificultad_progresiva=False)
    seleccion = crear_estado_seleccion(len(pool))

    estado = EstadoPartida(
        nombre=d["nombre"],
        reglas=reglas,
        vidas_restantes=reglas.vidas,
    )

    def _pantalla_partida() -> None:
        print(f"\n{banner('PARTIDA (modo libre)')}")
        print(campo("jugador", f"Jugador: {d['nombre']}"))
        print(f"{campo('opciones_juego', 'Reglas')}: {reglas.describe()}")
        if modo_infinito:
            print("Modo infinito.")
            print("Al terminar la sesion se guarda informe .txt en Data/Juego/.")
        else:
            print(f"Preguntas previstas: {total_objetivo}")
            print("Sin limpiar entre preguntas.")
            print("Al terminar se guarda un informe .txt en Data/Juego/.")

    limpiar_consola()
    _pantalla_partida()
    if not modo_infinito:
        esperar_enter("\nPulsa Enter para comenzar")

    establecer_contexto(
        ContextoPantalla(
            titulo=titulo_ui("Modo libre — partida en curso"),
            lineas=[
                campo("jugador", f"Jugador: {d['nombre']}"),
                f"{campo('opciones_juego', 'Reglas')}: {reglas.describe()}",
                con_emoji("Pulsa H para ver controles.", "❓"),
            ],
        )
    )

    registros_cierre: list[RegistroRespuesta] = []

    try:
        while estado.debe_continuar(total_objetivo):
            techo = techo_complejidad_partida(
                dificultad_progresiva=reglas.dificultad_progresiva,
                respondidas=estado.respondidas,
                niveles_seleccion=niveles_complejidad,
            )
            idx_elegida = elegir_indice_siguiente(
                pool,
                seleccion,
                modo_infinito=modo_infinito,
                dificultad_progresiva=reglas.dificultad_progresiva,
                niveles_complejidad=niveles_complejidad,
                respondidas=estado.respondidas,
            )
            if idx_elegida is None:
                break
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
                    f"Nivel: {techo} ({describe_niveles_seleccion(niveles_complejidad)})"
                )
            elif niveles_complejidad != niveles_en_pool(pool):
                origen = "plantilla" if p.fuente == "plantilla" else "dataset"
                extra = (
                    f"Tematica: {p.tematica or '-'} | Tipo: {p.tipo} | Origen: {origen} | "
                    f"Nivel: {describe_niveles_seleccion(niveles_complejidad)}"
                )

            registrar_contexto_pregunta(
                p,
                estado,
                indice=estado.respondidas + 1,
                total=total_objetivo,
                extra_meta=extra,
                progreso=linea_estado(estado, progreso),
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
                try:
                    publicar_informe_partida(
                        estado,
                        registros_cierre,
                        titulo="FIN DE PARTIDA (modo libre)",
                        total_previsto=total_objetivo or estado.respondidas,
                        nombre_jugador=d["nombre"],
                        meta=meta_cierre_libre(
                            banco=f"{modo_txt} — {desc_banco}",
                            filtro=_filtros.get(d.get("modo_filtro", "0"), "?"),
                            infinito=modo_infinito,
                            n_preguntas=total_objetivo or estado.respondidas,
                        ),
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
    return filtrar_pool_asistente(
        preguntas,
        tematica=d.get("tematica"),
        curso=d.get("curso"),
        semestre=d.get("semestre"),
        tipo=d.get("tipo_principal"),
    )
