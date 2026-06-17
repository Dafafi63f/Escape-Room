#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo historia: catálogo con propósito pedagógico y opciones acotadas."""

from __future__ import annotations

from Comun.config_historia import ConfigPresetHistoria
from Comun.jugador import NOMBRE_JUGADOR_DEFECTO
from .config_historia import pedir_config_historia
from .consola import pedir_menu_numerado, pedir_opcion, pedir_texto
from .datos import cargar_orden_materias
from .entrada_menu import esperar_enter
from .generador_examen_historia import (
    cargar_estadisticas_historicas,
    generar_examen,
    resumen_estadisticas,
)
from Comun.modelos import Pregunta
from .motor_partida import ejecutar_lista_fija
from .motor_resistencia import ejecutar_resistencia_historia
from Consola.navegacion import (
    AsistentePasos,
    IrMenuPrincipal,
    SalirPrograma,
    limpiar_consola,
    mostrar_transicion,
)
from Consola.textos_consola import banner, campo, con_emoji, titulo as titulo_ui
from .politica_reglas import aplicar_politica
from Comun.cierre_informe import meta_cierre_historia
from Comun.presets_historia import (
    PresetHistoria,
    aplicar_preset,
    argumentos_generador,
    cargar_presets_historia,
    politica_desde_preset,
)
from Comun.resistencia_historia import es_preset_resistencia
from Comun.rutas import PATH_MATERIAS, resolver_presets_historia


def _elegir_preset(presets: list[PresetHistoria]) -> PresetHistoria:
    opciones = [
        (p.id, f"{p.nombre} — {p.descripcion}")
        for p in presets
    ]
    idx = pedir_menu_numerado(
        campo("tipo_partida", "Tipo de partida (ordenado por utilidad)"),
        opciones,
        defecto=1,
    )
    return presets[idx - 1]


def jugar_modo_historia(
    preguntas: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
) -> bool:

    def _pantalla_intro() -> None:
        print(f"\n{banner('MODO HISTORIA')}")
        print(con_emoji(
            "Partidas con propósito claro; cada tipo permite ajustar solo lo relevante.",
            "📕",
        ))
        print(f"{campo('banco_seguro', 'Banco')}: dataset revisado (modo seguro).")

    mostrar_transicion(_pantalla_intro)

    try:
        presets = cargar_presets_historia(resolver_presets_historia())
    except (FileNotFoundError, ValueError) as e:
        print(f"\nNo se pudo cargar el catálogo de historia: {e}")
        return False

    stats: dict
    orden_materias: list[str]

    def paso_nombre(asist: AsistentePasos) -> None:
        asist.datos["nombre"] = pedir_texto(
            f"{campo('nombre', 'Nombre de jugador')}: ",
            default=NOMBRE_JUGADOR_DEFECTO,
            permitir_atras=True,
        )

    def paso_preset(asist: AsistentePasos) -> None:
        asist.datos["preset"] = _elegir_preset(presets)

    def paso_opciones(asist: AsistentePasos) -> None:
        nonlocal orden_materias
        preset: PresetHistoria = asist.datos["preset"]
        orden_materias = cargar_orden_materias(PATH_MATERIAS)
        if preset.tiene_opciones():
            asist.datos["config"] = pedir_config_historia(
                preset,
                materias_meta=materias_meta,
                materias_orden=orden_materias,
            )
        else:
            asist.datos["config"] = ConfigPresetHistoria()
        politica = politica_desde_preset(preset, asist.datos["config"])
        asist.datos["reglas"] = aplicar_politica(politica)

    def paso_historico(asist: AsistentePasos) -> None:
        nonlocal stats, orden_materias
        stats = cargar_estadisticas_historicas(materias_validas=set(materias_meta))
        orden_materias = cargar_orden_materias(PATH_MATERIAS)
        if pedir_opcion(
            "¿Ver resumen de dificultad histórica? (S/N): ",
            ["S", "N"],
            default="N",
            permitir_atras=True,
        ) == "S":
            print(resumen_estadisticas(stats, orden_materias))

    pasos = [
        ("Nombre", paso_nombre),
        ("Tipo de partida", paso_preset),
        ("Opciones del tipo", paso_opciones),
        ("Histórico (opcional)", paso_historico),
    ]

    asistente = AsistentePasos("Modo historia")
    try:
        asistente.ejecutar(pasos)
    except IrMenuPrincipal:
        return False
    except SalirPrograma:
        raise

    nombre = asistente.datos["nombre"]
    preset: PresetHistoria = asistente.datos["preset"]
    config: ConfigPresetHistoria = asistente.datos["config"]
    reglas = asistente.datos["reglas"]

    if es_preset_resistencia(preset):
        def _pantalla_resistencia() -> None:
            print(f"\n{banner('RANKING — RESISTENCIA INFINITA')}")
            print(f"{campo('tipo_partida', 'Tipo')}: {preset.nombre}")
            print(con_emoji(
                "Una falla termina la racha. La dificultad sube con cada acierto.",
                "🔥",
            ))
            print(con_emoji(
                "Récords en ranking local (multijugador offline).",
                "🏆",
            ))

        limpiar_consola()
        _pantalla_resistencia()
        esperar_enter("\nPulsa Enter para comenzar")
        try:
            ejecutar_resistencia_historia(
                preguntas,
                nombre=nombre,
                reglas=reglas,
                preset_id=preset.id,
                preset_nombre=preset.nombre,
                perfil=preset.perfil,
                materias_meta=materias_meta,
                stats_historicas=stats,
            )
        except SalirPrograma:
            raise
        return True

    try:
        plan = generar_examen(
            preguntas,
            materias_orden=orden_materias,
            materias_meta=materias_meta,
            stats=stats,
            **argumentos_generador(preset, config, materias_meta=materias_meta),
        )
    except ValueError as e:
        print(f"\nNo se pudo generar el examen: {e}")
        return False

    def _pantalla_inicio_examen() -> None:
        print(f"\n{banner('PARTIDA (modo historia)')}")
        print(f"{campo('tipo_partida', 'Tipo')}: {preset.nombre}")
        print(f"{campo('n_preguntas', 'Preguntas')}: {len(plan.preguntas)}")
        print(f"{campo('banco', 'Materias')}: {', '.join(plan.materias)}")
        if reglas.tiempo_total_seg:
            print(f"{campo('tiempo_total', 'Tiempo total')}: {reglas.tiempo_total_seg // 60} min")
        if reglas.correccion_al_final:
            print(con_emoji("Sin limpiar entre preguntas.", "📝"))
            print(con_emoji(
                "No verás si acertaste hasta el final (examen cerrado).",
                "🔒",
            ))
        print(con_emoji(
            "Al terminar se guarda un informe .txt en Juego/informes/.",
            "💾",
        ))

    limpiar_consola()
    _pantalla_inicio_examen()
    esperar_enter("\nPulsa Enter para comenzar")

    try:
        estado = ejecutar_lista_fija(
            plan.preguntas,
            nombre=nombre,
            reglas=reglas,
            titulo_fin=f"FIN — {preset.nombre}",
            etiqueta="Escena",
            guardar_informe=True,
            meta_informe=meta_cierre_historia(
                preset_id=preset.id,
                preset_nombre=preset.nombre,
                perfil=preset.perfil,
                materias=plan.materias,
                n_preguntas=len(plan.preguntas),
            ),
            stats_historicas=stats,
        )
    except SalirPrograma:
        raise

    if estado.fallos_por_materia:
        print(f"\n{con_emoji('Materias a reforzar en este intento (también en el informe .txt):', '📊')}")
        for materia, n in sorted(estado.fallos_por_materia.items(), key=lambda x: -x[1]):
            st = stats.get(materia)
            extra = f" (histórico: media {st.media:.2f})" if st else ""
            print(f"  · {materia}: {n} error(es){extra}")
    return True
