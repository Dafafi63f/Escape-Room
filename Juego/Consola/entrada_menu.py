#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lectura de teclas en menus. Bajo nivel Windows/fallback: ``entrada_teclas.py``.

  Enter     -> primera opcion (1 en menus; A en pregunta)
  1-9       -> opcion del menu; en pregunta ignorados (solo A-D)
  H         -> ayuda contextual (controles del momento actual)
  Supr      -> atras (menu principal: cierra juego); en pausa = continuar; en pregunta: ignorada
  Esc       -> pausa (Esc otra vez en pausa: salir); en texto con atras: volver atras
  F         -> feedback al creador (sin borrar pantalla; no en menu de pausa)
  Ctrl+C    -> interrupcion tipica de terminal (cierra el programa)
  A-D       -> respuesta en pregunta; fuera del examen, ignoradas
  S/N       -> solo en menus Si/No; fuera, ignoradas
  Resto     -> ignorado (sin mensaje)
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from .entrada_teclas import (
    TECLA_AYUDA,
    TECLA_ATRAS_TEXTO,
    TECLA_ESC,
    TECLA_FEEDBACK,
    TECLA_PAUSA,
    TipoTecla,
    EventoTecla as _EventoTecla,
    leer_tecla,
    leer_tecla_texto_windows as _leer_tecla_texto_windows,
)

_LETRAS_RESPUESTA = frozenset({"A", "B", "C", "D"})
_LETRAS_SN = frozenset({"S", "N"})

SIMBOLO_FOCO_ENTRADA = ">>"

TipoEntrada = Literal[
    "menu_numerico",
    "menu_si_no",
    "pregunta",
    "enter_solo",
    "tutorial",
    "pausa",
    "texto",
    "entero",
]


@dataclass
class ContextoEntrada:
    """Estado de entrada actual; alimenta el menu de ayuda dinamico."""

    tipo: TipoEntrada
    defecto: int | str = 1
    permitir_atras: bool = False
    es_menu_principal: bool = False
    en_partida: bool = False
    en_pausa: bool = False
    num_opciones: int | None = None
    minimo: int | None = None
    maximo: int | None = None


_contexto_entrada: ContextoEntrada | None = None


def establecer_contexto_entrada(ctx: ContextoEntrada | None) -> None:
    global _contexto_entrada
    _contexto_entrada = ctx


def obtener_contexto_entrada() -> ContextoEntrada | None:
    return _contexto_entrada


def _formatear_prompt(prompt: str, *, con_dos_puntos: bool = True) -> str:
    """Prefija >> al prompt: punto de clic y accion en una sola linea."""
    texto = prompt.rstrip()
    salto = ""
    if texto.startswith("\n"):
        salto = "\n"
        texto = texto.lstrip("\n")
    if con_dos_puntos and texto and not texto.endswith(":"):
        texto += ":"
    return f"{salto}{SIMBOLO_FOCO_ENTRADA} {texto} " if texto else f"{salto}{SIMBOLO_FOCO_ENTRADA} "


def _imprimir_linea_accion(prompt: str, *, con_dos_puntos: bool = True) -> None:
    """Linea de cierre del menu: una sola >> separada del contenido."""
    print()
    print(_formatear_prompt(prompt, con_dos_puntos=con_dos_puntos), end="", flush=True)


def texto_controles_detallado() -> list[str]:
    """Guía de controles para la pantalla de bienvenida."""
    return [
        "A diferencia de otros programas de consola, aquí NO se escriben comandos.",
        "Cada acción se activa con una sola tecla, sin pulsar Enter (salvo donde se indique).",
        "",
        "En menús:",
        "  · Enter  → opción por defecto (normalmente la 1)",
        "  · 1-9    → elegir la opción con ese número",
        "  · Supr   → volver atrás (en el menú principal: salir del juego)",
        f"  · {TECLA_PAUSA}     → menú de pausa ({TECLA_PAUSA} otra vez en pausa: salir)",
        "",
        "En preguntas del examen:",
        "  · A, B, C o D → responder (Enter = A)",
        "  · Los números 1-9 no hacen nada durante la pregunta",
        "",
        "En menús Sí/No:",
        "  · S o N → confirmar o rechazar (Enter = S)",
        "",
        "En campos de texto (nombre, mensaje, etc.):",
        "  · Enter vacío → valor por defecto del campo",
        f"  · Retroceso / Supr → borrar carácter",
        f"  · {TECLA_ATRAS_TEXTO}     → volver atrás",
        "",
        "En cualquier momento (menus de teclas):",
        "  · H      → ver controles del momento actual",
        f"  · {TECLA_FEEDBACK}      → enviar feedback al creador (sin borrar pantalla)",
        "",
        "Ctrl+C cierra el programa al instante (comportamiento habitual de la terminal).",
    ]


def lineas_ayuda_dinamica(*, desde_menu_ayuda: bool = False) -> list[str]:
    """Genera la ayuda segun la pantalla y el modo de entrada actuales."""
    from .navegacion import obtener_contexto_pantalla

    ctx_e = _contexto_entrada
    ctx_p = obtener_contexto_pantalla()
    lineas: list[str] = []

    if ctx_p is not None:
        lineas.append(f"Pantalla: {ctx_p.titulo}")
        for linea in ctx_p.lineas:
            lineas.append(f"  {linea}")
        lineas.append("")

    if ctx_e is None:
        lineas.append("Controles generales:")
        lineas.extend(texto_controles_detallado())
        return lineas

    if ctx_e.tipo == "menu_numerico":
        lineas.append("Menu numerico:")
        lineas.append(f"  Enter -> opcion {ctx_e.defecto} (por defecto)")
        if ctx_e.num_opciones:
            lineas.append(f"  1-{ctx_e.num_opciones} -> elegir opcion")
        lineas.extend(_lineas_navegacion(ctx_e))
    elif ctx_e.tipo == "menu_si_no":
        lineas.append("Menu Si/No:")
        lineas.append(f"  Enter -> {ctx_e.defecto} (por defecto)")
        lineas.append("  S / N -> Si o No")
        lineas.extend(_lineas_navegacion(ctx_e))
    elif ctx_e.tipo == "pregunta":
        lineas.append("Pregunta del examen:")
        lineas.append(f"  Enter -> {ctx_e.defecto} (por defecto)")
        lineas.append("  A / B / C / D -> responder")
        lineas.append("  1-9 -> ignorados durante la pregunta")
        lineas.append("  Supr -> sin efecto")
        lineas.append(f"  {TECLA_PAUSA} -> menu de pausa")
    elif ctx_e.tipo == "enter_solo":
        lineas.append("Confirmacion:")
        lineas.append("  Enter -> continuar")
        lineas.extend(_lineas_navegacion(ctx_e))
    elif ctx_e.tipo == "tutorial":
        lineas.append("Tutorial inicial:")
        lineas.append("  Haz clic en la ventana del juego (esta terminal)")
        lineas.append(f"  {SIMBOLO_FOCO_ENTRADA} Enter -> continuar")
        lineas.append(f"  {TECLA_PAUSA} -> menu de pausa")
        lineas.append(f"  {TECLA_AYUDA} -> ver controles detallados")
    elif ctx_e.tipo == "pausa":
        lineas.append("Menu de pausa:")
        lineas.append("  Enter -> opcion 1 (continuar)")
        lineas.append("  1-3 -> elegir opcion")
        lineas.append("  Supr -> continuar (cerrar pausa)")
        lineas.append(f"  {TECLA_PAUSA} otra vez -> salir del programa")
    elif ctx_e.tipo == "texto":
        lineas.append("Entrada de texto:")
        lineas.append("  Escribe y pulsa Enter para confirmar")
        lineas.append("  Enter vacio -> valor por defecto del campo")
        lineas.append("  Retroceso / Supr -> borrar caracter")
        lineas.extend(_lineas_navegacion(ctx_e))
    elif ctx_e.tipo == "entero":
        lineas.append("Entrada numerica:")
        if ctx_e.minimo is not None and ctx_e.maximo is not None:
            lineas.append(f"  Escribe un numero entre {ctx_e.minimo} y {ctx_e.maximo}")
        lineas.append(f"  Enter vacio -> {ctx_e.defecto} (por defecto)")
        lineas.append("  Retroceso / Supr -> borrar caracter")
        lineas.extend(_lineas_navegacion(ctx_e))

    if not desde_menu_ayuda:
        lineas.append("")
        lineas.append(f"  {TECLA_AYUDA} -> abrir esta ayuda")
        if ctx_e.tipo != "pausa":
            lineas.append(
                f"  {TECLA_FEEDBACK} -> feedback al creador (mantiene el contexto en pantalla)"
            )
        lineas.append("  La linea de accion de cada pantalla empieza por >>")
    return lineas


def _lineas_navegacion(ctx: ContextoEntrada) -> list[str]:
    if ctx.tipo in ("texto", "entero"):
        if ctx.permitir_atras:
            return [f"  {TECLA_ATRAS_TEXTO} -> volver atras"]
        return [f"  {TECLA_PAUSA} -> menu de pausa"]
    if ctx.en_pausa:
        return [
            "  Supr -> continuar (cerrar pausa)",
            f"  {TECLA_PAUSA} otra vez -> salir del programa",
        ]
    if ctx.es_menu_principal:
        return [
            "  Supr -> salir del juego",
            f"  {TECLA_PAUSA} -> menu de pausa",
        ]
    if ctx.en_partida:
        return [f"  {TECLA_PAUSA} -> menu de pausa"]
    if ctx.permitir_atras:
        return [
            "  Supr -> volver atras",
            f"  {TECLA_PAUSA} -> menu de pausa",
        ]
    return [
        "  Supr -> volver al menu principal",
        f"  {TECLA_PAUSA} -> menu de pausa",
    ]


class AbrirPausa(Exception):
    """Esc fuera del menu de pausa: abrir el menu de pausa."""


def _gestionar_tecla_escape(*, en_pausa: bool) -> None:
    """Primer Esc abre pausa; segundo Esc (ya en pausa) sale del programa."""
    from .navegacion import SalirPrograma

    if en_pausa:
        raise SalirPrograma() from None
    raise AbrirPausa() from None


def _es_menu_si_no(validas: set[str]) -> bool:
    return bool(validas) and validas <= _LETRAS_SN


def _redibujar_linea_texto(prompt: str, caracteres: list[str]) -> None:
    """Reescribe prompt + texto en la misma linea (tras borrar o pausa)."""
    contenido = "".join(caracteres)
    print(f"\r{prompt}{contenido} \b", end="", flush=True)


def _borrar_caracter_en_linea(prompt: str, caracteres: list[str]) -> None:
    if caracteres:
        caracteres.pop()
        _redibujar_linea_texto(prompt, caracteres)


def leer_linea_teclado(
    mensaje: str,
    *,
    permitir_atras: bool = False,
    en_partida: bool = False,
    mayusculas: bool = False,
) -> str:
    """Linea de texto tecla a tecla; Esc = atras o pausa; Supr/Retroceso = borrar (Windows)."""
    from .navegacion import SalirPrograma, VolverAtras, _gestionar_pausa, menu_ayuda_dinamico

    establecer_contexto_entrada(
        ContextoEntrada(
            tipo="texto",
            defecto="confirmar",
            permitir_atras=permitir_atras,
            en_partida=en_partida,
        )
    )
    prompt = _formatear_prompt(mensaje)
    caracteres: list[str] = []

    def _mostrar_linea() -> None:
        print()
        print(prompt, end="", flush=True)
        if caracteres:
            print("".join(caracteres), end="", flush=True)

    _mostrar_linea()

    while True:
        try:
            ev = _leer_tecla_texto_windows()
        except EOFError:
            raise SalirPrograma() from None

        if ev.tipo == TipoTecla.LETRA and ev.valor == TECLA_AYUDA:
            menu_ayuda_dinamico(en_partida=en_partida)
            _mostrar_linea()
            continue
        if ev.tipo == TipoTecla.LETRA and ev.valor == TECLA_FEEDBACK:
            from .navegacion import feedback_rapido_disponible, invocar_feedback_rapido

            if feedback_rapido_disponible():
                invocar_feedback_rapido()
            _mostrar_linea()
            continue
        if ev.tipo in (TipoTecla.BORRAR, TipoTecla.SUPR):
            _borrar_caracter_en_linea(prompt, caracteres)
            continue
        if ev.tipo == TipoTecla.ESCAPE:
            if permitir_atras:
                print()
                raise VolverAtras() from None
            try:
                _gestionar_pausa(en_partida=en_partida)
            except SalirPrograma:
                raise
            _mostrar_linea()
            continue
        if ev.tipo == TipoTecla.ENTER:
            print()
            texto = "".join(caracteres).strip()
            return texto.upper() if mayusculas else texto
        if ev.tipo == TipoTecla.CARACTER:
            caracteres.append(ev.valor)
            print(ev.valor, end="", flush=True)
            continue


def _procesar_tecla(
    ev: _EventoTecla,
    *,
    en_pausa: bool,
    permitir_atras: bool,
    es_menu_principal: bool = False,
    en_partida: bool = False,
    menu_si_no: bool = False,
) -> _EventoTecla | None:
    from .navegacion import IrMenuPrincipal, SalirPrograma, VolverAtras

    if ev.tipo == TipoTecla.ESCAPE:
        _gestionar_tecla_escape(en_pausa=en_pausa)

    if ev.tipo == TipoTecla.SUPR:
        if en_pausa:
            return _EventoTecla(TipoTecla.ENTER)
        if en_partida:
            return None
        if es_menu_principal:
            raise SalirPrograma() from None
        if permitir_atras:
            raise VolverAtras()
        raise IrMenuPrincipal() from None

    if ev.tipo == TipoTecla.LETRA:
        if ev.valor == TECLA_FEEDBACK:
            return None
        if not en_partida and ev.valor in _LETRAS_RESPUESTA:
            return None
        if ev.valor in _LETRAS_SN and not menu_si_no:
            return None
        return ev

    if ev.tipo == TipoTecla.DIGITO and en_partida:
        return None

    if ev.tipo == TipoTecla.IGNORAR:
        return None
    if ev.tipo in (TipoTecla.ENTER, TipoTecla.DIGITO):
        return ev
    return None


def _inferir_tipo_entrada(
    *,
    en_pausa: bool,
    en_partida: bool,
    menu_si_no: bool,
    tipo_entrada: TipoEntrada | None,
) -> TipoEntrada:
    if tipo_entrada is not None:
        return tipo_entrada
    if en_pausa:
        return "pausa"
    if en_partida:
        return "pregunta"
    if menu_si_no:
        return "menu_si_no"
    return "menu_numerico"


def _registrar_contexto_entrada(
    *,
    tipo_entrada: TipoEntrada | None,
    defecto: int | str,
    permitir_atras: bool,
    en_partida: bool,
    en_pausa: bool,
    es_menu_principal: bool,
    menu_si_no: bool,
    num_opciones: int | None = None,
) -> None:
    establecer_contexto_entrada(
        ContextoEntrada(
            tipo=_inferir_tipo_entrada(
                en_pausa=en_pausa,
                en_partida=en_partida,
                menu_si_no=menu_si_no,
                tipo_entrada=tipo_entrada,
            ),
            defecto=defecto,
            permitir_atras=permitir_atras,
            es_menu_principal=es_menu_principal,
            en_partida=en_partida,
            en_pausa=en_pausa,
            num_opciones=num_opciones,
        )
    )


def esperar_tecla_menu(
    prompt: str,
    *,
    defecto: int | str = 1,
    permitir_atras: bool = False,
    en_partida: bool = False,
    en_pausa: bool = False,
    es_menu_principal: bool = False,
    menu_si_no: bool = False,
    tipo_entrada: TipoEntrada | None = None,
    num_opciones: int | None = None,
    validar: Callable[[_EventoTecla], bool] | None = None,
) -> _EventoTecla:
    """Bucle hasta tecla valida; las ignoradas refrescan pantalla sin mensajes."""
    from .navegacion import (
        SalirPrograma,
        _gestionar_pausa,
        feedback_rapido_disponible,
        invocar_feedback_rapido,
        menu_ayuda_dinamico,
        refrescar_pantalla_activa,
    )

    while True:
        _registrar_contexto_entrada(
            tipo_entrada=tipo_entrada,
            defecto=defecto,
            permitir_atras=permitir_atras,
            en_partida=en_partida,
            en_pausa=en_pausa,
            es_menu_principal=es_menu_principal,
            menu_si_no=menu_si_no,
            num_opciones=num_opciones,
        )
        _imprimir_linea_accion(prompt)
        try:
            ev = leer_tecla(en_pausa=en_pausa)
        except EOFError:
            raise SalirPrograma() from None
        if ev.tipo == TipoTecla.LETRA and ev.valor == TECLA_AYUDA:
            menu_ayuda_dinamico(en_partida=en_partida)
            refrescar_pantalla_activa()
            continue
        if (
            not en_pausa
            and ev.tipo == TipoTecla.LETRA
            and ev.valor == TECLA_FEEDBACK
            and feedback_rapido_disponible()
        ):
            invocar_feedback_rapido()
            continue
        try:
            res = _procesar_tecla(
                ev,
                en_pausa=en_pausa,
                permitir_atras=permitir_atras,
                es_menu_principal=es_menu_principal,
                en_partida=en_partida,
                menu_si_no=menu_si_no,
            )
        except AbrirPausa:
            _gestionar_pausa(en_partida=en_partida)
            if not en_partida:
                refrescar_pantalla_activa()
            continue
        if res is None or (validar is not None and not validar(res)):
            refrescar_pantalla_activa()
            continue
        print()
        return res


def elegir_indice_menu(
    num_opciones: int,
    *,
    defecto: int = 1,
    permitir_cero: bool = False,
    permitir_atras: bool = False,
    en_partida: bool = False,
    prompt: str = "Selecciona",
    en_pausa: bool = False,
    es_menu_principal: bool = False,
) -> int:
    """Devuelve indice 1-based (o 0 si permitir_cero)."""

    def _validar(ev: _EventoTecla) -> bool:
        if ev.tipo == TipoTecla.ENTER:
            return True
        if ev.tipo == TipoTecla.DIGITO:
            n = int(ev.valor)
            if permitir_cero and n == 0:
                return True
            return 1 <= n <= num_opciones
        return False

    ev = esperar_tecla_menu(
        prompt,
        defecto=defecto,
        permitir_atras=permitir_atras,
        en_partida=en_partida,
        en_pausa=en_pausa,
        es_menu_principal=es_menu_principal,
        num_opciones=num_opciones,
        validar=_validar,
    )
    if ev.tipo == TipoTecla.ENTER:
        return 0 if permitir_cero and defecto == 0 else defecto
    return int(ev.valor)


def elegir_letra_menu(
    validas: set[str],
    *,
    defecto: str,
    permitir_atras: bool = False,
    en_partida: bool = False,
    prompt: str = "Selecciona",
    es_menu_principal: bool = False,
) -> str:
    """Letras validas (A-D en pregunta; S/N solo en menus Si/No)."""
    menu_si_no = _es_menu_si_no(validas)
    validas_set = set(validas)

    def _validar(ev: _EventoTecla) -> bool:
        if ev.tipo == TipoTecla.ENTER:
            return True
        return ev.tipo == TipoTecla.LETRA and ev.valor in validas_set

    ev = esperar_tecla_menu(
        prompt,
        defecto=defecto,
        permitir_atras=permitir_atras,
        en_partida=en_partida,
        es_menu_principal=es_menu_principal,
        menu_si_no=menu_si_no,
        validar=_validar,
    )
    if ev.tipo == TipoTecla.ENTER:
        return defecto
    return ev.valor


def esperar_enter(
    mensaje: str = "Pulsa Enter para continuar",
    *,
    permitir_atras: bool = False,
) -> None:
    """Espera Enter (tecla a tecla), con indicador de foco."""

    def _validar(ev: _EventoTecla) -> bool:
        return ev.tipo == TipoTecla.ENTER

    esperar_tecla_menu(
        mensaje,
        defecto="Enter",
        permitir_atras=permitir_atras,
        tipo_entrada="enter_solo",
        validar=_validar,
    )


def esperar_enter_en_foco(
    *,
    mensaje: str = "Haz clic aquí y pulsa Enter para continuar",
    reimprimir: Callable[[], None] | None = None,
) -> None:
    """Tutorial: la linea >> es el unico punto de interaccion; solo Enter continua."""
    from .navegacion import SalirPrograma, _gestionar_pausa, limpiar_consola, menu_ayuda_dinamico

    while True:
        establecer_contexto_entrada(
            ContextoEntrada(tipo="tutorial", defecto="Enter")
        )
        if reimprimir:
            limpiar_consola()
            reimprimir()
        _imprimir_linea_accion(mensaje, con_dos_puntos=False)
        try:
            ev = leer_tecla()
        except EOFError:
            raise SalirPrograma() from None

        if ev.tipo == TipoTecla.LETRA and ev.valor == TECLA_AYUDA:
            menu_ayuda_dinamico(en_partida=False)
            continue
        if ev.tipo == TipoTecla.ESCAPE:
            try:
                _gestionar_pausa(en_partida=False)
            except SalirPrograma:
                raise
            continue
        if ev.tipo == TipoTecla.ENTER:
            print()
            return
        continue
