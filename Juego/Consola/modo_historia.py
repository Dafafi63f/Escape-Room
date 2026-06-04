#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo historia (v1): examen balanceado con datos del histórico de qualificacions."""

from __future__ import annotations

from .consola import (
    elegir_filtro_obligatorio,
    pedir_entero_en_rango,
    pedir_menu_numerado,
    pedir_opcion,
    pedir_texto,
)
from .datos import cargar_orden_materias
from .generador_examen_historia import (
    PerfilPedagogico,
    cargar_estadisticas_historicas,
    describir_perfil,
    generar_examen,
    resumen_estadisticas,
)
from .modelos import Pregunta
from .motor_partida import ejecutar_lista_fija
from .navegacion import (
    AsistentePasos,
    IrMenuPrincipal,
    SalirPrograma,
    VolverAtras,
    limpiar_consola,
    mostrar_transicion,
)
from .politica_reglas import aplicar_politica, resolver_politica_historia
from .rutas import PATH_MATERIAS


def _elegir_perfil_en_paso(asist: AsistentePasos) -> None:
    opciones = list(PerfilPedagogico)
    idx = pedir_menu_numerado(
        "Perfil pedagógico (histórico agregado):",
        [(p.value, describir_perfil(p)) for p in opciones],
        defecto=1,
    )
    asist.datos["perfil"] = opciones[idx - 1]


def jugar_modo_historia(
    preguntas: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
) -> bool:

    def _pantalla_intro() -> None:
        print("\n=== MODO HISTORIA (v1) ===")
        print("Examen balanceado con histórico de qualificacions.")
        print("Banco: dataset revisado (modo seguro).")

    mostrar_transicion(_pantalla_intro)

    stats: dict
    orden_materias: list[str]

    def paso_nombre(asist: AsistentePasos) -> None:
        asist.datos["nombre"] = pedir_texto(
            "Nombre de jugador: ",
            default="Anonimo",
            permitir_atras=True,
        )

    def paso_reglas(asist: AsistentePasos) -> None:
        asist.datos["reglas"] = aplicar_politica(resolver_politica_historia())

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

    def paso_perfil(asist: AsistentePasos) -> None:
        _elegir_perfil_en_paso(asist)

    def paso_ambito(asist: AsistentePasos) -> None:
        perfil: PerfilPedagogico = asist.datos["perfil"]
        curso_filtro: str | None = None
        semestre_filtro: str | None = None
        n_materias = 6

        if perfil == PerfilPedagogico.POR_CURSO:
            cursos = sorted({m.get("curso", "") for m in materias_meta.values() if m.get("curso")})
            if not cursos:
                print("\nNo hay cursos en los metadatos. Pulsa Supr para retroceder.")
                raise VolverAtras()
            curso_filtro = elegir_filtro_obligatorio("curso", cursos)
            semestres = sorted(
                {
                    m.get("semestre", "")
                    for m in materias_meta.values()
                    if m.get("semestre") and m.get("curso") == curso_filtro
                }
            )
            if semestres and pedir_opcion(
                "¿Filtrar también por semestre? (S/N): ",
                ["S", "N"],
                "N",
                permitir_atras=True,
            ) == "S":
                semestre_filtro = elegir_filtro_obligatorio("semestre", semestres)
        elif perfil != PerfilPedagogico.SIMULACRO:
            max_m = max(2, min(20, len(orden_materias)))
            n_materias = pedir_entero_en_rango(
                "¿Cuántas materias incluir en el examen? [6]: ",
                2,
                max_m,
                min(6, max_m),
            )

        asist.datos["curso_filtro"] = curso_filtro
        asist.datos["semestre_filtro"] = semestre_filtro
        asist.datos["n_materias"] = n_materias

    asistente = AsistentePasos("Configuración historia")
    try:
        asistente.ejecutar(
            [
                ("Nombre", paso_nombre),
                ("Reglas de examen", paso_reglas),
                ("Histórico (opcional)", paso_historico),
                ("Perfil pedagógico", paso_perfil),
                ("Ámbito del examen", paso_ambito),
            ]
        )
    except IrMenuPrincipal:
        return False
    except SalirPrograma:
        raise

    nombre = asistente.datos["nombre"]
    reglas = asistente.datos["reglas"]
    perfil = asistente.datos["perfil"]

    try:
        plan = generar_examen(
            preguntas,
            perfil=perfil,
            materias_orden=orden_materias,
            materias_meta=materias_meta,
            stats=stats,
            n_materias=asistente.datos["n_materias"],
            curso_filtro=asistente.datos.get("curso_filtro"),
            semestre_filtro=asistente.datos.get("semestre_filtro"),
        )
    except ValueError as e:
        print(f"\nNo se pudo generar el examen: {e}")
        return False

    def _pantalla_inicio_examen() -> None:
        print("\n=== EXAMEN (modo historia) ===")
        print(f"Preguntas: {len(plan.preguntas)}")
        print(f"Perfil: {perfil.value}")
        print(f"Materias: {', '.join(plan.materias)}")
        print("Ctrl+C = pausa · Sin limpiar entre preguntas.")
        print("No verás si acertaste hasta el final (examen cerrado).")
        print("Al terminar se guarda un informe .txt en Juego/informes/.")

    limpiar_consola()
    _pantalla_inicio_examen()
    input("\nPulsa Enter para comenzar el examen...")

    try:
        estado = ejecutar_lista_fija(
            plan.preguntas,
            nombre=nombre,
            reglas=reglas,
            titulo_fin="FIN DEL EXAMEN (modo historia)",
            etiqueta="Escena",
            guardar_informe=True,
            meta_informe={
                "etiqueta_sesion": f"Examen historia — {perfil.value}",
                "perfil": perfil.value,
                "materias": ", ".join(plan.materias),
                "banco": "dataset revisado (modo seguro)",
                "n_preguntas": len(plan.preguntas),
            },
            stats_historicas=stats,
        )
    except SalirPrograma:
        raise

    if estado.fallos_por_materia:
        print("\nMaterias a reforzar en este intento (también en el informe .txt):")
        for materia, n in sorted(estado.fallos_por_materia.items(), key=lambda x: -x[1]):
            st = stats.get(materia)
            extra = f" (histórico: media {st.media:.2f})" if st else ""
            print(f"  · {materia}: {n} error(es){extra}")
    return True
