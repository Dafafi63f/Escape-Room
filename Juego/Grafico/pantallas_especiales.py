#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pantallas pygame de modos especiales (menú por botones, sin carrusel)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.config_historia import ConfigPresetHistoria
from Comun.presets_historia import PresetHistoria
from Comun.preferencias_grafico import nombre_jugador_grafico
from Comun.reto_dia_resistencia import ID_PRESET_RETO_DIA, etiqueta_fecha_reto_dia
from Comun.textos_ui import EmojiPar, _p
from Grafico.modo_historia import (
    cargar_catalogo_especiales,
    construir_navegacion_fin_partida_historia,
    iniciar_pantalla_partida_historia,
)
from Grafico.pantallas import MenuPrincipal, Pantalla
from Grafico.textos_grafico import (
    BTN_VOLVER_MENU,
    con_emoji,
    etiqueta,
    etiqueta_campo,
    subtitulo,
    titulo_pantalla,
)
from Grafico.tema import (
    ALTO,
    ANCHO,
    COLOR_AVISO,
    COLOR_FONDO,
    COLOR_TEXTO,
    COLOR_TITULO,
    MARGEN,
    Y_INICIO_TITULO,
    crear_fuentes,
)
from Grafico.texto import dibujar_texto_centro
from Grafico.ui import (
    Boton,
    dibujar_tooltips_botones,
    posicionar_pila_inferior,
    rect_boton_etiqueta,
    rects_botones_apilados,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

Y_TITULO = Y_INICIO_TITULO
Y_SUBTITULO = Y_TITULO + 32
Y_MODOS_LBL = Y_SUBTITULO + 36
Y_BOTONES_MODOS = Y_MODOS_LBL + 32
MARGEN_INF = 22

_EMOJI_INFINITA = _p("♾️")
_EMOJI_RETO_DIA = _p("🔥")
_EMOJI_ESPECIAL_DEFECTO = _p("⚡")

_EMOJI_POR_PRESET: dict[str, EmojiPar] = {
    "ranking_resistencia": _EMOJI_INFINITA,
    ID_PRESET_RETO_DIA: _EMOJI_RETO_DIA,
}


class ConfigModosEspeciales(Pantalla):
    """Lista de modos especiales (un botón por preset)."""

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.mensaje = ""
        self.presets = cargar_catalogo_especiales()

        fuente_menu = self.fuentes["menu"]
        etiquetas_modos = [preparar_etiqueta_modo(p) for p in self.presets]
        rects_modos = rects_botones_apilados(
            etiquetas_modos,
            fuente_menu,
            x_centro=ANCHO // 2,
            y0=Y_BOTONES_MODOS,
            gap=12,
            ancho_min=460,
            alto_min=52,
            margen_inferior=MARGEN_INF + 72,
        )
        self.botones_modo: list[Boton] = []
        for preset, rect, etiq in zip(self.presets, rects_modos, etiquetas_modos, strict=True):
            self.botones_modo.append(
                Boton(
                    etiq,
                    rect,
                    lambda pid=preset.id: self._iniciar_modo(pid),
                    tooltip=recortar_tooltip(preset.descripcion),
                )
            )

        etiq_volver = etiqueta(*BTN_VOLVER_MENU)
        self.boton_volver = Boton(
            etiq_volver,
            rect_boton_etiqueta(
                etiq_volver,
                fuente_menu,
                x_centro=ANCHO // 2,
                y=0,
                ancho_min=420,
                alto_min=44,
            ),
            lambda: self.ir_a(MenuPrincipal(datos, ir_a, salir_app)),
        )
        posicionar_pila_inferior(
            [self.boton_volver],
            x_centro=ANCHO // 2,
            gap=14,
            margen_inferior=MARGEN_INF,
        )

    def _pantalla_actual(self) -> ConfigModosEspeciales:
        return ConfigModosEspeciales(self.datos, self.ir_a, self.salir_app)

    def _preset_por_id(self, preset_id: str) -> PresetHistoria:
        for preset in self.presets:
            if preset.id == preset_id:
                return preset
        raise KeyError(preset_id)

    def _iniciar_modo(self, preset_id: str) -> None:
        preset = self._preset_por_id(preset_id)
        nombre = nombre_jugador_grafico()
        config = ConfigPresetHistoria()
        self.mensaje = ""

        def _pantalla_configuracion():
            return ConfigModosEspeciales(self.datos, self.ir_a, self.salir_app)

        navegacion = construir_navegacion_fin_partida_historia(
            self.datos,
            preset,
            config,
            nombre,
            self.ir_a,
            self.salir_app,
            _pantalla_configuracion,
        )
        try:
            pantalla = iniciar_pantalla_partida_historia(
                self.datos,
                preset,
                config,
                nombre,
                self.ir_a,
                self.salir_app,
                navegacion_fin=navegacion,
            )
        except ValueError as e:
            self.mensaje = str(e)
            return
        self.ir_a(pantalla)

    def _botones_ui(self) -> list[Boton]:
        return [*self.botones_modo, self.boton_volver]

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
            titulo_pantalla("MODOS ESPECIALES"),
            (ANCHO // 2, Y_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        dibujar_texto_centro(
            superficie,
            subtitulo(
                "Resistencia infinita y reto del día (más modos en el futuro)",
                "⚡",
            ),
            (ANCHO // 2, Y_SUBTITULO),
            self.fuentes["pequena"].get_height(),
            COLOR_TEXTO,
        )

        modos_lbl = self.fuentes["menu"].render(
            etiqueta_campo("modo_especial", "Elige un modo:"), True, COLOR_TEXTO
        )
        superficie.blit(modos_lbl, modos_lbl.get_rect(midtop=(ANCHO // 2, Y_MODOS_LBL)))

        for boton in self.botones_modo:
            boton.dibujar(superficie, self.fuentes["menu"])

        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(
                aviso,
                aviso.get_rect(center=(ANCHO // 2, self.boton_volver.rect.y - 28)),
            )

        self.boton_volver.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(
            superficie,
            self.fuentes["pequena"],
            self._botones_ui(),
        )

    def titulo_pausa(self) -> str:
        return "Modos especiales"


def preparar_etiqueta_modo(preset: PresetHistoria) -> str:
    from Grafico.texto import preparar_texto_ui

    emoji = _EMOJI_POR_PRESET.get(preset.id, _EMOJI_ESPECIAL_DEFECTO)
    if preset.id == ID_PRESET_RETO_DIA:
        texto = f"Reto del día — {etiqueta_fecha_reto_dia()}"
    else:
        texto = preset.nombre
    return preparar_texto_ui(con_emoji(texto, emoji, posicion="inicio"))


def recortar_tooltip(descripcion: str, max_len: int = 120) -> str:
    texto = descripcion.strip()
    if len(texto) <= max_len:
        return texto
    return texto[: max_len - 1].rstrip() + "…"
