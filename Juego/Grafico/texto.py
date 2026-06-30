#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalización y renderizado de texto mixto (texto + matemáticas + símbolos + emojis)."""

from __future__ import annotations

import pygame

from Grafico.fuentes import FamiliaFuente, crear_fuente, fuente_matematica_disponible

# Sustituciones solo si no hay fuente con glifos matemáticos (p. ej. CI sin Cambria).
_SUSTITUCIONES_ASCII: tuple[tuple[str, str], ...] = (
    ("ℝ", "R"),
    ("ℕ", "N"),
    ("ℤ", "Z"),
    ("ℚ", "Q"),
    ("ℂ", "C"),
    ("∫", "integral "),
    ("∑", "suma "),
    ("∂", "d"),
    ("∇", "grad "),
    ("∞", "inf"),
    ("≤", "<="),
    ("≥", ">="),
    ("≠", "!="),
    ("∈", "en"),
    ("·", "*"),
    ("×", "x"),
    ("²", "^2"),
    ("³", "^3"),
    ("⁴", "^4"),
    ("₀", "_0"),
    ("₁", "_1"),
    ("₂", "_2"),
    ("₃", "_3"),
    ("ᵇ", "^b"),
    ("ₐ", "_a"),
)

_CARACTERES_MATEMATICOS = frozenset(c for c, _ in _SUSTITUCIONES_ASCII)


def _es_emoji(cp: int) -> bool:
    return (
        0x1F000 <= cp <= 0x1F0FF
        or 0x1F300 <= cp <= 0x1FAFF
        or 0x1F600 <= cp <= 0x1F64F
        or 0x2600 <= cp <= 0x26FF
        or 0x2700 <= cp <= 0x27BF
        or 0xFE00 <= cp <= 0xFE0F
        # Controles multimedia (⏭️, ⏩, ⏸️…): emoji a color, no Segoe UI Symbol.
        or 0x23E9 <= cp <= 0x23FA
    )


def _es_matematica(cp: int, c: str) -> bool:
    if c in _CARACTERES_MATEMATICOS:
        return True
    return (
        0x0370 <= cp <= 0x03FF
        or 0x2100 <= cp <= 0x214F
        or 0x2200 <= cp <= 0x22FF
        or 0x2190 <= cp <= 0x21FF
    )


def _es_simbolo(cp: int) -> bool:
    return (
        0x2300 <= cp <= 0x23FF
        or 0x2500 <= cp <= 0x25FF
        or 0x2B00 <= cp <= 0x2BFF
    )


def familia_caracter(c: str) -> FamiliaFuente:
    if not c or c.isspace():
        return "texto"
    cp = ord(c)
    if _es_emoji(cp):
        return "emoji"
    if _es_matematica(cp, c):
        return "matematicas"
    if _es_simbolo(cp):
        return "simbolos"
    return "texto"


def _es_selector_variacion(c: str) -> bool:
    return 0xFE00 <= ord(c) <= 0xFE0F


def segmentar_por_familia(texto: str) -> list[tuple[str, FamiliaFuente]]:
    if not texto:
        return []
    segmentos: list[tuple[str, FamiliaFuente]] = []
    actual = texto[0]
    familia_actual = familia_caracter(actual)
    for c in texto[1:]:
        if _es_selector_variacion(c):
            actual += c
            continue
        fam = familia_caracter(c)
        if fam == familia_actual:
            actual += c
        else:
            segmentos.append((actual, familia_actual))
            actual = c
            familia_actual = fam
    segmentos.append((actual, familia_actual))
    return segmentos


def texto_requiere_fuentes_mixtas(texto: str) -> bool:
    return any(familia_caracter(c) != "texto" for c in texto)


def preparar_texto_ui(texto: str) -> str:
    """Devuelve texto listo para renderizar en pantalla."""
    if fuente_matematica_disponible():
        return texto
    resultado = texto
    for origen, destino in _SUSTITUCIONES_ASCII:
        resultado = resultado.replace(origen, destino)
    return resultado


def _fuente_segmento(
    familia: FamiliaFuente,
    tamano: int,
    *,
    bold: bool = False,
) -> pygame.font.Font:
    return crear_fuente(tamano, familia=familia, bold=bold and familia == "texto")


def medir_texto_mixto(
    texto: str,
    tamano: int,
    *,
    bold: bool = False,
) -> tuple[int, int]:
    texto = preparar_texto_ui(texto)
    ancho = 0
    alto = 0
    for fragmento, familia in segmentar_por_familia(texto):
        fuente = _fuente_segmento(familia, tamano, bold=bold)
        w, h = fuente.size(fragmento)
        ancho += w
        alto = max(alto, h)
    if alto == 0:
        fuente = _fuente_segmento("texto", tamano, bold=bold)
        return fuente.size(texto or " ")
    return ancho, alto


def renderizar_texto_mixto(
    pantalla: pygame.Surface,
    texto: str,
    pos: tuple[int, int],
    color: tuple[int, int, int],
    tamano: int,
    *,
    bold: bool = False,
) -> pygame.Rect:
    texto = preparar_texto_ui(texto)
    x, y = pos
    fragmentos: list[tuple[str, FamiliaFuente, int, int]] = []
    alto_linea = 0
    for fragmento, familia in segmentar_por_familia(texto):
        fuente = _fuente_segmento(familia, tamano, bold=bold)
        w, h = fuente.size(fragmento)
        if w == 0:
            continue
        fragmentos.append((fragmento, familia, w, h))
        alto_linea = max(alto_linea, h)
    if alto_linea == 0:
        return pygame.Rect(pos[0], pos[1], 0, 0)
    x_cursor = x
    for fragmento, familia, _w, h in fragmentos:
        fuente = _fuente_segmento(familia, tamano, bold=bold)
        superficie = fuente.render(fragmento, True, color)
        sw, sh = superficie.get_size()
        dy = (alto_linea - sh) // 2
        pantalla.blit(superficie, (x_cursor, y + dy))
        x_cursor += sw
    return pygame.Rect(pos[0], pos[1], x_cursor - pos[0], alto_linea)


def _partir_lineas_centro(
    texto: str,
    tamano: int,
    ancho_max: int,
    *,
    bold: bool = False,
) -> list[str]:
    palabras = texto.split()
    if not palabras:
        return [""]
    fuente = _fuente_segmento("texto", tamano, bold=bold)
    lineas: list[str] = []
    actual = palabras[0]
    for palabra in palabras[1:]:
        prueba = f"{actual} {palabra}"
        ancho = (
            medir_texto_mixto(prueba, tamano, bold=bold)[0]
            if texto_requiere_fuentes_mixtas(prueba)
            else fuente.size(prueba)[0]
        )
        if ancho <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    lineas.append(actual)
    return lineas


def dibujar_texto_centro(
    pantalla: pygame.Surface,
    texto: str,
    centro: tuple[int, int],
    tamano: int,
    color: tuple[int, int, int],
    *,
    bold: bool = False,
    ancho_max: int | None = None,
) -> pygame.Rect:
    """Texto centrado; usa fuente emoji/símbolos cuando hace falta."""
    texto = preparar_texto_ui(texto)
    if ancho_max is not None:
        lineas = _partir_lineas_centro(texto, tamano, ancho_max, bold=bold)
        if len(lineas) > 1:
            fuente = _fuente_segmento("texto", tamano, bold=bold)
            line_height = fuente.get_linesize()
            total_alto = len(lineas) * line_height
            y = centro[1] - total_alto // 2
            union = pygame.Rect(centro[0], y, 0, total_alto)
            for linea in lineas:
                if texto_requiere_fuentes_mixtas(linea):
                    ancho_linea, alto_linea = medir_texto_mixto(
                        linea, tamano, bold=bold
                    )
                    x = centro[0] - ancho_linea // 2
                    rect = renderizar_texto_mixto(
                        pantalla, linea, (x, y), color, tamano, bold=bold
                    )
                    y += max(line_height, alto_linea)
                else:
                    superficie = fuente.render(linea, True, color)
                    rect = superficie.get_rect(centerx=centro[0], top=y)
                    pantalla.blit(superficie, rect)
                    y += line_height
                union = union.union(rect)
            union.centerx = centro[0]
            return union
    if texto_requiere_fuentes_mixtas(texto):
        ancho, alto = medir_texto_mixto(texto, tamano, bold=bold)
        x = centro[0] - ancho // 2
        y = centro[1] - alto // 2
        rect = renderizar_texto_mixto(pantalla, texto, (x, y), color, tamano, bold=bold)
        rect.center = centro
        return rect
    fuente = _fuente_segmento("texto", tamano, bold=bold)
    superficie = fuente.render(texto, True, color)
    rect = superficie.get_rect(center=centro)
    pantalla.blit(superficie, rect)
    return rect
