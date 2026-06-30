#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Línea de estado de partida con iconos (texto/emoji; UI gráfica)."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from Comun.motor_nucleo import EstadoPartida
from Comun.reglas import SistemaPuntuacion

__all__ = [
    "EMOJI_TIEMPO_PREG",
    "EMOJI_TIEMPO_TOTAL",
    "EMOJI_ID_PREGUNTA",
    "EMOJI_ID_PREGUNTA_RESISTENCIA",
    "EMOJI_PROGRESO_EXAMEN",
    "EMOJI_PROGRESO_PREGUNTA_ESCAPE",
    "EMOJI_SALA_ESCAPE",
    "SegmentoEstado",
    "ascii_icono_segmento",
    "stdout_soporta_emoji",
    "emoji_candidatos_segmento",
    "formatear_linea_estado",
    "segmentos_linea_estado",
    "texto_progreso_examen_cerrado",
]

_SEPARADOR_TEXTO = "  "

# Iconos de la barra: tiempo activo de partida vs temporizador por pregunta.
EMOJI_TIEMPO_TOTAL = "⏰"
EMOJI_TIEMPO_PREG = "⏱️"
EMOJI_ID_PREGUNTA = "❓"
EMOJI_ID_PREGUNTA_RESISTENCIA = EMOJI_ID_PREGUNTA
EMOJI_PROGRESO_EXAMEN = "📝"
EMOJI_PROGRESO_PREGUNTA_ESCAPE = EMOJI_PROGRESO_EXAMEN
EMOJI_SALA_ESCAPE = "🗺️"
_ASCII_TIEMPO_TOTAL = "T·"
_ASCII_TIEMPO_PREG = "P·"

_EMOJI_ALTERNATIVOS: dict[str, tuple[str, ...]] = {
    "progreso": ("❓", "📝", "📋"),
    "pregunta_puerta": ("📝", "📋"),
    "jefe_resistencia": ("👑", "♔"),
    "sala_escape": ("🗺️", "🏠", "📍"),
    "racha": ("🔥", "💥"),
    "vidas": ("❤️", "❤", "🧡"),
    "tiempo_total": ("⏰", "⏳", "⌚", "🕐", "🕑"),
    "tiempo_preg": ("⏱️", "⏱", "⏳", "⌛", "⏰"),
    "desafio_bloque": ("⏲️", "⏰", "⏳"),
    "puntos": ("⭐", "★", "🌟"),
    "nota": ("📊", "📈"),
    "aciertos": ("✅", "✔️"),
}

_ASCII_POR_ID: dict[str, str] = {
    "progreso": "?",
    "pregunta_puerta": "?",
    "sala_escape": "S·",
    "racha": "R·",
    "vidas": "+",
    "tiempo_total": _ASCII_TIEMPO_TOTAL,
    "tiempo_preg": _ASCII_TIEMPO_PREG,
    "desafio_bloque": "B·",
    "puntos": "*",
    "nota": "%",
    "aciertos": "OK",
}


@dataclass(frozen=True)
class SegmentoEstado:
    """Un bloque de la barra de estado (icono + texto)."""

    id: str
    emoji: str
    texto: str


def stdout_soporta_emoji() -> bool:
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    return enc in {"utf-8", "utf8", "cp65001", "cp_utf8"}


def texto_progreso_examen_cerrado(indice_actual: int, total: int) -> str:
    """Progreso x/y para exámenes cerrados o partidas con tope fijo (icono 📝 en barra)."""
    return f"{indice_actual}/{total}"


def _progreso_visible(progreso: str) -> str:
    return progreso.replace("/inf", "/∞").replace(" inf", " ∞")


def _es_total_infinito(total_txt: str) -> bool:
    return total_txt.strip().lower().replace("∞", "inf") in {"inf", "infinity"}


def _normalizar_entrada_progreso(
    progreso: str,
    numero_pregunta: int | None,
) -> tuple[str, int | None]:
    """Convierte textos legacy («Pregunta N/inf») al formato de barra unificado."""
    if numero_pregunta is not None:
        return progreso, numero_pregunta
    prog = progreso.strip()
    if not prog:
        return progreso, None
    if prog.lower().startswith("pregunta "):
        rest = prog[len("Pregunta ") :].strip()
        if "/" in rest:
            actual_txt, total_txt = (p.strip() for p in rest.split("/", 1))
            try:
                actual = int(actual_txt)
            except ValueError:
                return progreso, None
            if _es_total_infinito(total_txt):
                return "", actual
            try:
                total = int(total_txt)
            except ValueError:
                return progreso, None
            return texto_progreso_examen_cerrado(actual, total), None
    if "/" in prog:
        _actual_txt, total_txt = (p.strip() for p in prog.split("/", 1))
        if _es_total_infinito(total_txt):
            try:
                return "", int(_actual_txt)
            except ValueError:
                return progreso, None
    return progreso, None


def _segmento_tiempo_activo(estado: EstadoPartida) -> SegmentoEstado | None:
    """Cuenta atrás global solo si hay límite; el transcurrido no se muestra en partida."""
    rest = estado.tiempo_total_restante()
    if rest is None:
        return None
    return SegmentoEstado("tiempo_total", EMOJI_TIEMPO_TOTAL, f"{rest}s")


def _segmento_temporizador_pregunta(segundos_restantes: int) -> SegmentoEstado:
    return SegmentoEstado(
        "tiempo_preg",
        EMOJI_TIEMPO_PREG,
        f"{segundos_restantes}s",
    )


def _segmento_id_pregunta(numero_pregunta: int) -> SegmentoEstado:
    return SegmentoEstado("progreso", EMOJI_ID_PREGUNTA, str(numero_pregunta))


def _segmento_progreso_examen(texto: str) -> SegmentoEstado:
    return SegmentoEstado(
        "progreso",
        EMOJI_PROGRESO_EXAMEN,
        _progreso_visible(texto),
    )


def _segmentos_id_pregunta(
    numero_pregunta: int,
    *,
    racha: int | None = None,
    bloque_filtro_texto: str | None = None,
) -> list[SegmentoEstado]:
    """ID de pregunta (❓) en modos sin tope: resistencia, libre infinito, etc."""
    segmentos = [_segmento_id_pregunta(numero_pregunta)]
    if racha is not None:
        segmentos.append(SegmentoEstado("racha", "🔥", str(racha)))
    if bloque_filtro_texto:
        from Comun.emojis_escape import EMOJI_JEFE

        es_jefe = bloque_filtro_texto.startswith("Jefe ")
        emoji_progreso = EMOJI_JEFE if es_jefe else EMOJI_PROGRESO_PREGUNTA_ESCAPE
        segmentos.append(
            SegmentoEstado(
                "pregunta_puerta",
                emoji_progreso,
                bloque_filtro_texto,
            )
        )
    return segmentos


def segmentos_linea_estado(
    estado: EstadoPartida,
    progreso: str,
    *,
    segundos_pregunta_restantes: int | None = None,
    vidas_max: int | None = None,
    numero_pregunta: int | None = None,
    racha: int | None = None,
    progreso_puerta: str | None = None,
    progreso_sala: str | None = None,
    mostrar_tiempo_activo: bool = True,
    desafio_bloque_texto: str | None = None,
    bloque_filtro_texto: str | None = None,
    efectos_puerta: tuple[str, ...] = (),
) -> list[SegmentoEstado]:
    """Construye los chips de la barra; cada bloque depende solo de sus reglas.

    Orden fijo: sala (escape) → pregunta en puerta → progreso → racha → vidas → tiempo → puntuación.
    Sin tope (resistencia, libre infinito): ❓ + id. Examen cerrado / finito: 📝 + x/y.
    """
    progreso, numero_pregunta = _normalizar_entrada_progreso(progreso, numero_pregunta)
    if numero_pregunta is not None:
        segmentos = _segmentos_id_pregunta(
            numero_pregunta,
            racha=racha,
            bloque_filtro_texto=bloque_filtro_texto,
        )
    else:
        segmentos: list[SegmentoEstado] = []
        if progreso_sala:
            segmentos.append(
                SegmentoEstado("sala_escape", EMOJI_SALA_ESCAPE, progreso_sala)
            )
        if progreso_puerta:
            segmentos.append(
                SegmentoEstado(
                    "pregunta_puerta",
                    EMOJI_PROGRESO_PREGUNTA_ESCAPE,
                    progreso_puerta,
                )
            )
        if progreso:
            segmentos.append(_segmento_progreso_examen(progreso))

    for etiqueta in efectos_puerta:
        segmentos.append(SegmentoEstado("efecto_puerta", "", etiqueta))

    if estado.reglas.tiene_vidas():
        n = estado.vidas_restantes or 0
        tope = vidas_max if vidas_max is not None else estado.reglas.vidas
        texto_vidas = f"{n}/{tope}" if tope else str(n)
        segmentos.append(SegmentoEstado("vidas", "❤️", texto_vidas))

    if mostrar_tiempo_activo:
        seg_tiempo = _segmento_tiempo_activo(estado)
        if seg_tiempo is not None:
            segmentos.append(seg_tiempo)

    if segundos_pregunta_restantes is not None:
        segmentos.append(_segmento_temporizador_pregunta(segundos_pregunta_restantes))

    if desafio_bloque_texto:
        segmentos.append(
            SegmentoEstado("desafio_bloque", "⏲️", desafio_bloque_texto)
        )

    sis = estado.reglas.sistema_puntuacion
    if sis == SistemaPuntuacion.ARCADE:
        segmentos.append(SegmentoEstado("puntos", "⭐", f"{estado.puntos_arcade}"))
    return segmentos


def ascii_icono_segmento(seg_id: str) -> str:
    """Sustituto textual del icono (emojis desactivados o terminal sin Unicode)."""
    return _ASCII_POR_ID.get(seg_id, "·")


def emoji_candidatos_segmento(seg: SegmentoEstado) -> tuple[str, ...]:
    """Glifos a probar en orden (el preferido del segmento primero)."""
    alternativas = _EMOJI_ALTERNATIVOS.get(seg.id, ())
    vistos: list[str] = []
    for glyph in (seg.emoji, *alternativas):
        if glyph and glyph not in vistos:
            vistos.append(glyph)
    return tuple(vistos)


def _icono_segmento(seg: SegmentoEstado, *, usar_emojis: bool) -> str:
    if usar_emojis:
        return seg.emoji
    return ascii_icono_segmento(seg.id)


def formatear_linea_estado(
    segmentos: list[SegmentoEstado],
    *,
    usar_emojis: bool = True,
) -> str:
    """Texto de la barra: ``❓ 12  🔥 4  ❤️ 3/3`` o ``📝 3/10  ❤️ 3/3``."""
    if not segmentos:
        return ""
    partes = [
        f"{_icono_segmento(s, usar_emojis=usar_emojis)} {s.texto}" for s in segmentos
    ]
    return _SEPARADOR_TEXTO.join(partes)


def linea_estado_con_iconos(
    estado: EstadoPartida,
    progreso: str,
    *,
    segundos_pregunta_restantes: int | None = None,
    usar_emojis: bool = True,
    vidas_max: int | None = None,
    numero_pregunta: int | None = None,
    racha: int | None = None,
    progreso_puerta: str | None = None,
    progreso_sala: str | None = None,
    mostrar_tiempo_activo: bool = True,
    desafio_bloque_texto: str | None = None,
    bloque_filtro_texto: str | None = None,
    efectos_puerta: tuple[str, ...] = (),
) -> str:
    """Atajo: segmentos + formato textual."""
    return formatear_linea_estado(
        segmentos_linea_estado(
            estado,
            progreso,
            segundos_pregunta_restantes=segundos_pregunta_restantes,
            vidas_max=vidas_max,
            numero_pregunta=numero_pregunta,
            racha=racha,
            progreso_puerta=progreso_puerta,
            progreso_sala=progreso_sala,
            mostrar_tiempo_activo=mostrar_tiempo_activo,
            desafio_bloque_texto=desafio_bloque_texto,
            bloque_filtro_texto=bloque_filtro_texto,
            efectos_puerta=efectos_puerta,
        ),
        usar_emojis=usar_emojis,
    )
