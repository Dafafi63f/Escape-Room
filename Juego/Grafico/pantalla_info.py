#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hub «Info del juego»: ranking, contacto visible y novedades."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pygame

from Comun.changelog_juego import cargar_changelog_juego_grafico
from Comun.contacto_creador import (
    canales_contacto_alternativo,
    nota_contacto_jugador,
    texto_bloque_contacto_alternativo,
)
from Grafico.pantallas import Pantalla
from Grafico.tema import (
    ALTO,
    ANCHO,
    COLOR_FONDO,
    COLOR_TEXTO_PANEL,
    COLOR_TITULO,
    MARGEN,
    Y_INICIO_TITULO,
    crear_fuentes,
)
from Grafico.texto import dibujar_texto_centro
from Grafico.textos_grafico import BTN_VOLVER, etiqueta, titulo_pantalla
from Grafico.ui import (
    Boton,
    capturar,
    dibujar_panel,
    dibujar_tooltips_botones,
    partir_texto,
    posicionar_pila_inferior,
    rect_boton_etiqueta,
    rects_botones_apilados,
)

_COLOR_TEXTO_INFO = (55, 65, 82)
_MARGEN_SCROLL = 14
_GAP_TRAS_SUBTITULO = 18
_PAD_CONTACTO = 14
_GAP_CONTACTO_BOTONES = 16


def _texto_contacto_hub() -> str:
    if canales_contacto_alternativo():
        return texto_bloque_contacto_alternativo()
    return (
        f"{nota_contacto_jugador()}\n\n"
        "No hay canales de contacto configurados en esta instalación."
    )


@dataclass(frozen=True)
class SeccionInfo:
    id: str
    titulo: str
    emoji: str
    tooltip: str


SECCIONES_INFO: tuple[SeccionInfo, ...] = (
    SeccionInfo(
        "ranking",
        "Ver ranking local",
        "🏆",
        "Tablas de resistencia infinita y reto del día.",
    ),
    SeccionInfo(
        "changelog_juego",
        "Novedades del juego",
        "🎮",
        "Cambios recientes en la interfaz gráfica.",
    ),
)


def _etiqueta_seccion(seccion: SeccionInfo) -> str:
    return f"{seccion.emoji} {seccion.titulo}"


class PantallaInfoTexto(Pantalla):
    """Texto informativo con desplazamiento vertical."""

    def __init__(
        self,
        titulo: str,
        contenido: str,
        volver_a: Callable[[], None],
    ) -> None:
        self.titulo = titulo
        self.contenido = contenido
        self.volver_a = volver_a
        self.fuentes = crear_fuentes()
        self.scroll = 0
        self._panel = pygame.Rect(MARGEN, Y_INICIO_TITULO + 36, ANCHO - 2 * MARGEN, ALTO - 168)
        self.boton_volver = Boton(
            etiqueta(*BTN_VOLVER),
            rect_boton_etiqueta(
                etiqueta(*BTN_VOLVER),
                self.fuentes["menu"],
                x_centro=ANCHO // 2,
                y=0,
                alto_min=48,
            ),
            self.volver_a,
        )
        posicionar_pila_inferior([self.boton_volver], x_centro=ANCHO // 2, gap=0, margen_inferior=24)
        self._lineas = self._construir_lineas()

    def _construir_lineas(self) -> list[str]:
        fuente = self.fuentes["pequena"]
        ancho = self._panel.width - 24
        lineas: list[str] = []
        for bloque in self.contenido.split("\n"):
            if not bloque.strip():
                lineas.append("")
                continue
            lineas.extend(partir_texto(fuente, bloque, ancho))
        return lineas

    def _max_scroll(self) -> int:
        fuente = self.fuentes["pequena"]
        alto_linea = fuente.get_linesize() + 4
        alto_total = len(self._lineas) * alto_linea + 16
        return max(0, alto_total - self._panel.height)

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self._max_scroll(), self.scroll - int(evento.y) * 24))
        elif evento.type == pygame.MOUSEMOTION:
            self.boton_volver.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            self.boton_volver.manejar_clic(evento.pos, evento.button)
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_texto_centro(
            superficie,
            titulo_pantalla(self.titulo),
            (ANCHO // 2, Y_INICIO_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        dibujar_panel(superficie, self._panel, color=(255, 255, 255))
        fuente = self.fuentes["pequena"]
        alto_linea = fuente.get_linesize() + 4
        y = self._panel.y + 12 - self.scroll
        for linea in self._lineas:
            if y + alto_linea >= self._panel.y and y <= self._panel.bottom:
                if linea:
                    txt = fuente.render(linea, True, _COLOR_TEXTO_INFO)
                    superficie.blit(txt, (self._panel.x + 12, y))
            y += alto_linea
            if y > self._panel.bottom + alto_linea:
                break
        if self._max_scroll() > 0:
            hint = fuente.render("Rueda del ratón para desplazarte", True, COLOR_TEXTO_PANEL)
            superficie.blit(
                hint,
                hint.get_rect(center=(ANCHO // 2, self._panel.bottom + 14)),
            )
        self.boton_volver.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], [self.boton_volver])


class PantallaInfoHub(Pantalla):
    """Menú unificado: ranking y changelog, con contacto visible en pantalla."""

    def titulo_pausa(self) -> str:
        return "Info del juego"

    def __init__(
        self,
        volver: Callable[[], None],
        *,
        navegar: Callable[[Pantalla], None],
        abrir_ranking: Callable[[Callable[[], None]], None],
    ) -> None:
        self.volver = volver
        self._navegar = navegar
        self._abrir_ranking = abrir_ranking
        self.fuentes = crear_fuentes()
        self._lineas_contacto = self._construir_lineas_contacto()
        self._construir_layout_contacto()
        self._crear_botones()

    def _construir_lineas_contacto(self) -> list[str]:
        fuente = self.fuentes["pequena"]
        ancho = ANCHO - 2 * MARGEN - 24
        lineas: list[str] = []
        for bloque in _texto_contacto_hub().split("\n"):
            if not bloque.strip():
                lineas.append("")
                continue
            lineas.extend(partir_texto(fuente, bloque, ancho))
        return lineas

    def _construir_layout_contacto(self) -> None:
        fuente = self.fuentes["pequena"]
        alto_linea = fuente.get_linesize() + 4
        alto_titulo = self.fuentes["menu"].get_height()
        alto_cuerpo = len(self._lineas_contacto) * alto_linea
        alto_panel = 10 + alto_titulo + 8 + alto_cuerpo + _PAD_CONTACTO
        y_panel = Y_INICIO_TITULO + 40 + _GAP_TRAS_SUBTITULO
        self._rect_contacto = pygame.Rect(
            MARGEN,
            y_panel,
            ANCHO - 2 * MARGEN,
            max(72, alto_panel),
        )
        self._y_botones_seccion = self._rect_contacto.bottom + _GAP_CONTACTO_BOTONES

    def _crear_botones(self) -> None:
        fuente = self.fuentes["menu"]
        etiquetas = [_etiqueta_seccion(s) for s in SECCIONES_INFO]
        rects = rects_botones_apilados(
            etiquetas,
            fuente,
            x_centro=ANCHO // 2,
            y0=self._y_botones_seccion,
            gap=12,
            ancho_min=460,
            alto_min=48,
        )
        self.botones_seccion: list[Boton] = []
        for seccion, rect in zip(SECCIONES_INFO, rects, strict=True):
            self.botones_seccion.append(
                Boton(
                    _etiqueta_seccion(seccion),
                    rect,
                    capturar(self._al_pulsar, seccion.id),
                    tooltip=seccion.tooltip,
                )
            )
        self.boton_volver = Boton(
            etiqueta(*BTN_VOLVER),
            rect_boton_etiqueta(
                etiqueta(*BTN_VOLVER),
                fuente,
                x_centro=ANCHO // 2,
                y=0,
                alto_min=48,
            ),
            self.volver,
        )
        posicionar_pila_inferior(
            [self.boton_volver],
            x_centro=ANCHO // 2,
            gap=0,
            margen_inferior=28,
        )

    def _volver_al_hub(self) -> None:
        self._navegar(self)

    def _al_pulsar(self, seccion_id: str) -> None:
        if seccion_id == "ranking":
            self._abrir_ranking(self._volver_al_hub)
            return
        if seccion_id == "changelog_juego":
            self._navegar(
                PantallaInfoTexto(
                    "Novedades del juego",
                    cargar_changelog_juego_grafico(),
                    self._volver_al_hub,
                ),
            )
            return

    def _botones_ui(self) -> list[Boton]:
        return [*self.botones_seccion, self.boton_volver]

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_texto_centro(
            superficie,
            titulo_pantalla("INFO DEL JUEGO"),
            (ANCHO // 2, Y_INICIO_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        subt = self.fuentes["menu"].render(
            "Ranking, contacto y novedades del juego.",
            True,
            COLOR_TEXTO_PANEL,
        )
        superficie.blit(subt, subt.get_rect(center=(ANCHO // 2, Y_INICIO_TITULO + 40)))
        self._dibujar_contacto(superficie)
        for boton in self.botones_seccion:
            boton.dibujar(superficie, self.fuentes["menu"])
        self.boton_volver.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], self._botones_ui())

    def _dibujar_contacto(self, superficie: pygame.Surface) -> None:
        dibujar_panel(superficie, self._rect_contacto, color=(255, 255, 255))
        tit = self.fuentes["menu"].render("Contacto del creador", True, _COLOR_TEXTO_INFO)
        superficie.blit(tit, (self._rect_contacto.x + _PAD_CONTACTO, self._rect_contacto.y + 10))
        fuente = self.fuentes["pequena"]
        alto_linea = fuente.get_linesize() + 4
        y = self._rect_contacto.y + 10 + tit.get_height() + 8
        for linea in self._lineas_contacto:
            if linea:
                txt = fuente.render(linea, True, _COLOR_TEXTO_INFO)
                superficie.blit(txt, (self._rect_contacto.x + _PAD_CONTACTO, y))
            y += alto_linea
            if y > self._rect_contacto.bottom - 8:
                break
