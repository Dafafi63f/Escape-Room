#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo feedback: el jugador envia avisos sobre el juego al creador."""

from __future__ import annotations

from .consola import pedir_menu_numerado, pedir_opcion, pedir_texto, pedir_texto_multilinea
from .envio_feedback import (
    CategoriaFeedback,
    ReporteFeedback,
    describir_resultado_envio,
    enviar_feedback,
)
from Comun.jugador import NOMBRE_JUGADOR_DEFECTO
from Comun.modelos import Pregunta
from .navegacion import (
    AsistentePasos,
    CancelarFeedbackRapido,
    IrMenuPrincipal,
    SalirPrograma,
    VolverAtras,
    mostrar_transicion,
)
from .config_creador import mensaje_crear_creador_privado
from Comun.rutas import resolver_config_creador_privado
from Consola.textos_consola import banner, campo, con_emoji


_CATEGORIAS: list[tuple[CategoriaFeedback, str]] = [
    (CategoriaFeedback.BUG, "Error o fallo del juego"),
    (CategoriaFeedback.SUGERENCIA, "Sugerencia de mejora"),
    (CategoriaFeedback.PREGUNTA_INCORRECTA, "Pregunta con error o respuesta dudosa"),
    (CategoriaFeedback.CONTROLES_INTERFAZ, "Controles, menus o interfaz"),
    (CategoriaFeedback.OTRO, "Otro tema"),
]

_AREAS: list[tuple[str, str]] = [
    ("menu", "Menus y navegacion"),
    ("partida", "Durante una partida o pregunta"),
    ("datos", "Preguntas, materias o banco de datos"),
    ("informes", "Informes o resultados"),
    ("rendimiento", "Rendimiento o carga"),
    ("general", "General / no se"),
]


def _tiene_config_externa() -> bool:
    return resolver_config_creador_privado() is not None


def _imprimir_intro(*, acceso_rapido: bool) -> None:
    print("\n" + "=" * 60)
    print(banner("MODO FEEDBACK"))
    if acceso_rapido:
        print(con_emoji(
            "(La pantalla anterior sigue visible arriba para que puedas consultarla.)",
            "👁️",
        ))
    print(con_emoji(
        "Envia un aviso al creador del juego (bug, sugerencia, etc.).",
        "📣",
    ))
    print(con_emoji("Siempre se guarda una copia en Juego/Feedback/.", "💾"))
    if acceso_rapido:
        print("Supr en el paso 1 = cancelar y volver al juego.")
    else:
        print("Supr = paso anterior (en el paso 1, vuelve al menu principal).")
    from .entrada_menu import TECLA_PAUSA

    print(f"{TECLA_PAUSA} = pausa ({TECLA_PAUSA} otra vez en pausa: salir). Ctrl+C = cerrar.")
    if _tiene_config_externa():
        print("Config detectada: se intentara enviar el aviso por correo (SMTP).")
        print("Si falta smtp_password, solo se guardara copia local y veras instrucciones.")
    else:
        print(f"Opcional: {mensaje_crear_creador_privado()}")
    print("=" * 60)


def _pasos_feedback(asist: AsistentePasos) -> list[tuple[str, object]]:
    def paso_nombre(a: AsistentePasos) -> None:
        a.datos["jugador"] = pedir_texto(
            f"{campo('nombre', 'Tu nombre (opcional)')}: ",
            default=NOMBRE_JUGADOR_DEFECTO,
            permitir_atras=True,
        )

    def paso_categoria(a: AsistentePasos) -> None:
        idx = pedir_menu_numerado(
            campo("tipo_partida", "Tipo de aviso"),
            [(c.value, desc) for c, desc in _CATEGORIAS],
            defecto=1,
            permitir_atras=True,
        )
        a.datos["categoria"] = _CATEGORIAS[idx - 1][0]

    def paso_area(a: AsistentePasos) -> None:
        idx = pedir_menu_numerado(
            con_emoji("Zona del juego relacionada", "🎯"),
            _AREAS,
            defecto=6,
            permitir_atras=True,
        )
        a.datos["area"] = _AREAS[idx - 1][0]

    def paso_mensaje(a: AsistentePasos) -> None:
        a.datos["mensaje"] = pedir_texto_multilinea(
            "\nDescribe el aviso con detalle:",
            default="(sin mensaje)",
            permitir_atras=True,
            enter_con_texto_termina=True,
        )

    def paso_contacto(a: AsistentePasos) -> None:
        a.datos["contacto"] = pedir_texto(
            "Correo de contacto (opcional): ",
            default="Sin contacto",
            permitir_atras=True,
        )

    def paso_confirmar(a: AsistentePasos) -> None:
        cat = a.datos["categoria"]
        jug = a.datos["jugador"]
        print(f"\n{con_emoji('--- Resumen del aviso ---', '📋')}")
        print(f"  {campo('jugador', f'Jugador: {jug}')}")
        print(f"  Tipo: {cat.value}")
        print(f"  Area: {a.datos['area']}")
        print(f"  Contacto: {a.datos.get('contacto') or 'Sin contacto'}")
        print("  Mensaje:")
        for linea in a.datos["mensaje"].splitlines():
            print(f"    {linea}")
        if pedir_opcion(
            "\n¿Enviar este aviso? (S/N): ",
            ["S", "N"],
            default="S",
            permitir_atras=True,
        ) == "N":
            raise VolverAtras()

    _ = asist
    return [
        ("Nombre", paso_nombre),
        ("Tipo de aviso", paso_categoria),
        ("Zona", paso_area),
        ("Mensaje", paso_mensaje),
        ("Contacto", paso_contacto),
        ("Confirmacion", paso_confirmar),
    ]


def _ejecutar_asistente_feedback(*, acceso_rapido: bool) -> dict | None:
    if acceso_rapido:
        asist = AsistentePasos(
            "Feedback",
            excepcion_paso1_atras=CancelarFeedbackRapido,
            mensaje_paso1_atras="<- Feedback cancelado",
        )
    else:
        asist = AsistentePasos("Feedback")

    try:
        asist.ejecutar(_pasos_feedback(asist))
    except VolverAtras:
        print("\nAviso cancelado.")
        return None
    except CancelarFeedbackRapido:
        print("\nFeedback cancelado.")
        return None
    except IrMenuPrincipal:
        raise
    except SalirPrograma:
        raise
    return asist.datos


def ejecutar_feedback_rapido() -> None:
    """Feedback desde tecla F: no limpia la terminal; al terminar restaura la pantalla."""
    _imprimir_intro(acceso_rapido=True)
    datos = _ejecutar_asistente_feedback(acceso_rapido=True)
    if datos is None:
        return
    reporte = ReporteFeedback(
        categoria=datos["categoria"],
        mensaje=datos["mensaje"],
        jugador=datos["jugador"],
        contacto=datos.get("contacto", ""),
        area=datos["area"],
    )
    resultado = enviar_feedback(reporte)
    print()
    for linea in describir_resultado_envio(resultado):
        print(linea)


def jugar_modo_feedback(
    preguntas: list[Pregunta],
    materias_meta: dict[str, dict[str, str]],
) -> None:
    _ = preguntas, materias_meta

    mostrar_transicion(lambda: _imprimir_intro(acceso_rapido=False))
    datos = _ejecutar_asistente_feedback(acceso_rapido=False)
    if datos is None:
        return

    reporte = ReporteFeedback(
        categoria=datos["categoria"],
        mensaje=datos["mensaje"],
        jugador=datos["jugador"],
        contacto=datos.get("contacto", ""),
        area=datos["area"],
    )
    resultado = enviar_feedback(reporte)
    print()
    for linea in describir_resultado_envio(resultado):
        print(linea)
